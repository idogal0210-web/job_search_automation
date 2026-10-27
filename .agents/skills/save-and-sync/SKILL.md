---
name: save-and-sync
description: |
  Save authorized changes, commit selected work, synchronize with verified GitHub upstream, and run deterministic project hygiene cleanup for job_search_automation.
  Supported operations: SAVE, COMMIT, SYNC, CLEAN, SYNC_AND_CLEAN, and AUDIT.
  Driven by .save-and-sync.yml policy and scripts/project_hygiene.py.
  Strictly enforces zero emojis in all executive summaries and reports.
---

# Save & Sync Protocol — job_search_automation

Keep authorized Git changes synchronized with the remote GitHub branch and maintain a lean, clean, leak-free project tree through deterministic evidence-based cleanup.

## 1. Operations & Modes
- **SAVE**: Save requested modified files locally. No Git commit, push, or file deletion.
- **COMMIT**: Create a local Git commit containing authorized changes with semantic message.
- **SYNC**: Fetch, reconcile with remote `origin/main`, and push authorized commits.
- **CLEAN**: Run deterministic project hygiene via `scripts/project_hygiene.py --clean` based on `.save-and-sync.yml`.
- **SYNC_AND_CLEAN**: Reconcile with remote GitHub, push commits, and execute deterministic cleanup.
- **AUDIT**: Read-only dry-run scan (`scripts/project_hygiene.py --audit`) showing disposable items without mutations.

Rules:
- Never infer `CLEAN` from `SAVE` or `SYNC`.
- Disambiguate "שמור ועדכן" / "שמור וסנכרן" from context; if intended operation is unclear, ask one focused question.
- Always refer to the remote platform as **GitHub** (never generic git).
- Strictly enforce zero emojis in all output summaries and logs.

## 2. Preflight & Project Policy
Policy configuration is strictly loaded from `.save-and-sync.yml` at the repository root.

### 4-Tier Classification:
1. **Tier 1 — Protected (Never Delete)**:
   `main.py`, `src/**`, `data/**` (jobs state, evaluation state, catalogs), `docs/**` (dashboard), `.agents/**`, `.github/**`, `.env`, `.gitignore`, `requirements*.txt`, `tests/**`, `tools/**`, `frontend/**`, `scripts/**`, `PROJECT_CONTEXT.md`, `README.md`.
2. **Tier 2 — Ephemeral Disposable (Safe Immediate Purge)**:
   `__pycache__/`, `*.pyc`, `*.pyo`, `.DS_Store`, `Thumbs.db`, `*.bak`, `*.tmp`, `*.temp`.
3. **Tier 3 — Log Retention**:
   Logs under `logs/*.log` older than 7 days or larger than 500 lines are pruned/truncated via `scripts/project_hygiene.py`.
4. **Tier 4 — Untracked / Unknown Candidates**:
   Unknown root leftovers or unreferenced drafts are never blindly deleted; relocate to `.recovery/YYYY-MM-DD/` with manifest or report in `AUDIT`.

## 3. Step-by-Step Execution Protocol

### Step 1: Validation & Integrity Check
Before staging or pushing, run:
```bash
python3 scripts/project_hygiene.py --validate
python3 -m unittest discover -s tests -p "test_*.py"
```
Must verify: zero syntax errors, zero broken JSON datasets, zero failing tests.

### Step 2: Pre-Commit Secret Scanning & Zero-Emoji Verification
Run automated secret pattern detection:
```bash
python3 scripts/project_hygiene.py --check-secrets
```
Must verify: zero unredacted API tokens (GitHub, Gemini, Tavily, Firecrawl, Hugging Face) and zero private keys staged.
Scan new files to ensure zero emojis are present in code, commit messages, or markdown artifacts.

### Step 3: Deterministic Cleanup (When CLEAN or SYNC_AND_CLEAN requested)
Execute the deterministic cleanup script:
```bash
python3 scripts/project_hygiene.py --clean
```
Captures exact count of items removed and total disk space freed.

### Step 4: GitHub Cloud Synchronization (When SYNC or SYNC_AND_CLEAN requested)
1. Inspect working tree: `git status --porcelain`.
2. Fetch remote and check divergence: `git fetch origin main`.
3. If remote is ahead, integrate cleanly per policy before pushing. Never rebase over uncommitted changes; never force-push.
4. Stage verified files: `git add <paths>`.
5. Create semantic commit: `feat(...)`, `fix(...)`, `chore(...)`, `refactor(...)`.
6. Push to GitHub: `git push origin main` (retry up to 3 times on transient transport failures with backoff).
7. Verify remote branch tip matches local commit.

## 4. Completion Report Format (Hebrew, RTL, Zero Emojis)
Always produce a clean, structured RTL summary without emojis:

- פעולה שבוצעה: [שמירה / התאמה / סנכרון / סנכרון ונקה]
- בדיקת תקינות ואינטגריטי: תקין (תחביר Python, קובצי JSON ובדיקות יחידה)
- סריקת אבטחה וסודות: תקין (אפס מפתחות דולפים, אפס אימוג'ים)
- היגיינת פרויקט וניקוי: [פירוט כמות הפריטים שנוקו ושטח הדיסק שפונה]
- סנכרון GitHub: [Hash של ה-Commit, ענף main, סטטוס Push מאומת]
- קבצים מקומיים שנשמרו: [רשימת קבצים]
- שורה תחתונה: הפרויקט רזה, נקי, מאובטח, שמור ומסונכרן במלואו מול GitHub.
