#!/usr/bin/env python3
"""
Lightweight CLI inspection tool for workspace state and data files.
Provides concise counts, schema keys, and sync parity without dumping full datasets.
Zero emojis strictly enforced.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

def get_json_data(filename):
    path = DATA_DIR / filename
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

def show_summary():
    jobs_state = get_json_data("jobs_state.json")
    sync_data = get_json_data("sync_state.json")
    historical = get_json_data("historical_catalog.json")
    inactive = get_json_data("inactive_jobs.json")
    evaluation = get_json_data("evaluation_state.json")

    print("=== WORKSPACE DATA SUMMARY ===")
    
    # 1. jobs_state.json
    if isinstance(jobs_state, list):
        print(f"data/jobs_state.json total records: {len(jobs_state)}")
        tiers = {}
        for j in jobs_state:
            if isinstance(j, dict):
                t = j.get("tier", "unknown")
                tiers[t] = tiers.get(t, 0) + 1
        print(f"  Tier breakdown: {tiers}")
    else:
        print("data/jobs_state.json: Not found or empty")

    # 2. sync_state.json
    if isinstance(sync_data, dict):
        updated = sync_data.get("updated_at", "N/A")
        print(f"data/sync_state.json (updated: {updated}):")
        for key in ["saved", "starred", "rejected", "purged"]:
            val = sync_data.get(key, [])
            count = len(val) if isinstance(val, (list, dict)) else val
            print(f"  {key}: {count}")
    else:
        print("data/sync_state.json: Not found or empty")

    # 3. historical_catalog.json
    if isinstance(historical, dict):
        print(f"data/historical_catalog.json total cataloged jobs: {len(historical)}")

    # 4. inactive_jobs.json
    if isinstance(inactive, dict):
        total_scanned = inactive.get("total_scanned", "N/A")
        inactive_count = inactive.get("inactive_count", "N/A")
        print(f"data/inactive_jobs.json inactive/scanned: {inactive_count}/{total_scanned}")

    # 5. evaluation_state.json
    if isinstance(evaluation, dict) and "jobs" in evaluation:
        print(f"data/evaluation_state.json evaluated jobs: {len(evaluation['jobs'])}")

def show_keys(filename):
    data = get_json_data(filename)
    print(f"=== SCHEMA KEYS: data/{filename} ===")
    if data is None:
        print("File not found.")
        return
    if isinstance(data, list) and len(data) > 0:
        sample = data[0]
        if isinstance(sample, dict):
            print(f"Sample item keys (record 1 of {len(data)}):")
            for k in sorted(sample.keys()):
                val = sample[k]
                v_type = type(val).__name__
                print(f"  - {k} ({v_type})")
        else:
            print(f"List contains non-dict elements of type: {type(sample)}")
    elif isinstance(data, dict):
        # Check if values are dicts (catalog format)
        first_val = next(iter(data.values())) if len(data) > 0 else None
        if isinstance(first_val, dict):
            print(f"Top-level catalog with {len(data)} job URLs. Schema keys of catalog entry:")
            for k in sorted(first_val.keys()):
                val = first_val[k]
                v_type = type(val).__name__
                print(f"  - {k} ({v_type})")
        else:
            print(f"Top-level keys ({len(data)} keys):")
            for k in sorted(list(data.keys())[:20]):
                val = data[k]
                v_type = type(val).__name__
                print(f"  - {k} ({v_type})")
            if len(data) > 20:
                print(f"  ... and {len(data) - 20} more keys")
    else:
        print("Unsupported data structure.")

def show_single_job(query_str):
    query = str(query_str).strip()
    # Check historical_catalog.json
    historical = get_json_data("historical_catalog.json")
    if isinstance(historical, dict):
        # Direct URL match
        if query in historical:
            print(f"=== JOB RECORD FROM CATALOG: {query} ===")
            print(json.dumps(historical[query], indent=2, ensure_ascii=False))
            return
        # Partial URL or title match
        for url, job in historical.items():
            if isinstance(job, dict):
                if query in url or query.lower() in job.get("title", "").lower() or query.lower() in job.get("company", "").lower():
                    print(f"=== JOB RECORD MATCH ({job.get('company')} - {job.get('title')}): {url} ===")
                    print(json.dumps(job, indent=2, ensure_ascii=False))
                    return

    # Check evaluation_state.json
    evaluation = get_json_data("evaluation_state.json")
    if isinstance(evaluation, dict) and "jobs" in evaluation:
        jobs = evaluation["jobs"]
        if isinstance(jobs, dict) and query in jobs:
            print(f"=== EVALUATION RECORD: {query} ===")
            print(json.dumps(jobs[query], indent=2, ensure_ascii=False))
            return

    print(f"Job matching '{query}' not found in catalog or state.")

def main():
    parser = argparse.ArgumentParser(description="Inspect workspace state files efficiently without token bloat.")
    parser.add_argument("--summary", action="store_true", help="Print concise counts and tier distributions across data/.")
    parser.add_argument("--keys", type=str, metavar="FILENAME", help="Print schema keys of a json file in data/ (e.g. jobs_state.json).")
    parser.add_argument("--job", type=str, metavar="ID_OR_URL", help="Inspect a single job by its ID or URL.")
    
    args = parser.parse_args()
    if args.summary:
        show_summary()
    elif args.keys:
        show_keys(args.keys)
    elif args.job:
        show_single_job(args.job)
    else:
        show_summary()

if __name__ == "__main__":
    main()
