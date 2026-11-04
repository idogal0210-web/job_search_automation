---
name: task-lifecycle-manager
description: "Manages the project task lifecycle, roadmap, and milestone verification for job_search_automation. Tracks tasks in TASKS.md through distinct phases: Backlog, In Progress, Blocked, and Verified Done. Prevents phantom progress and requires concrete tests/evidence before marking tasks as complete. Strictly zero emojis."
---

# Task Lifecycle Manager — job_search_automation

Manages the lifecycle of project tasks, engineering backlog, and sprint milestones. Ensures all agent actions map directly to verified user requirements and prevents false completion claims.

## 1. Operating Rules & Principles
- **Single Source of Truth**: All tasks, bugs, and feature requests are tracked in `TASKS.md` at the project root.
- **Evidence-Based Completion**: A task can ONLY be marked as `[x]` (Done) if accompanied by concrete evidence:
  - Unit tests or integration test execution output.
  - File verification and syntax checks (`python3 scripts/project_hygiene.py --validate`).
  - Working tree and UI inspection.
- **Strictly Zero Emojis**: Never use emojis in `TASKS.md`, commit messages, task summaries, or status tags (adheres strictly to `zero-emojis.md`).
- **Bounded Scope**: Never invent tasks outside user instructions. Keep tasks atomic, testable, and actionable.

## 2. Task Lifecycle States
Every item in `TASKS.md` resides in one of four states:
1. `[BACKLOG]`: Planned tasks awaiting implementation.
2. `[IN_PROGRESS]`: Currently active task being executed in the current session.
3. `[BLOCKED]`: Task waiting on external dependency, API key, or explicit user decision.
4. `[DONE]`: Verified complete with evidence (test result, commit hash, or output artifact).

## 3. Workflow Steps

### Step 1: Initialize or Load TASKS.md
When invoked, check if `TASKS.md` exists at the project root.
- If missing, generate a clean, structured `TASKS.md` based on active goals, outstanding bugs, and project architecture.
- If present, read active tasks, identify the next high-priority item, and summarize remaining work.

### Step 2: Task Transition & Execution
- Move the selected task to `[IN_PROGRESS]`.
- Execute the task within strict project boundaries (using relevant skills: `job-search-automation-state`, `modern-web-guidance`, etc.).

### Step 3: Verification & Closure
- Run regression tests and syntax checks:
  ```bash
  python3 scripts/project_hygiene.py --validate
  python3 -m unittest discover -s tests -p "test_*.py"
  ```
- If all checks pass, mark the task as `[DONE]` with a timestamp and proof snippet.
- If checks fail, log the issue, transition to `[BLOCKED]` or keep `[IN_PROGRESS]`, and report exact blocker.

### Step 4: Progress Reporting (Hebrew, RTL, Zero Emojis)
Present a clean, structured Hebrew summary:
- משימה שטופלה: [תיאור המשימה]
- ראיות אימות: [תוצאת בדיקות / קבצים שנבדקו]
- סטטוס משימות כולל: [X מתוך Y הושלמו]
- המשימה הבאה בתור: [פירוט הצעד הבא]
