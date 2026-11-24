import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from src.url_utils import canonical_job_url, job_identity, content_identity

def load_state(filepath: str, default=None, *, strict=False):
    if default is None:
        default = {}
        
    if not os.path.exists(filepath):
        return default
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        if strict:
            raise
        return default

def save_state_atomic(filepath: str, data):
    filepath = os.fspath(filepath)
    bak_filepath = filepath + '.bak'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    fd, tmp_filepath = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(filepath)), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(filepath):
            shutil.copy2(filepath, bak_filepath)
        os.replace(tmp_filepath, filepath)
    finally:
        if os.path.exists(tmp_filepath):
            os.unlink(tmp_filepath)


class EvaluationLedger:
    """Separate retry snapshots from the backwards-compatible handled URL list."""
    def __init__(self, path):
        self.path = os.fspath(path)
        data = load_state(self.path, {"version": 1, "jobs": {}}, strict=True)
        if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("jobs"), dict):
            raise ValueError("Invalid evaluation ledger; refusing to reset history")
        self.jobs = data["jobs"]
        for link, entry in self.jobs.items():
            if not isinstance(link, str) or not isinstance(entry, dict) or entry.get("stage") not in {"RETRY_PENDING", "READY", "COMPLETE"} or not isinstance(entry.get("job"), dict):
                raise ValueError("Invalid evaluation ledger entry")

    def save(self):
        save_state_atomic(self.path, {"version": 1, "jobs": self.jobs})

    def record(self, job, result):
        stage = "RETRY_PENDING"
        old = self.jobs.get(job["link"], {})
        attempts = old.get("attempts", 0) + 1
        if result.get("evaluation_source") == "keyword_fallback":
            stage = "RETRY_PENDING"
        elif result.get("evaluation_complete") is True:
            stage = "READY" if result.get("status") == "QUALIFIED" else "COMPLETE"
        elif attempts >= 3:
            stage = "COMPLETE"
        entry_job = {**job, **result}
        if stage == "COMPLETE":
            entry_job["snippet"] = ""
            entry_job["description"] = ""
        self.jobs[job["link"]] = {
            "stage": stage, "job": entry_job,
            "attempts": attempts,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Save after every evaluation: pending jobs survive even if the source disappears.
        self.save()

    def stage_candidates(self, jobs):
        changed = False
        for job in jobs:
            if job['link'] not in self.jobs:
                changed = True
                self.jobs[job['link']] = {
                    'stage': 'RETRY_PENDING', 'job': dict(job), 'attempts': 0,
                    'updated_at': datetime.now(timezone.utc).isoformat()}
        if changed:
            self.save()

    def select(self, raw_jobs, handled, max_pending=30):
        handled_canonical = {canonical_job_url(link) for link in handled}
        known = {job_identity(record["job"]): link for link, record in self.jobs.items()}
        known_urls = {canonical_job_url(link): link for link in self.jobs}
        content_seen = {}
        for entry in self.jobs.values():
            key = content_identity(entry["job"])
            if key:
                content_seen[key] = entry["job"]

        new_selected = {}
        for job in raw_jobs:
            link = job.get("link")
            if not canonical_job_url(link):
                print("[SKIP] malformed job URL", flush=True)
                continue
            identity = job_identity(job)
            existing = known.get(identity) or known_urls.get(canonical_job_url(link))
            if existing and existing != link:
                continue
            if canonical_job_url(link) in handled_canonical and not existing:
                continue
            content_key = content_identity(job)
            previous = content_seen.get(content_key) if content_key else None
            if previous and previous.get("link") != link and previous.get("source") and job.get("source") and previous["source"] != job["source"]:
                # Different explicit requisition IDs must remain separate.
                if not (previous.get("source_id") and job.get("source_id") and previous["source_id"] != job["source_id"]):
                    continue
            if content_key:
                content_seen[content_key] = job
            known[identity] = link
            known_urls[canonical_job_url(link)] = link
            record = self.jobs.get(link, {})
            if record.get("stage") == "COMPLETE" or (link in handled and not record):
                continue
            if link not in new_selected:
                new_selected[link] = dict(job)
            elif record.get("stage") != "READY" and len(job.get("snippet", "")) > len(new_selected[link].get("snippet", "")):
                new_selected[link].update(job)

        ready_selected = {}
        pending_selected = {}
        pending_count = 0
        for link, record in self.jobs.items():
            if record["stage"] == "READY":
                if link not in new_selected:
                    ready_selected[link] = dict(record["job"])
            elif record["stage"] == "RETRY_PENDING":
                if record.get("attempts", 0) >= 3:
                    record["stage"] = "COMPLETE"
                    continue
                if link in new_selected:
                    continue
                if pending_count >= max_pending:
                    continue
                pending_count += 1
                pending_selected[link] = dict(record["job"])

        # Prioritize new jobs from current run before pulling from RETRY_PENDING
        # READY jobs are delivered first (cached, 0 AI cost), followed by new candidates, then RETRY_PENDING
        return list(ready_selected.values()) + list(new_selected.values()) + list(pending_selected.values())

    def commit_delivery(self, links):
        for link in links:
            if self.jobs[link]["stage"] == "READY":
                self.jobs[link]["stage"] = "COMPLETE"
                if "job" in self.jobs[link]:
                    self.jobs[link]["job"]["snippet"] = ""
                    self.jobs[link]["job"]["description"] = ""
        self.save()

    def completed_links(self):
        return {link for link, value in self.jobs.items() if value["stage"] == "COMPLETE"}
