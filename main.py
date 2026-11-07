import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.config import get_search_keywords
from src.fetchers import (
    RunHealth,
    fetch_linkedin_jobs,
    fetch_drushim_jobs,
    fetch_comeet_jobs,
    fetch_indeed_jobs,
    fetch_glassdoor_jobs,
)
from src.job_policy import apply_keyword_fallback
from src.pipeline import evaluate_candidates, final_status, run_report
from src.publishers import send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic, EvaluationLedger

load_dotenv()
STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")
DEFAULT_DASHBOARD_URL = "https://idogal0210-web.github.io/job_search_automation/"


def load_context(root: Path, state_file: str):
    """Initialize stream buffering, load handled links and evaluation ledger."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(line_buffering=True)
    health = RunHealth()
    print("[INIT] Starting job search", flush=True)
    state = load_state(state_file, default=[], strict=True)
    if not isinstance(state, list) or not all(isinstance(link, str) for link in state):
        raise ValueError("jobs_state.json must remain a list of URLs")
    handled_links = set(state)
    sync_state_path = root / "data" / "sync_state.json"
    if sync_state_path.exists():
        sync_state = load_state(str(sync_state_path), default={}, strict=False) or {}
        user_overrides = set(sync_state.get("purged", [])) | set(sync_state.get("rejected", []))
        handled_links.update(user_overrides)
    ledger = EvaluationLedger(root / "data" / "evaluation_state.json")
    return health, handled_links, ledger, sync_state_path


def collect_all_jobs(health: RunHealth) -> list:
    """Fetch raw job postings across LinkedIn, Drushim, Comeet ATS, Indeed, and Glassdoor."""
    keywords_config = get_search_keywords()
    energy_keywords = keywords_config.get("energy", [])
    drone_keywords = keywords_config.get("drones", [])
    drushim_keywords = keywords_config.get("drushim", [])
    indeed_keywords = keywords_config.get("indeed", [])
    glassdoor_keywords = keywords_config.get("glassdoor", [])

    print("[FETCH] Scraping LinkedIn (Energy)...")
    linkedin_energy = fetch_linkedin_jobs(energy_keywords, health, max_pages=2)
    print("[FETCH] Scraping LinkedIn (Drones)...")
    linkedin_drones = fetch_linkedin_jobs(drone_keywords, health, max_pages=2)

    print("[FETCH] Scraping Drushim (Israeli Industry, Energy & Operations)...")
    drushim_jobs = fetch_drushim_jobs(drushim_keywords, health, max_pages=1)

    print("[FETCH] Scraping Comeet ATS (Enlight Renewable Energy)...")
    comeet_jobs = fetch_comeet_jobs("enlightenergy", "99.006", "Enlight Renewable Energy", health)

    print("[FETCH] Scraping Indeed (Israel Energy, SCADA, Gas & Operations)...")
    indeed_jobs = fetch_indeed_jobs(indeed_keywords, health, max_pages=1)

    print("[FETCH] Scraping Glassdoor (Israel Energy, SCADA, Gas & Operations)...")
    glassdoor_jobs = fetch_glassdoor_jobs(glassdoor_keywords, health, max_pages=1)

    all_raw_jobs = linkedin_energy + linkedin_drones + drushim_jobs + comeet_jobs + indeed_jobs + glassdoor_jobs
    return all_raw_jobs


def evaluate_all_jobs(all_raw_jobs: list, handled_links: set, health: RunHealth, ledger: EvaluationLedger):
    """Filter new candidates and run AI evaluation pipeline."""
    new_jobs = ledger.select(all_raw_jobs, handled_links)
    health.candidates_found = len(new_jobs)
    print(f"[FETCH] raw={len(all_raw_jobs)} candidates_including_pending={len(new_jobs)}", flush=True)

    client = None
    if os.getenv("GEMINI_API_KEY"):
        try:
            client = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(
                    timeout=20000,
                    retry_options=types.HttpRetryOptions(attempts=1)
                )
            )
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
    return processed_jobs, audit


def publish_dashboard(processed_jobs: list, root: Path) -> bool:
    """Build and update the GitHub Pages static application."""
    dashboard_ok = False
    try:
        archive = update_weekly_archive(processed_jobs, str(root / "data" / "weekly_archive.json"), set())
        build_and_save_docs_app(archive, [], str(root), is_weekly=False)
        dashboard_ok = True
        print(f"[UI] Generated dashboard with {len(archive)} archive jobs; deployment is a separate workflow step")
    except Exception as error:
        print(f"[UI_ERROR] {type(error).__name__}: {error}", flush=True)
    return dashboard_ok


def dispatch_notifications(processed_jobs: list, dashboard_ok: bool, health: RunHealth):
    """Send daily email notifications with top qualified jobs."""
    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_APP_PASSWORD") or os.getenv("SENDER_PASSWORD")
    email_configured = bool(sender_email and sender_pwd)

    health.final_status = (
        "DEGRADED_PENDING" if health.pending_evaluations else
        "DEGRADED_NETWORK" if (
            health.linkedin_failures
            + health.drushim_failures
            + getattr(health, "comeet_failures", 0)
            + getattr(health, "indeed_failures", 0)
            + getattr(health, "glassdoor_failures", 0)
        ) else
        "SUCCESS"
    )
    if not dashboard_ok:
        health.final_status = "FAILED_DASHBOARD"

    daily_top_picks = processed_jobs[:5]
    if email_configured:
        dashboard_url = os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL)
        send_email_report(
            sender_email, sender_pwd, daily_top_picks, daily_top_picks,
            daily_top_picks[:3], dashboard_url, health
        )
    else:
        print("[EMAIL] Not configured; qualified jobs remain READY for future delivery", flush=True)

    return email_configured, daily_top_picks


def persist_state(
    ledger: EvaluationLedger, daily_top_picks: list, handled_links: set,
    state_file: str, sync_state_path: Path, dashboard_ok: bool,
    email_configured: bool, health: RunHealth
) -> bool:
    """Commit delivery and atomically save handled links."""
    state_ok = True
    try:
        if dashboard_ok and email_configured and health.email_success:
            ledger.commit_delivery([job["link"] for job in daily_top_picks])
        handled_links.update(ledger.completed_links())
        if sync_state_path.exists():
            sync_state = load_state(str(sync_state_path), default={}, strict=False) or {}
            handled_links.update(sync_state.get("purged", []))
            handled_links.update(sync_state.get("rejected", []))
        save_state_atomic(state_file, sorted(handled_links))
    except Exception as error:
        state_ok = False
        print(f"[STATE_ERROR] {type(error).__name__}: {error}", flush=True)
    return state_ok


def report_results(
    health: RunHealth, audit: dict, root: Path,
    dashboard_ok: bool, email_configured: bool, state_ok: bool
) -> int:
    """Compute final status, write run reports, and determine exit code."""
    health.final_status = final_status(
        health, email_configured=email_configured,
        dashboard_ok=dashboard_ok, state_ok=state_ok
    )
    report = run_report(health, audit)
    save_state_atomic(root / "reports" / "latest_run.json", report)
    print("[SUMMARY] " + json.dumps(report["health"], ensure_ascii=False), flush=True)

    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(
                f"### Job search: {health.final_status}\n"
                f"- Candidates: {health.candidates_found}\n"
                f"- Qualified: {health.jobs_passed}\n"
                f"- Pending complete evaluation: {health.pending_evaluations}\n"
            )
    print(f"[DONE] Final Status: {health.final_status}", flush=True)
    return 1 if health.final_status.startswith("FAILED_") else 0


def main():
    root = Path(__file__).resolve().parent
    health, handled_links, ledger, sync_state_path = load_context(root, STATE_FILE)
    all_raw_jobs = collect_all_jobs(health)
    processed_jobs, audit = evaluate_all_jobs(all_raw_jobs, handled_links, health, ledger)
    dashboard_ok = publish_dashboard(processed_jobs, root)
    email_configured, daily_top_picks = dispatch_notifications(processed_jobs, dashboard_ok, health)
    state_ok = persist_state(
        ledger, daily_top_picks, handled_links, STATE_FILE,
        sync_state_path, dashboard_ok, email_configured, health
    )
    return report_results(health, audit, root, dashboard_ok, email_configured, state_ok)


if __name__ == "__main__":
    raise SystemExit(main())
