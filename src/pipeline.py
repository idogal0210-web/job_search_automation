"""Evaluation orchestration, separated from scraping and delivery for offline tests."""
import json
from dataclasses import asdict
from urllib.parse import urlparse

from src.evaluators import evaluate_and_enrich_job_with_gemini
from src.gemini_runtime import EvaluationUnavailable, GeminiPool
from src.job_policy import apply_keyword_fallback, deterministic_filter, is_drone_job
from src.fetchers import fetch_linkedin_full_job_description, fetch_drushim_full_job_description


def enrich(job):
    if job.get("description_complete") or job.get("description"):
        if job.get("description"):
            job["snippet"] = job["description"]
        return
    if job.get("source") not in {"LinkedIn", "Drushim"} and len(job.get("snippet", "")) >= 250:
        return
    host = (urlparse(job["link"]).hostname or "").lower()
    full = ""
    if host == "linkedin.com" or host.endswith(".linkedin.com"):
        full = fetch_linkedin_full_job_description(job["link"])
    elif host == "drushim.co.il" or host.endswith(".drushim.co.il"):
        full = fetch_drushim_full_job_description(job["link"])
    if full:
        job["snippet"] = full
        job["description"] = full
        job["description_complete"] = True


def evaluate_candidates(jobs, client, health, ledger, *, pool=None, enrich_job=enrich):
    pool = pool or GeminiPool()
    ledger.stage_candidates(jobs)
    passed, audit = [], []
    for original in jobs:
        job = dict(original)
        record = ledger.jobs.get(job["link"], {})
        if record.get("stage") == "READY":
            result = dict(record["job"])
            health.cached_evaluations += 1
        else:
            # Clear stale result fields before retrying an earlier partial evaluation.
            job = {k: job.get(k, "") for k in ("link", "title", "company", "snippet", "query", "source", "location", "logo", "date", "source_id", "is_direct_ats", "description", "description_complete")}
            precheck = deterministic_filter(job)
            # A missing industrial evidence decision requires the full description first.
            if precheck and precheck.get("disqualification_reason") != "control_room_lacks_scada_or_high_salary":
                result = precheck
            else:
                enrich_job(job)
                if (len(job.get("snippet", "").strip()) < 100 or
                        (job.get("source") in {"LinkedIn", "Drushim"} and not job.get("description_complete"))):
                    result = {"status": "RETRY_PENDING", "match_score": 0,
                              "evaluation_complete": False, "evaluation_source": "missing_description",
                              "retry_reason": "insufficient_description", "reasoning": "תיאור המשרה חסר; נדרשת בדיקה חוזרת"}
                else:
                    result = deterministic_filter(job)
                    if result is None:
                        try:
                            if client is None:
                                raise EvaluationUnavailable({"client": "missing_or_invalid_configuration"})
                            result = evaluate_and_enrich_job_with_gemini(
                                client, job["title"], job["company"], job["snippet"],
                                is_drone_job(job), health, pool=pool)
                        except EvaluationUnavailable as error:
                            result = apply_keyword_fallback(job, str(error))
            if job.get("location") and job["location"] not in {"לא צוין", "ישראל"}:
                result["location"] = job["location"]
            ledger.record(job, result)
        job.update(result)
        health.jobs_evaluated += 1
        if result.get("evaluation_complete") is not True:
            health.pending_evaluations += 1
        if result.get("evaluation_source") == "keyword_fallback":
            health.fallback_evaluations += 1
        if result.get("status") == "DISQUALIFIED":
            health.jobs_rejected += 1
        if result.get("status") == "QUALIFIED" and result.get("evaluation_complete") is True:
            passed.append(job)
        audit.append({k: job.get(k) for k in (
            "link", "title", "company", "status", "evaluation_source", "evaluation_model",
            "base_match_score", "priority_bonus", "match_score", "keyword_score",
            "concrete_matches_count", "disqualification_reason", "retry_reason", "reasoning")})
        print("[JOB] " + json.dumps({key: value for key, value in audit[-1].items() if key != "reasoning"}, ensure_ascii=False), flush=True)
    health.jobs_passed = len(passed)
    return sorted(passed, key=lambda job: job["match_score"], reverse=True), audit


def final_status(health, *, email_configured, dashboard_ok=True, state_ok=True):
    if not state_ok:
        return "FAILED_STATE"
    if not dashboard_ok:
        return "FAILED_DASHBOARD"
    if email_configured and not health.email_success:
        return "FAILED_EMAIL"
    attempts = health.linkedin_requests + health.drushim_requests + health.comeet_requests
    failures = health.linkedin_failures + health.drushim_failures + health.comeet_failures
    if attempts and failures >= attempts:
        return "FAILED_SCRAPERS"
    if health.pending_evaluations:
        return "DEGRADED_PENDING"
    if failures:
        return "DEGRADED_NETWORK"
    if not email_configured:
        return "DEGRADED_EMAIL_NOT_CONFIGURED"
    return "SUCCESS_EMPTY_RUN" if health.candidates_found == 0 else "SUCCESS"


def run_report(health, audit):
    return {"health": asdict(health), "jobs": audit}
