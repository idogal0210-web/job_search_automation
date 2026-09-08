---
name: resilient-automation-patterns
description: Ensures unattended automations (cron jobs, scrapers, scheduled pipelines) are fault-tolerant, observable, and self-healing. Covers retry with backoff, fallback chains, idempotency, circuit breakers, dead-man's-switch alerting, and structured failure reporting. Use when building, reviewing, or debugging any automation that runs without human supervision.
---

# Resilient Automation Patterns

Make every unattended automation **observable, recoverable, and safe to
re-run**. An automation that fails silently is worse than one that fails
loudly — it creates a false sense of reliability.

## Core Principle

**Assume every external call will fail eventually.** APIs return 500s, rate
limits trigger, HTML structures change, SMTP servers reject connections, and
DNS resolves to nothing. The question is never *if* but *when* — and whether
the system degrades gracefully or crashes silently.

---

## 1. Retry with Exponential Backoff

Never retry immediately or infinitely.

```python
# Pattern: retry with exponential backoff and jitter
import time, random

def retry(fn, max_attempts=3, base_delay=2.0, max_delay=60.0):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            if attempt == max_attempts:
                raise
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            delay += random.uniform(0, delay * 0.25)  # jitter
            print(f"[RETRY] Attempt {attempt}/{max_attempts} failed: {e}. "
                  f"Retrying in {delay:.1f}s...")
            time.sleep(delay)
```

Rules:
- **Max 3 attempts** for API calls (FMP, Gemini, Google Search).
- **Max 2 attempts** for SMTP sends (avoid duplicate emails).
- **Never retry** destructive or side-effecting operations (email sends,
  database writes, webhook dispatches) unless the operation is idempotent.
- Log every retry with: attempt number, error type, delay, and context.

---

## 2. Fallback Chains

When the primary source fails, degrade to the next best alternative —
never return empty data without explicit signaling.

```
Primary source failed?
├─ Alternative source available?  → try it, log the fallback
├─ Cached/stale data available?   → use it, mark output as "stale"
├─ Partial data available?        → use it, mark output as "partial"
└─ Nothing available?             → fail loudly, alert, do NOT produce output
```

Rules:
- Every fallback must be logged with: what failed, what was used instead,
  and whether the output quality is degraded.
- Never silently substitute empty strings, zero values, or placeholder text
  for real data. The consumer must know the data is missing.
- Document fallback chains in code comments so maintainers understand the
  degradation path.

---

## 3. Idempotency (Safe Re-runs)

Re-running the same automation twice must produce the same observable result
as running it once. This is non-negotiable for cron jobs.

Rules:
- **Email sends:** Check a "last sent" marker (timestamp, run ID, or hash)
  before sending. If the marker matches, skip the send.
- **Data persistence:** Use upsert semantics or check-before-write. Never
  append blindly to archives without deduplication.
- **Git commits:** Check `git diff --quiet` before committing. Never create
  empty commits.
- **File generation:** Overwrite deterministically or use content hashing to
  detect "nothing changed" before writing.

---

## 4. Circuit Breaker

When an external service fails repeatedly, stop calling it to avoid wasting
quota and time. Resume only after a cooldown period.

```
Call failed?
├─ Failure count < threshold (e.g. 3)?  → retry normally
├─ Failure count >= threshold?          → OPEN circuit, skip calls for N minutes
└─ Cooldown elapsed?                    → try ONE probe call (half-open)
    ├─ Probe succeeds?                  → CLOSE circuit, resume normal
    └─ Probe fails?                     → keep circuit OPEN, extend cooldown
```

Rules:
- Track failure counts per external service, not globally.
- When a circuit opens, log it clearly: `[CIRCUIT OPEN] FMP API — 3
  consecutive failures. Skipping for 10 minutes.`
- Never let a broken external service cascade into a full automation failure
  if the automation can produce partial results without it.

---

## 5. Dead Man's Switch (Failure Alerting)

An automation that fails silently is invisible. The user must know when
something did NOT happen.

Rules:
- **On success:** emit a minimal summary (one line or a short structured log).
- **On failure:** emit full error details AND trigger an alert channel:
  - GitHub Actions: the workflow already fails visibly in the Actions tab.
  - Local cron: write to a failure log file AND send a failure notification
    email (separate from the report email).
- **On "nothing happened":** if the automation ran but produced zero results
  (no jobs found, no market data, no changes), log it explicitly:
  `[INFO] Run completed — no new data to process.`
  This distinguishes "nothing to do" from "silently broken".
- Consider a heartbeat: if the daily report has not been sent by 09:00
  Israel time, something is wrong.

---

## 6. Structured Error Context

When logging or raising errors, always include actionable context:

```python
# Bad: bare exception
except Exception as e:
    print(f"Error: {e}")

# Good: structured, actionable context
except Exception as e:
    print(f"[ERROR] fetch_data.py > _fetch_yf('{ticker}') | "
          f"Attempt {attempt}/{max_attempts} | "
          f"{type(e).__name__}: {e}")
```

Every error log line must answer: **What failed? Where? Which attempt?
What was the input? What should happen next?**

---

## 7. Graceful Degradation Hierarchy

When building the final output (report, email, summary), follow this
hierarchy:

| Data Quality | Action |
| --- | --- |
| All sources succeeded | Produce full output, send normally |
| Some sources failed, fallbacks used | Produce output with degradation banner: "⚠️ חלק מהנתונים מבוססים על מקור חלופי" |
| Critical sources failed | Do NOT send a broken/empty report. Log failure, alert, skip this run |
| Infrastructure failure (SMTP, Git) | Retry once, then save output locally and alert |

---

## Anti-Patterns

| Dangerous | Instead |
| --- | --- |
| `except: pass` (swallowing errors) | Log, count, and re-raise after max retries |
| Infinite retry loops | Max 3 attempts with backoff, then fail loudly |
| Sending empty/broken reports | Skip the send, alert, save locally |
| No deduplication on re-run | Check markers before side effects |
| Same error message for all failures | Structured context: what, where, attempt, input |
| Assuming "it ran" means "it worked" | Verify output content, not just exit code |
| Silent cron failure | Dead man's switch + failure alerting |

---

## Checklist Before Deploying Any Automation

- [ ] Every external call has retry + backoff (max 3 attempts).
- [ ] Every data source has a documented fallback or explicit failure path.
- [ ] Re-running twice produces identical observable results (idempotent).
- [ ] Failures are logged with structured context and trigger alerts.
- [ ] Success is logged minimally (one line, not a wall of text).
- [ ] "Nothing happened" is distinguishable from "silently broken".
- [ ] No `except: pass` or bare `except Exception` without logging.
- [ ] Partial results are clearly marked as partial in the output.
