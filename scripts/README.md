# Scripts & Maintenance Utilities

This directory contains standalone operational, maintenance, and verification scripts for the job search automation repository.

## Operational & Maintenance Scripts

- **`inspect_state.py`**: Non-invasive CLI inspector for workspace JSON datasets (`jobs_state.json`, `sync_state.json`, `evaluation_state.json`, etc.). Allows inspecting record counts, categories, and specific job records without loading full datasets into memory.
- **`project_hygiene.py`**: Deterministic cleanup and hygiene runner driven by `.save-and-sync.yml`. Cleans ephemeral `.tmp`, `.bak`, `.DS_Store` files and verifies project state.
- **`validate_zero_emoji.py`**: Quality floor verification gate that ensures zero pictorial emoji characters across code, templates, and documentation.
- **`requeue_jobs.py`**: Resets specific job links from `COMPLETE` or failed state back to `RETRY_PENDING` in the evaluation ledger to allow re-evaluation.
- **`backfill_company_logos.py`**: Maintenance utility to scan existing job records and backfill missing company logos using Google Favicon / Clearbit APIs.
- **`scan_inactive_jobs.py`**: Offline scanner that checks HTTP statuses of cataloged job links, identifying expired or closed listings and recording them in `data/inactive_jobs.json`.
- **`update_job_gaps_and_reasoning.py`**: One-off maintenance script used during model migrations to populate Hebrew fit gaps and concise reasoning fields for historical records.
- **`evaluate_dataset.py`**: Benchmark dataset evaluator used for prompt regression testing, scoring calibration, and precision measurement.

## External Tools & Workers

- **`tools/cloudflare-worker/job-check.js`**: Standalone Cloudflare Worker script for edge-based job URL validation and status verification.
