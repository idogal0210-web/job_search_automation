---
name: task-lifecycle-manager
description: "Manages the project task lifecycle, PRD requirement traceability (docs/PRD.md REQ-01..15), roadmap, and milestone verification for job_search_automation. Tracks tasks in TASKS.md through distinct phases: Backlog, In Progress, Blocked, and Verified Done. Prevents phantom progress and requires concrete tests/evidence before marking tasks as complete. Strictly zero emojis."
---

# Task Lifecycle Manager — job_search_automation

Manages the lifecycle of project tasks, engineering backlog, and sprint milestones. Ensures all agent actions map directly to numbered requirements in [`docs/PRD.md`](file:///Users/ido/.gemini/antigravity/scratch/job_search_automation/docs/PRD.md) (`prd-build-protocol`) and prevents false completion claims.

## 1. Operating Rules & Principles
- **Single Source of Truth & PRD Traceability**:
  - All tasks, bugs, and feature implementations are tracked in `TASKS.md` at the project root.
  - Every engineering task must trace to a numbered requirement (`REQ-01` through `REQ-15`) in `docs/PRD.md` or an approved decision record in `docs/decisions/`.
  - Before writing code, apply `replaceability-test` (single source of truth and modular isolation across scrapers, persistence, and UI).
- **Evidence-Based Completion**: A task can ONLY be marked as `[x]` (Done) if accompanied by concrete verification evidence:
  - Dual-template parity check (`python3 tests/test_template_docs_sync.py`).
  - Zero-emoji and secret/hygiene audit (`python3 scripts/validate_zero_emoji.py && python3 scripts/project_hygiene.py --check-secrets --validate`).
  - Full unit test suite execution (`python3 -m unittest discover -s tests -p "test_*.py"`) and JS syntax check (`node -c frontend/js/dashboard.js docs/dashboard.js`).
  - Living documentation synchronization (`TASKS.md`, `PROJECT_CONTEXT.md`, and `docs/PRD.md` / `README.md` when architecture or features change).
- **Strictly Zero Emojis**: Never use emojis or Unicode Dingbats (`U+2700..U+27BF`) in `TASKS.md`, commit messages, task summaries, or status tags (`zero-emojis.md`).
- **Bounded Scope**: Never invent tasks or features outside user instructions. Keep tasks atomic, testable, and actionable.

## 2. Task Lifecycle States
Every item in `TASKS.md` resides in one of four states:
1. `[BACKLOG]`: Planned tasks awaiting implementation.
2. `[IN_PROGRESS]`: Currently active task being executed in the current session.
3. `[BLOCKED]`: Task waiting on external dependency, API key, or explicit user decision.
4. `[DONE]`: Verified complete with target files list, numbered evidence breakdown, test count, and completion date.

## 3. Workflow Steps

### Step 1: Load Context & Trace Requirements
When invoked:
- Read `TASKS.md`, `PROJECT_CONTEXT.md`, and relevant sections of `docs/PRD.md`.
- Identify the target task, its mapped `REQ-*` requirement, affected modules, and acceptance criteria.

### Step 2: Task Transition & Scoped Execution
- Move the selected task to `[IN_PROGRESS]`.
- Execute the change within strict project boundaries using relevant domain skills (`job-search-automation-state`, `ai-ux-human-agent-interaction`, `ui-review`, `resilient-automation-patterns`).
- If `frontend/` assets are touched, run `python3 src/ui_builder.py` to synchronize `docs/`.

### Step 3: Deterministic Verification & Closure
Run the mandatory verification suite:
```bash
python3 tests/test_template_docs_sync.py
python3 scripts/validate_zero_emoji.py
python3 scripts/project_hygiene.py --check-secrets --validate
node -c frontend/js/dashboard.js docs/dashboard.js
python3 -m unittest discover -s tests -p "test_*.py"
```
- If all checks pass, record the task as `[x] **TASK-XX**` in `TASKS.md` with target files, numbered evidence items, and completion date, and synchronize `PROJECT_CONTEXT.md`.
- If checks fail, keep `[IN_PROGRESS]` or transition to `[BLOCKED]` and report the exact failure output.

### Step 4: Progress Reporting (Hebrew, RTL, Zero Emojis)
Present a concise Hebrew summary wrapped in `<div dir="rtl" style="text-align: right;">`:
- משימה ודרישה שטופלו: [מזהה משימה ודרישת PRD]
- קבצים שעודכנו: [קישורים קליקביליים לקבצים]
- ראיות אימות: [תוצאות בדיקות יחידה, סנכרון תבניות, היגיינה ואפס אימוג'ים]
- הצעד הבא: [משימה הבאה או המתנה להנחיה]
