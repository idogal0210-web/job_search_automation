---
trigger: always_on
description: "Mandates running full unit tests, project hygiene, and updating living documentation (TASKS.md, PROJECT_CONTEXT.md) before any Git commit or push."
---

# Pre-Push Verification and Living Documentation Guard

## 1. Core Principle
Zero broken pipelines, zero phantom progress, and zero outdated documentation on `main`. An AI agent must never commit or push unverified code or leave project documentation behind. The full end-to-end GitOps procedure (staging, branch management, sync, remote hygiene) is maintained in the global `save-and-sync` skill.

## 2. Invariant Rules (Iron Guards)

### Step 1: Mandatory Validation & Automated Tests
Before executing `git commit` or `git push`, the agent MUST execute and verify a clean exit code (`0`) on:
```bash
python3 scripts/project_hygiene.py --validate
python3 -m unittest discover -s tests -p "test_*.py"
```
- If any test fails, the agent MUST stop immediately, log the exact failure, and resolve the defect before committing.
- Fabricating test execution or claiming "tests passed" without concrete terminal evidence is strictly forbidden.

### Step 2: Mandatory Living Documentation Synchronization
Whenever ANY code, UI component, database adapter, or architecture element is modified:
1. **`TASKS.md`:** Must be updated in the SAME commit. Transition active items from `[IN_PROGRESS]` to `[DONE]` only when backed by reproducible test evidence.
2. **`PROJECT_CONTEXT.md`:** Must be updated in the SAME commit to reflect current architecture, schemas, or file trees.
3. **`README.md`:** Must be updated if the change alters user-facing features, CLI commands, or dashboard workflows.
4. **Dependencies:** If Python libraries are added or changed, both `requirements.txt` and `requirements-lock.txt` must be updated together.

### Step 3: Zero-Emoji Enforcement
Strictly verify that commit messages, code files, JSON payloads, and markdown artifacts contain zero emojis.
