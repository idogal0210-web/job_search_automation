import os
import sys
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

from src.fetchers import (
    RunHealth,
    fetch_linkedin_jobs,
    fetch_linkedin_full_job_description,
    fetch_drushim_jobs,
    fetch_drushim_full_job_description
)
from src.evaluators import evaluate_and_enrich_job_with_gemini, QuotaExhaustedError, NON_TECHNICAL_TITLES
from src.salary_engine import evaluate_job_salary
from src.publishers import send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")

# Authoritative keyword-fallback function for technical failures only.
FALLBACK_KEYWORDS = [
    "gas", "energy", "mechanical", "control",
    "infrastructure", "cleantech", "drone", "uav", "scada",
    "solar", "energy tech", "גז", "אנרגיה", "מכונות", "בקרה", "סולארי", "רחפנים", "תחנת כוח"
]

def apply_keyword_fallback(job: dict) -> dict:
    """Score a job deterministically using keyword matching when Gemini is unavailable.
    Strictly enforces non-technical and blacklist filters before awarding scores.
    """
    title_lower = job.get("title", "").lower()
    company_lower = job.get("company", "").lower()

    # Pre-check blacklist
    for bl in ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון"]:
        if bl in company_lower:
            return {
                "status": "DISQUALIFIED",
                "match_score": 0,
                "concrete_matches_count": 0,
                "reasoning": f"חברה ברשימה השחורה ({job.get('company')})",
                "disqualification_reason": "blacklist"
            }

    # Pre-check non-technical roles
    for non_tech in NON_TECHNICAL_TITLES:
        if non_tech in title_lower:
            return {
                "status": "DISQUALIFIED",
                "match_score": 0,
                "concrete_matches_count": 0,
                "reasoning": f"תפקיד לא טכני שנפסל בגיבוי ({non_tech})",
                "disqualification_reason": "non_technical_role"
            }

    text = f"{job.get('title', '')} {job.get('snippet', '')}".lower()
    match_count = sum(1 for word in FALLBACK_KEYWORDS if word in text)
    score = min(100, match_count * 15)
    sal_intel = evaluate_job_salary(job)
    return {
        "status": "QUALIFIED" if score >= 50 else "DISQUALIFIED",
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
        "work_model": "N/A",
        "company_requirements": "דרישות טכניות והתאמה לתחום על בסיס מילות מפתח (דרישות מפורטות בקישור המשרה).",
        "salary_range": sal_intel["salary_range"],
        "salary_source_type": sal_intel["salary_source_type"],
        "salary_source_label": sal_intel["salary_source_label"],
        "salary_source_url": sal_intel["salary_source_url"],
        "salary_evidence": sal_intel["salary_evidence"],
        "salary_confidence": sal_intel.get("salary_confidence", "medium"),
    }


def main():
    health = RunHealth()
    print("[INIT] Starting Morning Job Search Automation (Modular Architecture)")

    # 1. Load state
    # We expect jobs_state.json to be a list of handled job links/IDs
    state = load_state(STATE_FILE, default=[])
    handled_links = set(state)

    # 2. Fetch Jobs
    energy_keywords = [
        "SCADA Control Room Operator", "מפעיל חדר בקרה SCADA", "בקר SCADA",
        "Gas Plant Operator", "מפעיל מתקן גז",
        "Gas Transmission Technician", "טכנאי הולכת גז",
        "Gas Systems Controller", "בקר מערכות גז",
        "Rotating Equipment Mechanic", "מכונאי ציוד סובב",
        "Burner Technician", "טכנאי מבערים",
        "Natural Gas Technician", "הנדסאי גז טבעי",
        "Solar Technician", "הנדסאי סולארי",
        "Solar Construction Inspector", "מפקח הקמה סולארי",
        "Solar O&M Technician", "טכנאי תפעול ואחזקה סולארי",
        "Solar Field Service Engineer", "מהנדס שירות שטח סולארי",
        "PV Monitoring Operator", "מפעיל מערכות ניטור פאנלים",
        "High Voltage Technician", "טכנאי מתח עליון",
        "PV Technician", "טכנאי פוטו-וולטאי",
        "Power Plant Technician", "טכנאי תחנת כוח",
        "BMS Operator", "בקר מבנה",
        "Electro-Mechanical Technician", "טכנאי מערכות אלקטרו-מכניות",
        "Field Service Engineer", "מהנדס שירות שטח",
        "Infrastructure Systems Operator", "מפעיל מערכות תשתית",
        "Energy Control Room Operator", "מפעיל חדר בקרת אנרגיה",
        "Power Plant Maintenance Mechanic", "מכונאי אחזקת תחנות כוח"
    ]
    
    drone_keywords = [
        "Drone Integrator", "אינטגרטור רחפנים",
        "UAV Technician", 'טכנאי מערכות כטב"ם',
        "Drone Operator", "מפעיל רחפנים",
        "Integration and Testing Technician", "טכנאי אינטגרציה ובדיקות",
        "Internal Pilot", "מטיס פנים",
        "Aviation and UAV Mechanic", 'מכונאי תעופה וכטב"ם',
        "Payload Technician", 'טכנאי מטע"דים'
    ]
    
    energy_tech_keywords = [
        "Energy Storage Technician", "הנדסאי אגירת אנרגיה",
        "BESS Technician", "טכנאי מערכות סוללות",
        "Commissioning Technician", "טכנאי מסירה והפעלה",
        "EV Charging Infrastructure Technician", "טכנאי תשתיות טעינה",
        "Microgrid Operator", "מפעיל מיקרו-גריד",
        "Smart Energy Integrator", "אינטגרטור אנרגיה חכמה",
        "CleanTech Technician", "טכנאי קלינטק"
    ]
    
    # Extend energy keywords with energy tech
    energy_keywords.extend(energy_tech_keywords)

    print("[FETCH] Scraping LinkedIn (Energy)...")
    linkedin_energy = fetch_linkedin_jobs(energy_keywords, health, max_pages=2)
    print("[FETCH] Scraping LinkedIn (Drones)...")
    linkedin_drones = fetch_linkedin_jobs(drone_keywords, health, max_pages=2)

    print("[FETCH] Scraping Drushim (Israeli Industry, Energy & Operations)...")
    drushim_keywords = [
        "מפעיל חדר בקרה SCADA",
        "בקר SCADA",
        "הנדסאי מכונות",
        "גז טבעי",
        "סולארי",
        "בקרת מבנה",
        "תחנת כוח",
        "טכנאי שירות",
        "רחפנים",
        'טכנאי כטב"ם'
    ]
    drushim_jobs = fetch_drushim_jobs(drushim_keywords, health, max_pages=1)

    # Pure broad industry search across LinkedIn and Drushim
    all_raw_jobs = linkedin_energy + linkedin_drones + drushim_jobs

    # 3. Filter New Jobs
    # FIX #2: Use j.get("link") to avoid a hard crash (KeyError) if a scraped
    #         record is missing the "link" field. Skip only that bad record.
    # FIX #3: Do NOT merge into handled_links here. Track new links in a
    #         separate `seen_this_run` set and only persist them after the full
    #         pipeline (evaluation → dashboard → email) completes successfully.
    new_jobs = []
    seen_this_run = set()
    skipped_malformed = 0
    for j in all_raw_jobs:
        link = j.get("link")
        if not link:
            skipped_malformed += 1
            print(f"[WARNING] Skipping malformed job with no 'link': {j.get('title', 'Unknown')}")
            continue
        if link not in handled_links and link not in seen_this_run:
            new_jobs.append(j)
            seen_this_run.add(link)

    health.candidates_found = len(new_jobs)
    malformed_note = f" ({skipped_malformed} skipped, missing link)" if skipped_malformed else ""
    print(f"[FILTER] Found {len(new_jobs)} new jobs out of {len(all_raw_jobs)} total.{malformed_note}")

    # 4. Evaluate with AI
    client = None
    if os.getenv("GEMINI_API_KEY"):
        client = genai.Client(http_options={'timeout': 20000}) # 20 seconds timeout
    else:
        print("[WARNING] GEMINI_API_KEY missing. Cannot evaluate jobs.")

    processed_jobs = []
    gemini_quota_exhausted = False  # Circuit Breaker flag
    successfully_evaluated_links = set()

    if client:
        for job in new_jobs:
            is_drone = (
                "drone" in job.get("query", "").lower()
                or job.get("sector") in ["רחפנים אוטונומיים וביטחון", "רחפנים אוטונומיים"]
            )
            result = None
            is_technical_error = False

            if gemini_quota_exhausted:
                # Quota already confirmed exhausted — skip Gemini entirely, no sleep needed.
                print(f"[CIRCUIT BREAKER] Skipping Gemini for: {job.get('title')}")
                is_technical_error = True
            else:
                # Two-Stage Enrichment: If snippet is very brief (< 250 chars), fetch full description
                if "linkedin.com" in job.get("link", "") and len(job.get("snippet", "")) < 250:
                    full_desc = fetch_linkedin_full_job_description(job["link"])
                    if full_desc:
                        job["snippet"] = full_desc
                elif "drushim.co.il" in job.get("link", "") and len(job.get("snippet", "")) < 250:
                    full_desc = fetch_drushim_full_job_description(job["link"])
                    if full_desc:
                        job["snippet"] = full_desc

                try:
                    result = evaluate_and_enrich_job_with_gemini(
                        client,
                        job["title"],
                        job["company"],
                        job["snippet"],
                        is_drone,
                        health
                    )
                except QuotaExhaustedError:
                    # Hard daily quota hit — activate circuit breaker for this run.
                    gemini_quota_exhausted = True
                    is_technical_error = True
                    result = None
                except Exception as e:
                    is_technical_error = True
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print(f"[API ERROR] Rate limit reached. Using keyword fallback for: {job.get('title')}")
                    else:
                        print(f"[API ERROR] Failure for: {job.get('title')}. Error: {e}. Using keyword fallback.")
                    result = None
                finally:
                    # Adaptive steady gap between Gemini calls
                    time.sleep(2)

            # Apply keyword fallback ONLY for technical service failures, NEVER for business disqualifications
            if result is None and is_technical_error:
                print(f"[FALLBACK] Applying keyword fallback for: {job.get('title')}")
                result = apply_keyword_fallback(job)

            if result:
                job.update(result)
                job_link = job.get("link")

                # If job was evaluated (qualified or disqualified), record it as completed
                if result.get("status") in ["QUALIFIED", "DISQUALIFIED"] or result.get("match_score", 0) > 0:
                    if job_link:
                        successfully_evaluated_links.add(job_link)

                # Collect passing jobs
                if result.get("status") != "DISQUALIFIED":
                    threshold = 70 if is_drone else 60
                    if job.get("match_score", 0) >= threshold:
                        processed_jobs.append(job)

    health.jobs_passed = len(processed_jobs)
    print(f"[EVALUATE] {len(processed_jobs)} jobs passed the score threshold.")

    # 5. Curate Top Picks & Prepare Dashboard Archive
    # Keep ALL passing jobs sorted by match_score for the Interactive Dashboard and Archive
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_5_jobs = processed_jobs[:5]
    top_3 = top_5_jobs[:3]

    # 6. Update Dashboard (Preserving ALL passing jobs, not only top 5!)
    print(f"[UI] Updating Weekly Archive and Dashboard with all {len(processed_jobs)} qualified jobs...")
    archive_file_path = os.path.join(os.path.dirname(__file__), "data", "weekly_archive.json")
    rejected_set = set()
    active_dashboard_jobs = processed_jobs
    try:
        temp_archive = update_weekly_archive(processed_jobs, archive_file_path, rejected_set)
        active_dashboard_jobs = temp_archive if temp_archive else processed_jobs
        project_root = os.path.dirname(__file__)
        build_and_save_docs_app(active_dashboard_jobs, list(rejected_set), project_root, is_weekly=False)
        print(f"[UI] Dashboard updated successfully with {len(active_dashboard_jobs)} active archive jobs.")
    except Exception as e:
        print(f"[UI ERROR] Dashboard/archive update failed: {e}. Continuing to email step.")

    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    # 7. Dispatch Email (Top curated jobs only)
    print("[EMAIL] Building and dispatching email...")

    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_APP_PASSWORD") or os.getenv("SENDER_PASSWORD")

    email_configured = bool(sender_email and sender_pwd)

    if email_configured:
        send_email_report(
            sender_email=sender_email,
            sender_pwd=sender_pwd,
            processed_jobs=processed_jobs,
            curated_email_jobs=top_5_jobs,
            top_3=top_3,
            dashboard_url=dashboard_url,
            health=health,
        )
    else:
        print("[WARNING] Missing email credentials (SENDER_EMAIL and/or SENDER_APP_PASSWORD).")

    # 8. Save State Atomically
    # Save ONLY successfully evaluated jobs into handled_links!
    # Any job that hit an unhandled retryable error will NOT be marked as handled and will be retried next run.
    try:
        if health.email_success or not email_configured:
            handled_links.update(successfully_evaluated_links)
            save_state_atomic(STATE_FILE, list(handled_links))
            print(f"[STATE] State saved securely ({len(successfully_evaluated_links)} new links committed).")
        else:
            print("[STATE] Email failed to send; NOT saving state so these jobs are retried next run.")
    except Exception as e:
        print(f"[STATE ERROR] Failed to save state: {e}. Jobs may be re-evaluated next run.")

    # 9. Determine Final Status with High Integrity
    # Distinguish genuine technical service failure from a healthy empty run
    total_network_failures = health.linkedin_failures + health.drushim_failures
    total_network_attempts = health.linkedin_requests + health.drushim_requests

    if health.gemini_attempts > 0 and health.gemini_successes == 0:
        if health.jobs_passed == 0:
            health.final_status = "FAILED_AI"
            print(f"[DONE] Final Status: {health.final_status} (AI service exhausted/failed)")
            sys.exit(1)
        else:
            health.final_status = "DEGRADED_FALLBACK"
    elif total_network_attempts > 0 and total_network_failures >= total_network_attempts:
        health.final_status = "FAILED_SCRAPERS"
        print(f"[DONE] Final Status: {health.final_status} (Scraper network failure)")
        sys.exit(1)
    elif health.linkedin_failures > 0 or health.drushim_failures > 0:
        health.final_status = "DEGRADED_NETWORK"
    elif email_configured and not health.email_success:
        health.final_status = "FAILED_EMAIL"
    elif len(new_jobs) == 0:
        health.final_status = "SUCCESS_EMPTY_RUN"
    else:
        health.final_status = "SUCCESS"

    print(f"[DONE] Final Status: {health.final_status}")


if __name__ == "__main__":
    main()
