---
name: resilient-automation-patterns
description: "Ensures unattended automations (cron jobs, scrapers, GeminiPool LLM calls, Tavily/Firecrawl extraction, and Supabase cloud sync) in job_search_automation are fault-tolerant, credit-safe, observable, and idempotent."
---

# Resilient Automation Patterns (`job_search_automation`)

Make every unattended run (`main.py`, `src/pipeline.py`, `.github/workflows/daily_job_search.yml`) **observable, credit-safe, recoverable, and idempotent**. Assume every external dependency (LinkedIn, Drushim, Comeet, Gemini API, Tavily, Firecrawl, Supabase, SMTP) will eventually fail or rate-limit.

## 1. Multi-Model Gemini Fallback Pool (`src/gemini_runtime.py`)
- **Ordered Model Rotation (`GeminiPool`):** Execute structured evaluations using the configured fallback chain:
  `gemini-3.8-flash` -> `gemini-3.5-flash-lite` -> `gemini-3.5-flash`.
- **Quota & Rate-Limit Recovery (`429 / 503`):** On transient API errors or quota exhaustion on the primary model, rotate immediately to the next model in the pool with exponential backoff (`base * 2**(attempt-1) + jitter`, max 3 attempts).
- **Safe Degradation (`RETRY_PENDING`):** If all models in `GeminiPool` fail or a job listing lacks usable description text, persist the job as `RETRY_PENDING` in `data/evaluation_state.json` for `scripts/requeue_jobs.py`. Never assign a fabricated LLM score or silently drop a valid candidate job.

## 2. Three-Tier Scraper & MCP Credit Protection (`src/fetchers.py`, `src/ats_client.py` & MCP Policy)
- **Tier 1 — Fast Static Fetchers, Direct ATS APIs & `Tavily` Discovery:** Use native Python fetchers (`src/fetchers.py`, `src/ats_client.py` for Comeet, Greenhouse, Lever, Ashby) and `Tavily` MCP for initial job discovery and domain verification.
- **Tier 1.5 — `api-anything` MCP (API-First Extraction & Delta Polling):** Use `api-anything` (`call_operation`, `call_batch`, `learn_site`) to inspect, learn, and poll external career sites via HTTP/JSON (`changes: true` / `changesOnly: true`) before spending Firecrawl credits or launching a browser. Respect `retryAfterMs` on `rate` responses.
- **Tier 2 — Surgical `Firecrawl` Extraction:** Invoke `Firecrawl` MCP **only** when Tier 1/1.5 fails or a specific job URL requires heavy JS/SPA rendering. Never run bulk/broad crawling on `Firecrawl` to prevent credit exhaustion.
- **Per-Source Circuit Breaker:** Track consecutive failures per source via `CircuitBreaker` (`src/fetchers.py`, `main.py`). After 3 consecutive failures, open the circuit for that source (`[CIRCUIT OPEN] <source>`), log the degradation, and continue the pipeline with remaining healthy sources.

## 3. Idempotency & Bi-Directional State Protection
Running the pipeline twice must produce identical state without data loss:
- **Deterministic Job Keys:** Deduplicate via canonical URL (`src/url_utils.py`) and normalized `(company, title, location)` in `src/state_manager.py`.
- **User Triage Protection (`localStorage` + Supabase `public.sync_state`):** Pipeline runs and UI builds (`src/ui_builder.py`) must never overwrite or purge user triage actions (`starred`, `saved`, `rejected`, `purged`).
- **Supabase Sync Resilience:** Client-side and sync adapters must handle offline/timeout states gracefully via optimistic local writes and retry on `visibilitychange` / `focus` without blocking UI rendering.
- **Email & Git Idempotency:** Check last-dispatched run markers before sending SMTP alerts (max 2 retries; never auto-resend on ambiguous timeout). In GitHub Actions, verify `git diff --staged --quiet` before committing.

## 4. Observability, Dead-Man's Switch & Pre-Deploy Checklist
- **Distinguish Empty vs. Broken:** Log `[INFO] Run completed - no new data to process` (`SUCCESS_EMPTY_RUN`) when fetchers succeed with 0 new matches, versus explicit failure alerts when scrapers or APIs fail.
- **Structured Error Context:** Every error log must include `[ERROR] <module>.<func> | Attempt X/Y | <ErrorType>: <context>`. Zero bare `except: pass` blocks.
- **Zero Emojis:** Strictly zero emojis in logs, step summaries (`GITHUB_STEP_SUMMARY`), email alerts, and dashboard banners.
