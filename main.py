import os
import sys
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

from src.fetchers import RunHealth, fetch_linkedin_jobs
from src.evaluators import evaluate_and_enrich_job_with_gemini
from src.publishers import build_unified_html_email, send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")

def main():
    health = RunHealth()
    print("[INIT] Starting Morning Job Search Automation (Modular Architecture)")

    # 1. Load state
    # We expect jobs_state.json to be a list of handled job links/IDs
    state = load_state(STATE_FILE, default=[])
    handled_links = set(state)

    # 2. Fetch Jobs
    energy_keywords = ["SCADA operator", "Power plant technician", "Natural gas operator", "Mechanical technician energy", "מפעיל חדר בקרה"]
    drone_keywords = ["Drone operator", "UAV technician", "System integration drone", "מטיס פנים", "כטב\"ם אינטגרציה"]

    print("[FETCH] Scraping LinkedIn (Energy)...")
    linkedin_energy = fetch_linkedin_jobs(energy_keywords, health, max_pages=1)
    print("[FETCH] Scraping LinkedIn (Drones)...")
    linkedin_drones = fetch_linkedin_jobs(drone_keywords, health, max_pages=1)
    
    all_raw_jobs = linkedin_energy + linkedin_drones
    
    # 3. Filter New Jobs
    new_jobs = []
    for j in all_raw_jobs:
        if j["link"] not in handled_links:
            new_jobs.append(j)
            handled_links.add(j["link"]) # mark as seen to avoid duplicates in the same run
            
    health.candidates_found = len(new_jobs)
    print(f"[FILTER] Found {len(new_jobs)} new jobs out of {len(all_raw_jobs)} total fetched.")

    # 4. Evaluate with AI
    client = None
    if os.getenv("GEMINI_API_KEY"):
        client = genai.Client()
    else:
        print("[WARNING] GEMINI_API_KEY missing. Cannot evaluate jobs.")

    processed_jobs = []
    if client:
        for job in new_jobs:
            is_drone = "drone" in job.get("query", "").lower() or job.get("sector") in ["רחפנים אוטונומיים וביטחון", "רחפנים אוטונומיים"]
            try:
                result = evaluate_and_enrich_job_with_gemini(
                    client, 
                    job["title"], 
                    job["company"], 
                    job["snippet"], 
                    is_drone, 
                    health
                )
                time.sleep(4)
            except Exception as e:
                # Catch 429 specifically from google.genai or trigger fallback
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"[API ERROR] Rate limit reached. Using keyword fallback for: {job.get('title')}")
                else:
                    print(f"[API ERROR] Failure, using keyword fallback for: {job.get('title')}. Error: {e}")
                
                # Fallback logic
                keywords = ["gas", "energy", "mechanical", "control", "infrastructure", "cleantech", "drone", "uav", "scada"]
                text = f"{job.get('title', '')} {job.get('snippet', '')}".lower()
                match_count = sum(1 for word in keywords if word in text)
                score = match_count * 15
                
                result = {
                    "match_score": score,
                    "concrete_matches_count": match_count,
                    "reasoning": "הערכה באמצעות מילות מפתח עקב חסימת Rate Limit מה-API של גוגל.",
                    "sector_key": "other",
                    "sector": "כללי - Fallback",
                    "location": "לא צוין",
                    "company_domain_product": "מבוסס מילות מפתח (ללא AI)",
                    "job_summary": "משרה מבוססת גיבוי עקב חסימה זמנית ב-API.",
                    "experience_strengths": "נמצאו התאמות מילות מפתח.",
                    "key_highlights": "הערכה חלופית אוטומטית.",
                    "company_size": "N/A",
                    "junior_openness": "N/A",
                    "work_model": "N/A"
                }
                time.sleep(4)
                
            # Actually, evaluate_and_enrich_job_with_gemini catches exceptions internally and returns None!
            # So if it returned None because all models failed with 429, we should apply fallback:
            if result is None:
                print(f"[API ERROR] Rate limit or failure for {job.get('title')}. Applying keyword fallback.")
                keywords = ["gas", "energy", "mechanical", "control", "infrastructure", "cleantech", "drone", "uav", "scada"]
                text = f"{job.get('title', '')} {job.get('snippet', '')}".lower()
                match_count = sum(1 for word in keywords if word in text)
                score = match_count * 15
                
                result = {
                    "match_score": score,
                    "concrete_matches_count": match_count,
                    "reasoning": "הערכה באמצעות מילות מפתח עקב חסימת תור מה-API של גוגל.",
                    "sector_key": "other",
                    "sector": "כללי - Fallback",
                    "location": "לא צוין",
                    "company_domain_product": "מבוסס מילות מפתח (ללא AI)",
                    "job_summary": "משרה מבוססת גיבוי עקב חסימה זמנית ב-API.",
                    "experience_strengths": "נמצאו התאמות מילות מפתח.",
                    "key_highlights": "הערכה חלופית אוטומטית.",
                    "company_size": "N/A",
                    "junior_openness": "N/A",
                    "work_model": "N/A"
                }
                
            if result:
                job.update(result)
                if (is_drone and job["match_score"] >= 70) or (not is_drone and job["match_score"] >= 60):
                    processed_jobs.append(job)

    health.jobs_passed = len(processed_jobs)
    print(f"[EVALUATE] {len(processed_jobs)} jobs passed the score threshold.")

    # 5. Curate Top 5
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_5_jobs = processed_jobs[:5]
    top_3 = top_5_jobs[:3]

    # 6. Update Dashboard
    print("[UI] Updating Weekly Archive and Dashboard...")
    archive_file_path = os.path.join(os.path.dirname(__file__), "data", "weekly_archive.json")
    rejected_set = set()
    temp_archive = update_weekly_archive(top_5_jobs, archive_file_path, rejected_set)
    active_dashboard_jobs = temp_archive if temp_archive else top_5_jobs
    
    project_root = os.path.dirname(__file__)
    build_and_save_docs_app(active_dashboard_jobs, list(rejected_set), project_root, is_weekly=False)
    
    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    # 7. Dispatch Email
    print("[EMAIL] Building and dispatching email...")
    email_html = build_unified_html_email(top_5_jobs, top_3, dashboard_url)
    
    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_PASSWORD")
    
    if sender_email and sender_pwd:
        send_email_report(sender_email, sender_pwd, top_5_jobs, email_html, health)
    else:
        print("[WARNING] Missing email credentials.")
        
    # 8. Save State Atomically
    if health.email_success or not sender_email:
        save_state_atomic(STATE_FILE, list(handled_links))
        print("[STATE] State saved securely.")

    if health.gemini_failures > 0 and health.gemini_successes == 0 and health.jobs_evaluated > 0:
        health.final_status = "FAILED_AI"
        sys.exit(1)
        
    if health.linkedin_failures > 0:
        health.final_status = "DEGRADED"
    else:
        health.final_status = "SUCCESS"

    print(f"[DONE] Final Status: {health.final_status}")

if __name__ == "__main__":
    main()
