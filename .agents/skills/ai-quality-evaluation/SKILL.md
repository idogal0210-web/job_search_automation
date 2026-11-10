---
name: ai-quality-evaluation
description: "Systematically verify that software and AI agents behave correctly, reliably, and consistently. Applied to job_search_automation for evaluating Gemini job scoring, prompt regression testing, and output accuracy."
---

# AI Quality & Evaluation Engineer (`job_search_automation`)

## 1. Mission
Systematically verify that the `job_search_automation` pipeline, Gemini LLM evaluators, salary engine, and Career Studio AI behave accurately, deterministically, and without regressions. Replace subjective confidence with measurable evidence.

## 2. Activate When
- Modifying prompts (`prompts/job_evaluation_v1.txt`, `prompts/cv_analysis_v1.txt`, `prompts/cv_generation_v1.txt`) or LLM orchestration (`src/gemini_runtime.py`, `src/evaluators.py`).
- Upgrading Gemini model IDs (`gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`) or Pydantic response schemas.
- Updating deterministic filtering rules in `src/job_policy.py` or `search-preferences.json`.
- Introducing or modifying scrapers in `src/fetchers.py` or Career Studio bridge endpoints (`scripts/studio_bridge.py`).
- Investigating false positives (irrelevant/blacklisted jobs passing) or false negatives (high-fit energy/UAV roles rejected).

## 3. Canonical Architecture & Aligned Thresholds
Always evaluate against the active codebase and unified policy:
- **Pipeline & Evaluators:** `main.py`, `src/pipeline.py`, `src/job_policy.py`, `src/evaluators.py`, `src/gemini_runtime.py`, `src/salary_engine.py`, `src/state_manager.py`.
- **Benchmark & Evaluation Scripts:**
  - `scripts/evaluate_dataset.py` (calculates Confusion Matrix, Precision, Recall, F1, and False Negatives against `data/evaluation_benchmark_template.json`).
  - `scripts/requeue_jobs.py` (re-evaluates `RETRY_PENDING` or cached jobs).
  - `scripts/project_hygiene.py --validate` (validates syntax, JSON schemas, and repo hygiene).
- **Aligned Quality Thresholds (Synchronized with `job-search-automation-state`):**
  - **Energy / Gas / Solar PV / BESS / SCADA:** Pass threshold **`60+`** (with >= 3 distinct evidenced matches).
  - **UAV / Drone / Defence:** Pass threshold **`70+`** (with >= 3 distinct evidenced matches).
  - **Hard Blacklist (`Energean`, `INGL`, `Chevron`) & Excluded Roles:** Score must deterministically equal **`0`** (`DISQUALIFIED`).
  - **Control Room / NOC Rule:** Disqualified unless industrial SCADA/telemetry is explicit AND (advertised salary >= 20,000 ILS or Tier-1 enterprise employer). Advertised salary < 15,000 ILS = `0`.

## 4. Execution Workflow

### Step 1 — Define Quality Dimensions
1. **Deterministic Gate Accuracy:** 100% block rate on blacklisted employers, excluded non-technical roles, and sub-15,000 ILS roles before or during evaluation.
2. **Schema & Pydantic Compliance:** Every Gemini response must validate cleanly against its Pydantic contract without hallucinated fields or missing rationale.
3. **Evidence Grounding:** Match scores and requirement assessments must cite concrete phrases from the job description (e.g., practical engineer flexibility vs. rigid B.Sc requirement).
4. **State & Retry Resilience:** Rate limits (`429`) or empty descriptions transition cleanly to `RETRY_PENDING` in `data/evaluation_state.json` without corrupting `data/jobs_state.json` or `docs/data/jobs.json`.

### Step 2 — Run Automated Verification Suite
Execute the project's test suites before approving any change:
```bash
python3 scripts/project_hygiene.py --validate
python3 -m unittest discover -s tests -p "test_*.py"
```
When evaluating scoring precision or prompt updates, run:
```bash
python3 scripts/evaluate_dataset.py
```
When testing UI/Studio milestones, also run the Node.js stress harnesses if applicable (`node tests/stress_m1_harness.js`, `node tests/stress_m2_harness.js`).

### Step 3 — Failure & Regression Analysis
For any test failure or misclassified job:
1. Inspect exact input fixture, prompt version (`prompts/*.txt`), and raw Pydantic/JSON output.
2. Classify root cause: deterministic policy regex gap (`src/job_policy.py`), prompt instruction ambiguity (`prompts/`), or model fallback degradation.
3. Apply targeted fix and re-run the full unit test suite + benchmark dataset to verify zero regressions.

## 5. Guardrails
- Never fabricate test execution or benchmark metrics.
- Never modify production state files (`data/jobs_state.json`, `docs/data/jobs.json`) during test runs; use isolated fixtures or `tempfile`.
- Never weaken hard exclusions to artificially inflate recall.
- Strictly zero emojis in all test code, logs, and evaluation reports.
