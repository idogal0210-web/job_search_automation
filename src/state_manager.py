import json
import os
import shutil
import tempfile
from datetime import datetime, timezone

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
        if result.get("evaluation_complete") is True:
            stage = "READY" if result.get("status") == "QUALIFIED" else "COMPLETE"
        old = self.jobs.get(job["link"], {})
        self.jobs[job["link"]] = {
            "stage": stage, "job": {**job, **result},
            "attempts": old.get("attempts", 0) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Save after every evaluation: pending jobs survive even if the source disappears.
        self.save()

    def stage_candidates(self, jobs):
        for job in jobs:
            if job['link'] not in self.jobs:
                self.jobs[job['link']] = {
                    'stage': 'RETRY_PENDING', 'job': dict(job), 'attempts': 0,
                    'updated_at': datetime.now(timezone.utc).isoformat()}
        self.save()

    def select(self, raw_jobs, handled):
        selected = {}
        for link, record in self.jobs.items():
            if record["stage"] != "COMPLETE":
                selected[link] = dict(record["job"])
        for job in raw_jobs:
            link = job.get("link")
            if not isinstance(link, str) or not link.startswith(("https://", "http://")):
                print("[SKIP] malformed job URL", flush=True)
                continue
            record = self.jobs.get(link, {})
            if record.get("stage") == "COMPLETE" or (link in handled and not record):
                continue
            if link not in selected:
                selected[link] = dict(job)
            elif record.get("stage") != "READY" and len(job.get("snippet", "")) > len(selected[link].get("snippet", "")):
                selected[link].update(job)
        return list(selected.values())

    def commit_delivery(self, links):
        for link in links:
            if self.jobs[link]["stage"] == "READY":
                self.jobs[link]["stage"] = "COMPLETE"
        self.save()

    def completed_links(self):
        return {link for link, value in self.jobs.items() if value["stage"] == "COMPLETE"}
