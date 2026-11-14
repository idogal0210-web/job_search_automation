import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.config import get_search_keywords, get_ats_boards, get_target_companies
from src.fetchers import (
    CircuitBreaker,
    RunHealth,
    fetch_linkedin_jobs,
    fetch_target_companies_linkedin_jobs,
    fetch_drushim_jobs,
    fetch_comeet_jobs,
    fetch_greenhouse_jobs,
    fetch_lever_jobs,
)
from src.job_policy import apply_keyword_fallback
from src.pipeline import evaluate_candidates, final_status, run_report
from src.publishers import send_email_report
from src.ui_builder import build_and_save_docs_app, update_weekly_archive
from src.state_manager import load_state, save_state_atomic, EvaluationLedger

load_dotenv()
STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "jobs_state.json")
DEFAULT_DASHBOARD_URL = "https://idogal0210-web.github.io/job_search_automation/"


def _outbox_path_for_state(state_file: str) -> Path:
    return Path(state_file).resolve().parent / "email_outbox.json"


def _batch_digest(links: list) -> str:
    payload = "|".join(sorted(str(x) for x in (links or [])))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


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


def get_target_company_queries(target_companies: list, batch_size: int = 5) -> list:
    """Generate batched OR queries for target companies."""
    queries = []
    unique_comps = list(dict.fromkeys(target_companies))
    for i in range(0, len(unique_comps), batch_size):
        chunk = unique_comps[i:i + batch_size]
        or_query = " OR ".join(f'"{c}"' for c in chunk)
        queries.append(f"({or_query})")
    return queries


def collect_all_jobs(health: RunHealth) -> list:
    """Fetch raw job postings across LinkedIn, Drushim, and direct ATS portals."""
    target_companies, _ = get_target_companies()
    keywords_config = get_search_keywords()
    energy_keywords = keywords_config.get("energy", [])
    drone_keywords = keywords_config.get("drones", [])
    drushim_keywords = keywords_config.get("drushim", [])

    target_queries = get_target_company_queries(target_companies)
    print(f"[FETCH] Scraping LinkedIn ({len(target_companies)} Target Companies in {len(target_queries)} batched queries)...")
    linkedin_targets = fetch_linkedin_jobs(target_queries, health, max_pages=1)

    print("[FETCH] Scraping LinkedIn (Energy)...")
    linkedin_energy = fetch_linkedin_jobs(energy_keywords, health, max_pages=2)
    print("[FETCH] Scraping LinkedIn (Drones)...")
    linkedin_drones = fetch_linkedin_jobs(drone_keywords, health, max_pages=2)

    print("[FETCH] Scraping Drushim (Israeli Industry, Energy & Operations)...")
    drushim_jobs = fetch_drushim_jobs(drushim_keywords, health, max_pages=1)

    breaker = CircuitBreaker(threshold=3)
    ats_boards = get_ats_boards()
    comeet_boards = ats_boards.get("comeet") or [
        {"slug": "enlightenergy", "uid": "99.006", "company": "Enlight Renewable Energy"}
    ]

    ats_jobs = []
    for board in comeet_boards:
        if breaker.is_open("comeet"):
            break
        prev_fail = health.comeet_failures
        print(f"[FETCH] Scraping Comeet ATS ({board.get('company', board['slug'])})...")
        batch = fetch_comeet_jobs(board["slug"], board["uid"], board.get("company", board["slug"]), health)
        if health.comeet_failures > prev_fail:
            breaker.record_failure("comeet")
        else:
            breaker.record_success("comeet")
        ats_jobs.extend(batch)

    for board in ats_boards.get("greenhouse", []):
        if breaker.is_open("greenhouse"):
            break
        prev_fail = health.greenhouse_failures
        print(f"[FETCH] Scraping Greenhouse ATS ({board.get('company', board['slug'])})...")
        batch = fetch_greenhouse_jobs(board["slug"], board.get("company", board["slug"]), health_metrics=health)
        if health.greenhouse_failures > prev_fail:
            breaker.record_failure("greenhouse")
        else:
            breaker.record_success("greenhouse")
        ats_jobs.extend(batch)

    for board in ats_boards.get("lever", []):
        if breaker.is_open("lever"):
            break
        prev_fail = health.lever_failures
        print(f"[FETCH] Scraping Lever ATS ({board.get('company', board['slug'])})...")
        batch = fetch_lever_jobs(board["slug"], board.get("company", board["slug"]), health_metrics=health)
        if health.lever_failures > prev_fail:
            breaker.record_failure("lever")
        else:
            breaker.record_success("lever")
        ats_jobs.extend(batch)

    all_raw_jobs = linkedin_targets + linkedin_energy + linkedin_drones + drushim_jobs + ats_jobs
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


def dispatch_notifications(
    processed_jobs: list,
    dashboard_ok: bool,
    health: RunHealth,
    outbox_path: Path = None,
):
    """
    Send daily email notifications with top qualified jobs using an atomic Outbox
    pattern so a crash in persist_state after SMTP delivery never re-sends duplicates.
    """
    sender_email = os.getenv("SENDER_EMAIL")
    sender_pwd = os.getenv("SENDER_APP_PASSWORD") or os.getenv("SENDER_PASSWORD")
    email_configured = bool(sender_email and sender_pwd)

    # Single unified status calculation before email dispatch
    health.final_status = final_status(
        health,
        email_configured=email_configured,
        dashboard_ok=dashboard_ok,
        state_ok=True,
        check_email_result=False,
    )

    daily_top_picks = processed_jobs[:5]
    batch_links = [job.get("link", "") for job in daily_top_picks if job.get("link")]
    digest = _batch_digest(batch_links)
    resolved_outbox = outbox_path or _outbox_path_for_state(STATE_FILE)

    if email_configured:
        existing_outbox = load_state(str(resolved_outbox), default={}, strict=False) or {}
        if (
            batch_links
            and isinstance(existing_outbox, dict)
            and existing_outbox.get("status") == "SENT"
            and existing_outbox.get("digest") == digest
        ):
            print("[EMAIL_OUTBOX] Batch already SENT in unacknowledged outbox; skipping duplicate email send", flush=True)
            health.email_success = True
            return email_configured, daily_top_picks

        try:
            save_state_atomic(
                str(resolved_outbox),
                {
                    "status": "SENDING",
                    "links": batch_links,
                    "digest": digest,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            pass

        dashboard_url = os.getenv("DASHBOARD_URL", DEFAULT_DASHBOARD_URL)
        send_email_report(sender_email, sender_pwd, daily_top_picks, dashboard_url, health)

        try:
            save_state_atomic(
                str(resolved_outbox),
                {
                    "status": "SENT" if health.email_success else "FAILED",
                    "links": batch_links,
                    "digest": digest,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception:
            pass
    else:
        print("[EMAIL] Not configured; qualified jobs remain READY for future delivery", flush=True)

    return email_configured, daily_top_picks


def persist_state(
    ledger: EvaluationLedger, daily_top_picks: list, handled_links: set,
    state_file: str, sync_state_path: Path, dashboard_ok: bool,
    email_configured: bool, health: RunHealth
) -> bool:
    """Commit delivery, acknowledge outbox, and atomically save handled links."""
    state_ok = True
    try:
        batch_links = [job["link"] for job in daily_top_picks if job.get("link")]
        if dashboard_ok and email_configured and health.email_success:
            ledger.commit_delivery(batch_links)
        handled_links.update(ledger.completed_links())
        if sync_state_path.exists():
            sync_state = load_state(str(sync_state_path), default={}, strict=False) or {}
            handled_links.update(sync_state.get("purged", []))
            handled_links.update(sync_state.get("rejected", []))
        save_state_atomic(state_file, sorted(handled_links))

        if dashboard_ok and email_configured and health.email_success:
            outbox_file = _outbox_path_for_state(state_file)
            save_state_atomic(
                str(outbox_file),
                {
                    "status": "ACKED",
                    "links": batch_links,
                    "digest": _batch_digest(batch_links),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
            )
    except Exception as error:
        state_ok = False
        print(f"[STATE_ERROR] {type(error).__name__}: {error}", flush=True)
    return state_ok


def report_results(
    health: RunHealth, audit: dict, root: Path,
    dashboard_ok: bool, email_configured: bool, state_ok: bool
) -> int:
    """Compute final status, write run reports with quality metrics, and determine exit code."""
    health.final_status = final_status(
        health, email_configured=email_configured,
        dashboard_ok=dashboard_ok, state_ok=state_ok
    )
    inactive_report_path = root / "data" / "inactive_jobs.json"
    inactive_report = load_state(str(inactive_report_path), default=None, strict=False) if inactive_report_path.exists() else None
    report = run_report(health, audit, inactive_report=inactive_report)
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
                f"- Gate rejection rate: {report['quality_metrics']['gate_rejection_rate']:.1%}\n"
                f"- Estimated Gemini cost: ${report['quality_metrics']['estimated_gemini_cost_usd']:.4f}\n"
            )
    print(f"[DONE] Final Status: {health.final_status}", flush=True)
    return 1 if health.final_status.startswith("FAILED_") else 0


def main():
    root = Path(__file__).resolve().parent
    health, handled_links, ledger, sync_state_path = load_context(root, STATE_FILE)
    all_raw_jobs = collect_all_jobs(health)
    processed_jobs, audit = evaluate_all_jobs(all_raw_jobs, handled_links, health, ledger)
    dashboard_ok = publish_dashboard(processed_jobs, root)
    email_configured, daily_top_picks = dispatch_notifications(
        processed_jobs, dashboard_ok, health, outbox_path=_outbox_path_for_state(STATE_FILE)
    )
    state_ok = persist_state(
        ledger, daily_top_picks, handled_links, STATE_FILE,
        sync_state_path, dashboard_ok, email_configured, health
    )
    return report_results(health, audit, root, dashboard_ok, email_configured, state_ok)


if __name__ == "__main__":
    raise SystemExit(main())
