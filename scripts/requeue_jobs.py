"""Explicit recovery of selected legacy jobs, never a reset of all history.

Input: JSON list of job objects with link/title/company/snippet, copied from
known job records. Defaults to dry-run. Run from the repository root.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.state_manager import EvaluationLedger


def requeue(ledger, jobs, apply=False):
    if not isinstance(jobs, list) or not jobs:
        raise ValueError('Input must be a nonempty list of selected job records')
    for job in jobs:
        if not isinstance(job, dict) or not all(isinstance(job.get(key), str) and job[key].strip()
                                               for key in ('link', 'title', 'company', 'snippet')):
            raise ValueError('Every job needs link, title, company and snippet')
        if not job['link'].startswith(('https://', 'http://')):
            raise ValueError('Job link must be HTTP(S)')
    links = sorted({job['link'] for job in jobs})
    if apply:
        for job in jobs:
            raw = {k: job[k] for k in ('link', 'title', 'company', 'snippet')}
            ledger.jobs[job['link']] = {'stage': 'RETRY_PENDING', 'job': raw, 'attempts': 0,
                                       'requeue_reason': 'explicit_legacy_recovery'}
        ledger.save()
    return links


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jobs', required=True, help='JSON file containing explicitly selected jobs')
    parser.add_argument('--apply', action='store_true', help='Write pending records (default is dry-run)')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    ledger = EvaluationLedger(root/'data/evaluation_state.json')
    jobs = json.loads(Path(args.jobs).read_text(encoding='utf-8'))
    links = requeue(ledger, jobs, apply=args.apply)
    print(json.dumps({'applied': args.apply, 'selected_links': links}, ensure_ascii=False, indent=2))
