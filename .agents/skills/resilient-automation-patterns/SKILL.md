---
name: resilient-automation-patterns
description: "Ensures unattended automations (cron jobs, scrapers, GeminiPool LLM calls, Parallel/Tavily/Firecrawl extraction, inactive job scanner, loopback Studio Bridge, and versioned Supabase CAS cloud sync) in job_search_automation are fault-tolerant, credit-safe, SSRF-protected, observable, and idempotent."
---

# Resilient Automation Patterns (`job_search_automation`)

Make every unattended run (`main.py`, `src/pipeline.py`, `scripts/scan_inactive_jobs.py`, `.github/workflows/daily_job_search.yml`) **observable, credit-safe, recoverable, and idempotent**. Assume every external dependency (LinkedIn, Drushim, Comeet, Greenhouse, Lever, Gemini API, Parallel, Tavily, Firecrawl, Supabase, SMTP) will eventually fail or rate-limit.

## 1. Multi-Model Gemini Fallback Pool (`src/gemini_runtime.py`)
- **Ordered Model Rotation (`GeminiPool`):** Execute structured evaluations using the configured fallback chain:
  `gemini-3.8-flash` -> `gemini-3.5-flash-lite` -> `gemini-3.5-flash`.
- **Quota & Rate-Limit Recovery (`429 / 503`):** On transient API errors or quota exhaustion on the primary model, rotate immediately to the next model in the pool with exponential backoff (`base * 2**(attempt-1) + jitter`, max 3 attempts).
- **Safe Degradation (`RETRY_PENDING`):** If all models in `GeminiPool` fail or a job listing lacks usable description text, persist the job as `RETRY_PENDING` in `data/evaluation_state.json` for `scripts/requeue_jobs.py`. Never assign a fabricated LLM score or silently drop a valid candidate job.

## 2. Three-Tier Scraper & MCP Credit Protection (`src/fetchers.py`, `src/ats_client.py` & MCP Policy)
- **Tier 1 — Fast Static Fetchers, Direct ATS APIs & `Tavily` Discovery:** Use native Python fetchers (`src/fetchers.py` including 15 batched OR queries across 75 target companies on LinkedIn, Drushim, and `src/ats_client.py` for Comeet, Greenhouse, Lever, Ashby) and `Tavily` MCP for initial job discovery and domain verification.
- **Tier 1.5 — `Parallel` MCP (Free Web Search & Fetch):** Prefer `parallel_parallel-search` (`web_search`, `web_fetch`) for free live web discovery and page fetching before spending `Tavily` or `Firecrawl` credits.
- **Tier 2 — Surgical `Firecrawl` Extraction:** Invoke `Firecrawl` MCP **only** when Tier 1/1.5 fails or a specific job URL requires heavy JS/SPA rendering. Never run bulk/broad crawling on `Firecrawl` to prevent credit exhaustion.
- **Per-Source Circuit Breaker:** Track consecutive failures per source via `CircuitBreaker` (`src/fetchers.py`, `main.py`). After 3 consecutive failures, open the circuit for that source (`[CIRCUIT OPEN] <source>`), log the degradation, and continue the pipeline with remaining healthy sources.

## 3. Idempotency, Atomic Outbox & Versioned Supabase CAS Sync
Running the pipeline or client sync twice must produce identical state without data loss or duplicate notifications:
- **Deterministic Job Keys:** Deduplicate via canonical URL, `stable_job_id` (`li_`, `comeet_`, `dr_`, `gh_`, `lever_`, `ashby_`), and normalized `content_job_hash` (`ch_<sha256[:12]>`) in `src/url_utils.py` and `src/state_manager.py`.
- **Version-Aware Supabase CAS Protection (`localStorage` + `public.sync_state`):** Pipeline runs and UI builds (`src/ui_builder.py`) must never overwrite user triage actions (`starred`, `saved`, `rejected`, `purged`). Client sync uses authenticated conditional `PATCH` (`compareAndSwap` with `version` column and conflict merge), tracks `ido_job_last_cloud_version` (`isNewRemoteVersion`), and performs bidirectional `purged` reconciliation so remote restores automatically prune stale local `purged` states.
- **Atomic Email Outbox (`email_outbox.json`):** Persist pending email payloads to an atomic outbox before SMTP dispatch in `main.py` so post-send state crashes never trigger duplicate daily emails. Unify `final_status` across `dispatch_notifications` and `report_results`. In GitHub Actions, verify `git diff --staged --quiet` before committing.
- **Native Runtime Normalization:** Perform salary range ordering (`normalizeSalaryRange`) and location deduplication (`normalizeJobLocation`) deterministically at render time in `dashboard.js` without global `MutationObserver` loops (`ui-fixes.js` is permanently retired).

## 4. Security, SSRF Guards & Inactive Job Detection
- **SSRF & Peer IP Guard (`src/url_guard.py`):** Validate every external URL fetched by `tools/cv_tailor/src/scraper.py` or `scripts/studio_bridge.py` against `is_global` IP checks on both literal and DNS paths, re-validate every HTTP redirect hop, and verify the connected socket peer IP.
- **Loopback Studio Bridge Hardening (`scripts/studio_bridge.py`):** Enforce loopback `Host` validation, `is_allowed_origin` on `POST`, per-process `X-Studio-Token` (`/api/session` with `hmac.compare_digest`), `Content-Type: application/json`, and `Content-Length` in `[0, 1MiB]`.
- **Two-Signal Inactive Job Scanner (`scripts/scan_inactive_jobs.py` & `src/closure_signatures.json`):** Strip non-content tags (`<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, `<template>`) and related-job sidebars, check primary JSON-LD `JobPosting.validThrough`, and require 2 independent closure signals on non-ATS pages to prevent false-positive closures.

## 5. Observability & Pre-Deploy Checklist
- **Distinguish Empty vs. Broken:** Log `SUCCESS_EMPTY_RUN` when fetchers succeed with 0 new matches, versus explicit failure statuses (`DEGRADED_NETWORK`, `FAILED_SCRAPERS`) and `is_incomplete_run` guards (`src/publishers.py`). Record `gate_rejection_rate`, `estimated_gemini_cost_usd`, and `unknown_scan_rate`.
- **Structured Error Context:** Every error log must include `[ERROR] <module>.<func> | Attempt X/Y | <ErrorType>: <context>`. Zero bare `except: pass` blocks.
- **Zero Emojis:** Strictly zero emojis in logs, step summaries (`GITHUB_STEP_SUMMARY`), email alerts, and dashboard banners.
