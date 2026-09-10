import os
import sys
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

from src.fetchers import RunHealth, fetch_linkedin_jobs
from src.evaluators import evaluate_and_enrich_job_with_gemini, QuotaExhaustedError
from src.publishers import send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")

# FIX #5 (DRY): Single authoritative keyword-fallback function.
# Previously this block was copy-pasted twice inside the evaluation loop
# (once in the `except` branch, once in the `if result is None` branch),
# creating a risk of the two copies diverging silently.
FALLBACK_KEYWORDS = [
    "gas", "energy", "mechanical", "control",
    "infrastructure", "cleantech", "drone", "uav", "scada"
]

def apply_keyword_fallback(job: dict) -> dict:
    """Score a job deterministically using keyword matching when Gemini is unavailable."""
    text = f"{job.get('title', '')} {job.get('snippet', '')}".lower()
    match_count = sum(1 for word in FALLBACK_KEYWORDS if word in text)
    # FIX #6: Cap score at 100 to stay within the documented 0-100 range.
    score = min(100, match_count * 15)
    return {
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
        "company_requirements": "דרישות טכניות והתאמה לתחום על בסיס מילות מפתח (דרישות מפורטות בקישור המשרה)."
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
        "SCADA operator", "Power plant technician", "Natural gas operator",
        "Mechanical technician energy", "מפעיל חדר בקרה"
    ]
    drone_keywords = [
        "Drone operator", "UAV technician", "System integration drone",
        "מטיס פנים", "כטב\"ם אינטגרציה"
    ]

    print("[FETCH] Scraping LinkedIn (Energy)...")
    linkedin_energy = fetch_linkedin_jobs(energy_keywords, health, max_pages=1)
    print("[FETCH] Scraping LinkedIn (Drones)...")
    linkedin_drones = fetch_linkedin_jobs(drone_keywords, health, max_pages=1)

    all_raw_jobs = linkedin_energy + linkedin_drones

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
        client = genai.Client()
    else:
        print("[WARNING] GEMINI_API_KEY missing. Cannot evaluate jobs.")

    processed_jobs = []
    gemini_quota_exhausted = False  # Circuit Breaker flag
    if client:
        for job in new_jobs:
            is_drone = (
                "drone" in job.get("query", "").lower()
                or job.get("sector") in ["רחפנים אוטונומיים וביטחון", "רחפנים אוטונומיים"]
            )
            result = None

            if gemini_quota_exhausted:
                # Quota already confirmed exhausted — skip Gemini entirely, no sleep needed.
                print(f"[CIRCUIT BREAKER] Skipping Gemini for: {job.get('title')}")
            else:
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
                    result = None
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print(f"[API ERROR] Rate limit reached. Using keyword fallback for: {job.get('title')}")
                    else:
                        print(f"[API ERROR] Failure for: {job.get('title')}. Error: {e}. Using keyword fallback.")
                    result = None
                finally:
                    # Always sleep after a Gemini attempt to maintain a steady gap.
                    time.sleep(4)

            # Single DRY fallback call handles all failure paths.
            if result is None:
                print(f"[FALLBACK] Applying keyword fallback for: {job.get('title')}")
                result = apply_keyword_fallback(job)

            if result:
                job.update(result)
                threshold = 70 if is_drone else 60
                if job["match_score"] >= threshold:
                    processed_jobs.append(job)

    health.jobs_passed = len(processed_jobs)
    print(f"[EVALUATE] {len(processed_jobs)} jobs passed the score threshold.")

    # 5. Curate Top 5
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_5_jobs = processed_jobs[:5]
    top_3 = top_5_jobs[:3]

    # 6. Update Dashboard
    # FIX #7: Wrap dashboard steps in try/except so a rendering failure does
    #         not abort the entire pipeline (email and state save can still run).
    print("[UI] Updating Weekly Archive and Dashboard...")
    archive_file_path = os.path.join(os.path.dirname(__file__), "data", "weekly_archive.json")
    rejected_set = set()
    active_dashboard_jobs = top_5_jobs
    try:
        temp_archive = update_weekly_archive(top_5_jobs, archive_file_path, rejected_set)
        active_dashboard_jobs = temp_archive if temp_archive else top_5_jobs
        project_root = os.path.dirname(__file__)
        build_and_save_docs_app(active_dashboard_jobs, list(rejected_set), project_root, is_weekly=False)
        print("[UI] Dashboard updated successfully.")
    except Exception as e:
        print(f"[UI ERROR] Dashboard/archive update failed: {e}. Continuing to email step.")

    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    # 7. Dispatch Email
    print("[EMAIL] Building and dispatching email...")

    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_APP_PASSWORD") or os.getenv("SENDER_PASSWORD")

    # FIX #4: Named boolean — correctly handles the case where SENDER_EMAIL
    # is set but the password is missing (previously: state silently never saved).
    email_configured = bool(sender_email and sender_pwd)

    if email_configured:
        # Pass all 7 required arguments using named kwargs to prevent future
        # mis-ordering if the signature ever changes.
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
    # FIX #3 (continued): Only merge seen_this_run into handled_links now,
    # after all pipeline steps completed. Wrapped in try/except so a
    # state-save failure is logged but does not crash the process.
    try:
        if health.email_success or not email_configured:
            handled_links.update(seen_this_run)
            save_state_atomic(STATE_FILE, list(handled_links))
            print("[STATE] State saved securely.")
        else:
            print("[STATE] Email failed to send; NOT saving state so these jobs are retried next run.")
    except Exception as e:
        print(f"[STATE ERROR] Failed to save state: {e}. Jobs may be re-evaluated next run.")

    # 9. Determine Final Status
    # FIX #1: If ALL Gemini calls failed but keyword fallback still produced
    # passing jobs → DEGRADED_FALLBACK (not FAILED_AI + exit(1)).
    # Only exit(1) when zero jobs passed AND evaluations ran (genuine failure).
    if (
        health.gemini_failures > 0
        and health.gemini_successes == 0
        and health.jobs_evaluated > 0
    ):
        if health.jobs_passed == 0:
            health.final_status = "FAILED_AI"
            print(f"[DONE] Final Status: {health.final_status}")
            sys.exit(1)
        else:
            health.final_status = "DEGRADED_FALLBACK"
    elif health.linkedin_failures > 0:
        health.final_status = "DEGRADED"
    elif email_configured and not health.email_success:
        health.final_status = "FAILED_EMAIL"
    else:
        health.final_status = "SUCCESS"

    print(f"[DONE] Final Status: {health.final_status}")


if __name__ == "__main__":
    main()
