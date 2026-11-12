#!/usr/bin/env python3
"""
Scan Inactive Jobs Engine.
Validates job URLs to detect expired, closed, or removed postings.
Outputs structured findings to data/inactive_jobs.json and docs/data/inactive_jobs.json.
Enforces strict zero emoji policy.
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.ats_client import fetch_ats_job_detail

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("scan_inactive_jobs")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

INACTIVE_SIGNATURES = [
    # English indicators - LinkedIn & International
    (r"not currently accepting applications", "הגשת המועמדות נסגרה (Not currently accepting applications)"),
    (r"no longer accepting applications", "הגשת המועמדות נסגרה (No longer accepting applications)"),
    (r"(?:not|no longer|not currently)\s+accepting\s+applications", "הגשת המועמדות נסגרה"),
    (r"this job is no longer available", "המשרה אינה זמינה עוד"),
    (r"this position is closed", "המשרה נסגרה"),
    (r"position is no longer open", "המשרה אינה פתוחה עוד"),
    (r"job posting has expired", "תוקף פרסום המשרה פג"),
    (r"applications are no longer being accepted", "הגשת המועמדות נסגרה"),
    (r"closed-job__flavor", "משרה סגורה בלינקדאין"),
    (r"topcard__flavor--closed", "משרה סגורה בלינקדאין"),
    (r"page not found", "דף המשרה לא נמצא"),
    (r"job (?:has been|was) (?:filled|closed|removed)", "המשרה נסגרה"),
    (r"no longer (?:available|open|active)", "המשרה אינה זמינה עוד"),
    (r"this (?:job|position|role) (?:is|has been) (?:closed|filled|expired)", "המשרה נסגרה"),
    (r"posting (?:is )?(?:closed|expired)", "תוקף פרסום המשרה פג"),
    (r"position (?:has been )?filled", "המשרה אויישה"),
    (r"המשרה אוישה", "המשרה אוישה"),
    (r"המשרה הוסרה", "המשרה הוסרה מהאתר"),
    (r"פג תוקף", "תוקף פרסום המשרה פג"),
    # Hebrew indicators
    (r"המשרה (?:אינה|איננה) פעילה", "המשרה אינה פעילה באתר"),
    (r"המשרה נסגרה", "המשרה נסגרה לקבלת מועמדויות"),
    (r"דף המשרה לא נמצא", "דף המשרה לא נמצא באתר"),
    (r"לא אותרה משרה", "לא אותרה משרה פעילה"),
    (r"מודעה זו אינה רלוונטית", "המודעה אינה רלוונטית עוד"),
    (r"הגשת מועמדות למשרה זו הסתיימה", "הגשת מועמדות הסתיימה"),
    (r"(?:אינה|איננה|לא) מקבלת מועמדויות", "הגשת המועמדות נסגרה"),
]


def _valid_through_expired(html: str) -> bool:
    """Returns True when a JSON-LD JobPosting declares a validThrough date in the past."""
    for match in re.finditer(r'"validThrough"\s*:\s*"(\d{4}-\d{2}-\d{2})', html):
        try:
            if datetime.strptime(match.group(1), "%Y-%m-%d").date() < datetime.now(timezone.utc).date():
                return True
        except ValueError:
            continue
    return False


def check_job_url(job: Dict, timeout: int = 12) -> Tuple[str, str, int]:
    """
    Classifies a job URL.
    Returns: (state, reason, status_code) where state is one of
    "inactive" (confirmed closed/removed), "active" (loaded, no closure signal) or
    "unknown" (could not be verified: blocked, rate limited, server error, timeout).
    """
    link = job.get("link", "").strip()
    if not link or not link.startswith("http"):
        return "inactive", "קישור לא תקין או חסר", 0

    ats_res = fetch_ats_job_detail(link, timeout=timeout)
    if ats_res is not None:
        return ats_res["state"], ats_res["reason"], int(ats_res.get("status_code") or 0)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    resp = None
    last_error = ""
    for attempt in range(2):
        try:
            resp = requests.get(link, headers=headers, timeout=timeout, allow_redirects=True)
        except requests.exceptions.Timeout:
            last_error = "פסק זמן בבדיקת הקישור"
        except requests.exceptions.RequestException as exc:
            last_error = f"שגיאת תקשורת: {str(exc)[:50]}"
        else:
            if resp.status_code in (429, 503) and attempt == 0:
                time.sleep(2)
                continue
            break
        time.sleep(1)

    if resp is None:
        return "unknown", last_error or "לא ניתן לאמת את הקישור", 0

    status = resp.status_code
    if status in (404, 410):
        return "inactive", f"דף המשרה הוסר (HTTP {status})", status
    if status in (401, 403, 429) or status >= 500:
        return "unknown", f"האתר חסם או לא ענה (HTTP {status}), לא ניתן לאמת", status

    final_url = resp.url.lower()
    if "jobs/view" in link.lower() and "jobs/view" not in final_url and "linkedin.com" in final_url:
        return "inactive", "הפניה לדף ראשי - המשרה הוסרה", status

    html = resp.text
    text = html.lower()
    for pattern, reason in INACTIVE_SIGNATURES:
        if re.search(pattern, text, re.IGNORECASE):
            return "inactive", reason, status
    if _valid_through_expired(html):
        return "inactive", "תוקף פרסום המשרה פג (validThrough)", status

    return "active", "משרה פעילה ומאומתת", status


def load_target_jobs(jobs_path: str) -> List[Dict]:
    """Loads active jobs from jobs.json."""
    if not os.path.exists(jobs_path):
        logger.warning(f"File not found: {jobs_path}")
        return []
    try:
        with open(jobs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("jobs", [])
            elif isinstance(data, list):
                return data
    except Exception as exc:
        logger.error(f"Error reading {jobs_path}: {exc}")
    return []


def run_scanner(limit: Optional[int] = None, max_workers: int = 5, dry_run: bool = False) -> Dict:
    """Executes the inactive jobs scanner."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    jobs_path = os.path.join(root_dir, "docs", "data", "jobs.json")
    if not os.path.exists(jobs_path):
        jobs_path = os.path.join(root_dir, "data", "jobs.json")

    all_jobs = load_target_jobs(jobs_path)
    if limit and limit > 0:
        all_jobs = all_jobs[:limit]

    logger.info(f"Scanning {len(all_jobs)} jobs for inactive/closed status...")

    inactive_list = []
    scanned_links = []
    unknown_links = []
    scanned_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_job = {executor.submit(check_job_url, job): job for job in all_jobs}
        for future in as_completed(future_to_job):
            job = future_to_job[future]
            scanned_count += 1
            try:
                state, reason, status_code = future.result()
                if state == "unknown":
                    unknown_links.append(job.get("link", ""))
                else:
                    scanned_links.append(job.get("link", ""))
                if state == "inactive":
                    inactive_item = {
                        "link": job.get("link", ""),
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "reason": reason,
                        "status_code": status_code,
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                    }
                    inactive_list.append(inactive_item)
                    logger.info(f"[INACTIVE] {job.get('title')} at {job.get('company')} -> {reason}")
            except Exception as exc:
                logger.warning(f"Error evaluating job {job.get('link')}: {exc}")

    report = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "total_scanned": scanned_count,
        "inactive_count": len(inactive_list),
        "unknown_count": len(unknown_links),
        "inactive_jobs": inactive_list,
        "verified_links": scanned_links,
        "unknown_links": unknown_links,
    }

    if not dry_run:
        out_dirs = [
            os.path.join(root_dir, "data"),
            os.path.join(root_dir, "docs", "data"),
        ]
        for out_dir in out_dirs:
            os.makedirs(out_dir, exist_ok=True)
            out_file = os.path.join(out_dir, "inactive_jobs.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"Report saved to {out_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description="Scan inactive and closed job postings.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of jobs to scan")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent worker threads")
    parser.add_argument("--dry-run", action="store_true", help="Run scan without writing results to disk")
    args = parser.parse_args()

    report = run_scanner(limit=args.limit, max_workers=args.workers, dry_run=args.dry_run)
    logger.info(
        f"Completed scan: {report['total_scanned']} checked, {report['inactive_count']} inactive detected, {report['unknown_count']} unverified."
    )


if __name__ == "__main__":
    main()
