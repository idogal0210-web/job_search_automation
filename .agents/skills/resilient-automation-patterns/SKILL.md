---
name: resilient-automation-patterns
description: Ensures unattended automations (cron jobs, scrapers, scheduled pipelines) in job_search_automation are fault-tolerant, observable and safe to re-run. Covers retry with backoff, fallbacks, idempotency, circuit breakers, failure alerting and structured error context. Use when building, reviewing or debugging the daily job-search run, scrapers (LinkedIn, Drushim, Comeet), email dispatch or any unsupervised automation.
---

# Resilient Automation Patterns

Make every unattended automation **observable, recoverable and safe to re-run**. A silent failure is worse than a loud one. Assume every external call (LinkedIn, Drushim, Comeet, Gemini, SMTP) will fail eventually.

## 1. Retry with exponential backoff
- Never retry immediately or infinitely. Use `delay = min(base * 2**(attempt-1), max)` plus ~25% jitter.
- **Max 3 attempts** for API and scraping calls. **Max 2** for SMTP sends. **Never retry** a side-effecting operation (email, DB write, webhook) unless it is idempotent. After an ambiguous email result, stop and report, never auto-resend.
- Log each retry: attempt number, error type, delay, context.

## 2. Fallback chains
Primary failed: try an alternative source, then cached data (mark `stale`), then partial data (mark `partial`). If nothing is available, fail loudly, alert and produce no output.
- Log what failed, what replaced it and whether quality degraded.
- Never substitute empty strings, zeros or placeholders for real data.
- A job without a usable description stays `RETRY_PENDING`; it is never silently scored.

## 3. Idempotency
Running twice must equal running once.
- **Email:** check a last-sent marker (run ID, date or hash) before sending.
- **Persistence:** upsert or check-before-write with deterministic job IDs. Never append to archives without deduplication, and never let a new run overwrite user actions (archive, star, delete) in `data/`.
- **Git:** check `git diff --quiet` first; never create empty commits.

## 4. Circuit breaker
Track failures per external service. At 3 consecutive failures open the circuit and skip that service for a cooldown (e.g. 10 minutes), then allow one probe call. Log `[CIRCUIT OPEN] <service>`. One broken source must not fail a run that can still produce partial results.

## 5. Failure alerting (dead man's switch)
- **Success:** one-line summary.
- **Failure:** full error details plus an alert (GitHub Actions: visible failed run; local: failure log and a separate failure email).
- **Nothing found:** log explicitly `[INFO] Run completed - no new data to process`, to distinguish "nothing to do" from "silently broken". Final status values such as `SUCCESS_EMPTY_RUN` or `FAILED_DASHBOARD` must reflect reality.

## 6. Structured error context
Every error line answers: what failed, where, which attempt, what input, what happens next. Example: `[ERROR] scraper.py > fetch_comeet(url) | Attempt 2/3 | TimeoutError: ...`. No bare `except: pass`.

## 7. Graceful degradation

| Situation | Action |
| :--- | :--- |
| All sources succeeded | Normal output |
| Some fallbacks used | Output with a visible degradation banner |
| Critical source failed | Do not send a broken or empty report; log, alert, skip the run |
| Infrastructure failure (SMTP, Git) | Retry once, then save output locally and alert |

## Pre-deploy checklist
- [ ] External calls have retry plus backoff (max 3).
- [ ] Each data source has a documented fallback or explicit failure path.
- [ ] A second run produces identical observable results.
- [ ] Failures carry structured context and trigger alerts; success is one line.
- [ ] "Nothing happened" is distinguishable from "silently broken".
- [ ] Partial results are clearly marked as partial.
