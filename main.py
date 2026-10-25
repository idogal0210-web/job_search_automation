import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.fetchers import RunHealth, fetch_linkedin_jobs, fetch_drushim_jobs, fetch_comeet_jobs
from src.job_policy import apply_keyword_fallback
from src.pipeline import evaluate_candidates, final_status, run_report
from src.publishers import send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic, EvaluationLedger

load_dotenv()
STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(line_buffering=True)
    health = RunHealth()
    root = Path(__file__).resolve().parent
    print("[INIT] Starting job search", flush=True)
    state = load_state(STATE_FILE, default=[], strict=True)
    if not isinstance(state, list) or not all(isinstance(link, str) for link in state):
        raise ValueError("jobs_state.json must remain a list of URLs")
    handled_links = set(state)
    ledger = EvaluationLedger(root / "data" / "evaluation_state.json")
    energy_keywords = [
        "SCADA Control Room Operator", "מפעיל חדר בקרה SCADA", "מפעיל מערכות SCADA",
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
        "Power Plant Maintenance Mechanic", "מכונאי אחזקת תחנות כוח",
        "Power Dispatcher", "מתאם סחר בחשמל", "בקר סחר באנרגיה",
        "Commercial Energy Operations", "בקר תפעול מסחרי",
        "Solar Site Manager", "מנהל אתר סולארי", "מנהל עבודה סולארי",
        "Solar Project Coordinator", "הנדסאי פרויקטים סולאריים",
        "Electrical Inspector", "מפקח עבודות חשמל",
        "Turbine Technician", "טכנאי טורבינות",
        "Thermal Plant Technician", "טכנאי מתקני אנרגיה תרמית",
        "I&C Technician", "טכנאי מכשור ובקרה"
    ]
    
    drone_keywords = [
        "Drone Integrator", "אינטגרטור רחפנים",
        "UAV Technician", 'טכנאי מערכות כטב"ם',
        "Drone Operator", "מפעיל רחפנים",
        "Integration and Testing Technician", "טכנאי אינטגרציה ובדיקות",
        "Internal Pilot", "מטיס פנים",
        "Aviation and UAV Mechanic", 'מכונאי תעופה וכטב"ם',
        "Payload Technician", 'טכנאי מטע"דים',
        "Field Test Operator", "מפעיל ניסויי שדה", "טכנאי ניסויי טיסה",
        "Tactical Drone Specialist", "מומחה מוצר שטח רחפנים",
        "Mechanical Assembler UAV", 'מרכיב מכאני כטב"ם'
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
        "מפעיל מערכות SCADA",
        "הנדסאי מכונות",
        "גז טבעי",
        "סולארי",
        "טכנאי מערכות BMS",
        "תחנת כוח",
        "טכנאי שירות",
        "רחפנים",
        'טכנאי כטב"ם'
    ]
    drushim_jobs = fetch_drushim_jobs(drushim_keywords, health, max_pages=1)

    print("[FETCH] Scraping Comeet ATS (Enlight Renewable Energy)...")
    comeet_jobs = fetch_comeet_jobs("enlightenergy", "99.006", "Enlight Renewable Energy", health)

    # Pure broad industry search across LinkedIn, Drushim and direct Comeet ATS
    all_raw_jobs = linkedin_energy + linkedin_drones + drushim_jobs + comeet_jobs


    new_jobs = ledger.select(all_raw_jobs, handled_links)
    health.candidates_found = len(new_jobs)
    print(f"[FETCH] raw={len(all_raw_jobs)} candidates_including_pending={len(new_jobs)}", flush=True)
    client = None
    if os.getenv("GEMINI_API_KEY"):
        try:
            client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(timeout=20000,
                    retry_options=types.HttpRetryOptions(attempts=1)))
        except Exception as error:
            print(f"[AI_CONFIG] Could not initialize Gemini client: {type(error).__name__}", flush=True)

    if client is None:
        print("[AI_CONFIG] No GEMINI_API_KEY; unresolved jobs will remain pending", flush=True)

    try:
        processed_jobs, audit = evaluate_candidates(new_jobs, client, health, ledger)
    finally:
        if client is not None:
            client.close()
    print(f"[EVALUATE] passed={health.jobs_passed} rejected={health.jobs_rejected} pending={health.pending_evaluations}", flush=True)

    dashboard_ok = False
    try:
        archive = update_weekly_archive(processed_jobs, str(root / "data" / "weekly_archive.json"), set())
        build_and_save_docs_app(archive, [], str(root), is_weekly=False)
        dashboard_ok = True
        print(f"[UI] Generated dashboard with {len(archive)} archive jobs; deployment is a separate workflow step")
    except Exception as error:
        print(f"[UI_ERROR] {type(error).__name__}: {error}", flush=True)

    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_APP_PASSWORD") or os.getenv("SENDER_PASSWORD")
    email_configured = bool(sender_email and sender_pwd)
    # This status describes evaluation/output preparation, before dispatch.
    health.final_status = ("DEGRADED_PENDING" if health.pending_evaluations else
                           "DEGRADED_NETWORK" if health.linkedin_failures + health.drushim_failures else
                           "SUCCESS")
    if not dashboard_ok:
        health.final_status = "FAILED_DASHBOARD"
    if email_configured:
        daily_top_picks = processed_jobs[:5]
        send_email_report(sender_email, sender_pwd, daily_top_picks, daily_top_picks,
                          daily_top_picks[:3],
                          "https://idogal0210-web.github.io/job_search_automation/", health)
    else:
        print("[EMAIL] Not configured; qualified jobs remain READY for future delivery", flush=True)

    state_ok = True
    try:
        # Reuse evaluated READY jobs on output failure; never rerun AI just to retry email.
        if dashboard_ok and email_configured and health.email_success:
            ledger.commit_delivery([job["link"] for job in processed_jobs])
        handled_links.update(ledger.completed_links())
        save_state_atomic(STATE_FILE, sorted(handled_links))
    except Exception as error:
        state_ok = False
        print(f"[STATE_ERROR] {type(error).__name__}: {error}", flush=True)
    health.final_status = final_status(health, email_configured=email_configured,
                                      dashboard_ok=dashboard_ok, state_ok=state_ok)
    report = run_report(health, audit)
    save_state_atomic(root / "reports" / "latest_run.json", report)
    print("[SUMMARY] " + json.dumps(report["health"], ensure_ascii=False), flush=True)
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(f"### Job search: {health.final_status}\n"
                         f"- Candidates: {health.candidates_found}\n"
                         f"- Qualified: {health.jobs_passed}\n"
                         f"- Pending complete evaluation: {health.pending_evaluations}\n")
    print(f"[DONE] Final Status: {health.final_status}", flush=True)
    return 1 if health.final_status.startswith("FAILED_") else 0


if __name__ == "__main__":
    raise SystemExit(main())
