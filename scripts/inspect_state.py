#!/usr/bin/env python3
"""
Lightweight CLI inspection tool for workspace state and data files.
Provides concise counts, schema keys, and sync parity without dumping full datasets.
Zero emojis strictly enforced.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def get_json_data(filename: str) -> Any:
    path = DATA_DIR / filename
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}


def _infer_tier_for_job(job: Dict[str, Any]) -> str:
    if not isinstance(job, dict):
        return "unclassified"
    if job.get("tier"):
        return str(job["tier"])
    bonus = int(job.get("priority_bonus") or 0)
    if bonus >= 10:
        return "tier1"
    if bonus >= 5:
        return "tier2"
    if job.get("is_target_company"):
        return "target"
    return "standard"


def show_summary() -> None:
    jobs_state = get_json_data("jobs_state.json")
    sync_data = get_json_data("sync_state.json")
    historical = get_json_data("historical_catalog.json")
    inactive = get_json_data("inactive_jobs.json")
    evaluation = get_json_data("evaluation_state.json")

    catalog_map = historical if isinstance(historical, dict) else {}
    eval_jobs = evaluation.get("jobs", {}) if isinstance(evaluation, dict) and isinstance(evaluation.get("jobs"), dict) else {}

    print("=== WORKSPACE DATA SUMMARY ===")

    # 1. jobs_state.json (canonical list of seen URL strings)
    if isinstance(jobs_state, list):
        print(f"data/jobs_state.json total seen URLs: {len(jobs_state)}")
        tiers: Dict[str, int] = {}
        for item in jobs_state:
            if isinstance(item, dict):
                t = _infer_tier_for_job(item)
            elif isinstance(item, str):
                job_obj = catalog_map.get(item)
                if not isinstance(job_obj, dict) and item in eval_jobs:
                    entry = eval_jobs.get(item)
                    job_obj = entry.get("job") if isinstance(entry, dict) else None
                t = _infer_tier_for_job(job_obj) if isinstance(job_obj, dict) else "unindexed_url"
            else:
                t = "unknown"
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
        cat_tiers: Dict[str, int] = {}
        for j in historical.values():
            if isinstance(j, dict):
                t = _infer_tier_for_job(j)
                cat_tiers[t] = cat_tiers.get(t, 0) + 1
        if cat_tiers:
            print(f"  Catalog tier breakdown: {cat_tiers}")

    # 4. inactive_jobs.json
    if isinstance(inactive, dict):
        total_scanned = inactive.get("total_scanned", "N/A")
        inactive_count = inactive.get("inactive_count", "N/A")
        unknown_count = inactive.get("unknown_count", 0)
        print(f"data/inactive_jobs.json inactive/scanned: {inactive_count}/{total_scanned} (unknown: {unknown_count})")

    # 5. evaluation_state.json
    if eval_jobs:
        print(f"data/evaluation_state.json evaluated jobs: {len(eval_jobs)}")


def show_keys(filename: str) -> None:
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
            print(f"List of {len(data)} elements of type: {type(sample).__name__}")
    elif isinstance(data, dict):
        first_val = next(iter(data.values())) if len(data) > 0 else None
        if isinstance(first_val, dict) and filename == "historical_catalog.json":
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


def show_single_job(query_str: str) -> None:
    query = str(query_str).strip()
    historical = get_json_data("historical_catalog.json")
    if isinstance(historical, dict):
        if query in historical:
            print(f"=== JOB RECORD FROM CATALOG: {query} ===")
            print(json.dumps(historical[query], indent=2, ensure_ascii=False))
            return
        for url, job in historical.items():
            if isinstance(job, dict):
                if query in url or query.lower() in job.get("title", "").lower() or query.lower() in job.get("company", "").lower():
                    print(f"=== JOB RECORD MATCH ({job.get('company')} - {job.get('title')}): {url} ===")
                    print(json.dumps(job, indent=2, ensure_ascii=False))
                    return

    evaluation = get_json_data("evaluation_state.json")
    if isinstance(evaluation, dict) and "jobs" in evaluation:
        jobs = evaluation["jobs"]
        if isinstance(jobs, dict) and query in jobs:
            print(f"=== EVALUATION RECORD: {query} ===")
            print(json.dumps(jobs[query], indent=2, ensure_ascii=False))
            return

    print(f"Job matching '{query}' not found in catalog or state.")


def main() -> None:
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
