import os
import sys
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

from src.fetchers import RunHealth, fetch_linkedin_jobs, scrape_comeet_companies
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
    
    print("[FETCH] Scraping Comeet (ATS)...")
    comeet_res = scrape_comeet_companies()
    health.comeet_companies_attempted = comeet_res.get("attempted", 0)
    health.comeet_companies_successful = comeet_res.get("successes", 0)
    health.comeet_companies_failed = comeet_res.get("failures", 0)
    health.comeet_jobs_found = len(comeet_res.get("jobs", []))

    all_raw_jobs = linkedin_energy + linkedin_drones + comeet_res.get("jobs", [])
    
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
            result = evaluate_and_enrich_job_with_gemini(
                client, 
                job["title"], 
                job["company"], 
                job["snippet"], 
                is_drone, 
                health
            )
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
    temp_archive = update_weekly_archive(top_5_jobs)
    active_dashboard_jobs = temp_archive if temp_archive else top_5_jobs
    build_and_save_docs_app(active_dashboard_jobs, is_weekly=False)
    
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
        
    if health.linkedin_failures > 0 or health.comeet_companies_failed > 0:
        health.final_status = "DEGRADED"
    else:
        health.final_status = "SUCCESS"

    print(f"[DONE] Final Status: {health.final_status}")

if __name__ == "__main__":
    main()
