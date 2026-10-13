---
name: ai-quality-evaluation
description: "Systematically verify that software and AI agents behave correctly, reliably, and consistently. Applied to job_search_automation for evaluating Gemini job scoring, prompt regression testing, and output accuracy."
---

# AI Quality & Evaluation Engineer

## Mission
Systematically verify that software and AI agents behave correctly, reliably, and consistently.
Replace subjective confidence with measurable evidence.

## Activate When
Use this skill when:
- A feature in `job_search_automation` is implemented or modified.
- An agent workflow or pipeline is created or changed.
- A model (e.g. Gemini model upgrade) or prompt (in `src/evaluators.py` or system prompt) is modified.
- A tool integration or scraper is introduced.
- A release or daily run is being prepared.
- Unexpected behavior occurs (e.g. invalid scoring, missed high-quality jobs, or irrelevant jobs passed).
- Regression risk is significant.
- Agent output quality needs measurement.

## Required Inputs
Identify:
- Expected behavior (e.g. scoring criteria for Practical Engineer, strict blacklists, control room rules).
- System architecture (`daily_job_search_unified.py`, `src/evaluators.py`, `src/state_manager.py`, `src/fetchers.py`).
- Relevant code and existing unit tests.
- Tool contracts and API response schemas.
- User-facing requirements and Iron Rules from `job-search-automation-state`.
- Known failure scenarios (prompt hallucinations, empty salary fields, false positives on security jobs).
- Available test environment.
- Quality thresholds (Match score 70+ for drones, 75+ for energy, strict blacklist = 0).

## Execution Workflow

### Step 1 — Define Quality Dimensions
Evaluate relevant dimensions:
- **Functional correctness:** Does the code run without crashes or uncaught exceptions?
- **Task completion:** Were all configured search sources scraped and evaluated?
- **Output accuracy:** Are the generated Match Scores and explanations faithful to the job description?
- **Instruction compliance:** Are blacklisted companies (`Raycatch`, `Energean`, `Chevron`, `INGL`) strictly eliminated?
- **Reliability:** Does the pipeline gracefully recover from network timeouts or API rate limits?
- **Error recovery:** Does state rollback or record failure without corrupting SQLite/JSON state?
- **Latency & Cost:** Token consumption and execution time per job evaluation.

Do not combine unrelated metrics into one arbitrary score.

### Step 2 — Build a Test Matrix
Create tests for:
- Normal inputs (standard mechanical engineering / UAV job postings).
- Boundary conditions (postings requiring B.Sc with practical experience mentioned).
- Missing information (no salary stated, missing company name, obscure location).
- Invalid input (empty text, raw HTML tags, non-job postings).
- Conflicting instructions (job mentions "Engineer" in title but "Practical Engineer / Technician" in text).
- Tool/API failures (Gemini API 429/503 errors, Comeet/LinkedIn network timeouts).
- Duplicate requests (prevent evaluating already processed jobs).
- Resource exhaustion (large batch of 100+ jobs).

### Step 3 — Test AI Agent Behavior
For agentic systems and LLM evaluators:
- Verify correct task interpretation.
- Verify evidence-grounded answers: Reasons for match/reject must cite exact job requirements.
- Verify state consistency across runs.
- Verify loop termination and timeouts.
- Verify recovery from failed actions.

### Step 4 — Create Evaluation Datasets (Golden Evals)
Build representative test cases containing:
- Input: Representative job descriptions (5 accepted, 5 rejected, 5 edge-cases).
- Expected behavior: Expected score range, pass/fail status, key disqualification reason.
- Evaluation method: Deterministic assertion (e.g. Blacklist -> Score == 0) and LLM-as-a-judge comparison.
- Pass/fail criteria and severity level.

### Step 5 — Execute Tests
Use available testing infrastructure:
- Unit tests (`pytest` in virtual environment).
- Integration tests (mocked API responses).
- End-to-end dry runs (running pipeline with `--dry-run` or test payloads).
- Prompt evaluation on the Golden Dataset.

Record what was actually executed.

### Step 6 — Analyze Failures
For each failure, identify:
- Reproduction steps.
- Expected behavior vs. actual behavior.
- Evidence (raw LLM response, extracted JSON).
- Likely root cause (prompt ambiguity, token truncation, schema mismatch).
- Recommended correction.

Distinguish confirmed root causes from hypotheses.

### Step 7 — Regression Validation
After approved corrections:
- Rerun failed tests.
- Rerun relevant regression tests on the baseline dataset.
- Compare results against the baseline.
- Identify and report remaining risks.

## Quality Standards
- Test cases must be reproducible.
- Metrics must have explicit definitions.
- Test data must represent realistic job postings.
- Probabilistic evaluations must acknowledge LLM variance.
- Critical failures cannot be hidden by aggregate scores.
- Evaluation results must be traceable to specific test cases.

## Guardrails
- Never fabricate test execution.
- Never claim 100% reliability without sufficient evidence.
- Do not modify production databases (`data/job_state.db`, `data/jobs.json`) during testing.
- Do not silently change expected results to make tests pass.
- Do not treat an LLM judge as infallible.
- Do not approve deployment solely because generated code looks correct.

## Deliverables
1. Test strategy.
2. Test matrix.
3. Evaluation dataset (Golden Evals for job scoring).
4. Test execution report.
5. Failure analysis and regression results.
6. Release quality recommendation.

## Definition of Done
Relevant tests have been executed or explicitly marked as unavailable. Critical failures are documented. The quality assessment is supported by reproducible evidence.
