# 7. שכבת נתונים

## 7.1 סכמות ומודלים
הסכמות מוגדרות באמצעות `pydantic.BaseModel` עם `strict=True` בקובץ `src/gemini_runtime.py`:

```python
class EvidenceQuote(BaseModel):
    model_config = ConfigDict(strict=True)
    quote: str = ""
    source_field: str = ""


class RequirementAssessment(BaseModel):
    model_config = ConfigDict(strict=True)
    requirement: str
    importance: Literal["required", "preferred", "unknown"] = "unknown"
    ad_evidence: EvidenceQuote = Field(default_factory=EvidenceQuote)
    profile_evidence: EvidenceQuote = Field(default_factory=EvidenceQuote)
    assessment: Literal["match", "gap", "unknown"] = "unknown"
    explanation: str = ""


class Evaluation(BaseModel):
    model_config = ConfigDict(strict=True)
    status: Literal["QUALIFIED", "DISQUALIFIED"]
    technical_role: bool
    match_score: int = Field(ge=0, le=100)
    concrete_matches_count: int = Field(ge=0, le=10)
    reasoning: str = Field(min_length=1)
    sector_key: Literal["solar", "natural_gas", "energy_tech", "drones", "cuas", "scada", "operations", "energy", "other"]
    sector: str = ""
    location: str = "לא צוין"
    company_domain_product: str = "לא צוין"
    job_summary: str = "לא צוין"
    experience_strengths: str = "לא צוין"
    key_highlights: str = "לא צוין"
    company_size: str = "לא צוין"
    junior_openness: str = "לא צוין"
    work_model: str = "לא צוין"
    company_requirements: str = "לא צוין"
    fit_gaps: str = "אין מספיק מידע לאימות פערי ההתאמה."
    requirement_assessments: list[RequirementAssessment] = Field(default_factory=list)

    @field_validator("junior_openness", mode="before")
    @classmethod
    def normalize_junior_openness(cls, v):
        if isinstance(v, bool):
            return "כן" if v else "לא"
        return str(v) if v is not None else "לא צוין"


class EvaluationUnavailable
```

## 7.2 קוד קריאה וכתיבה ומנגנון האחסון
- **מנגנון האחסון:** קובצי JSON שטוחים המאוחסנים ישירות בתוך ה-Git repository. אין שימוש במסד נתונים עצמאי (SQL/NoSQL) או בגיליון אלקטרוני.
- **קובצי הנתונים המרכזיים בתיקיית `data/` ו-`docs/data/`:**
  - `data/jobs_state.json`: מערך של כתובות URL מטופלות לצורך מניעת כפילויות סריקה.
  - `data/evaluation_state.json`: פנקס ההערכות המלא (`EvaluationLedger`) הכולל שלבי משרה (`RETRY_PENDING`, `READY`, `COMPLETE`), תוצאות הערכה מלאות, מועדי עדכון ומונה ניסיונות.
  - `data/sync_state.json`: נתוני אינטראקציית משתמש מהדשבורד (`saved`, `starred`, `rejected`, `purged`).
  - `data/historical_catalog.json`: קטלוג היסטורי של כלל המשרות המאושרות.
  - `data/weekly_archive.json`: ארכיון שבועי מתגלגל של משרות.
  - `docs/data/jobs.json`: קובץ נתוני המשרות הפעילות הנצרך ע"י ה-Frontend ב-GitHub Pages.
- **מנגנון כתיבה אטומית (`save_state_atomic`):**
  כתיבה דרך קובץ זמני (`tempfile.mkstemp`), ביצוע `f.flush()` ו-`os.fsync()`, יצירת עותק גיבוי `.bak` והחלפה מיידית אטומית באמצעות `os.replace`.

קוד השמירה והטעינה מתוך `src/state_manager.py` (שורות 8–43):
```python
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from src.url_utils import canonical_job_url, job_identity, content_identity

def load_state(filepath: str, default=None, *, strict=False):
    if default is None:
        default = {}
        
    if not os.path.exists(filepath):
        return default
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        if strict:
            raise
        return default

def save_state_atomic(filepath: str, data):
    filepath = os.fspath(filepath)
    bak_filepath = filepath + '.bak'
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
    
    fd, tmp_filepath = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(filepath)), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(filepath):
            shutil.copy2(filepath, bak_filepath)
        os.replace(tmp_filepath, filepath)
    finally:
        if os.path.exists(tmp_filepath):
            os.unlink(tmp_filepath)


class EvaluationLedger:
    """Separate retry snapshots from the backwards-compatible hand
```

## 7.3 מבנה אובייקט משרה אחד כפי שהוא נשמר בפועל (עם ערכים מזויפים)
```json
{
  "link": "https://www.example-jobs.com/view/1029384",
  "title": "SCADA Control Room Operator",
  "company": "Clean Energy Systems Ltd",
  "location": "מרכז הארץ / שפלה",
  "date": "2026-11-04T08:30:00Z",
  "source": "LinkedIn",
  "match_score": 92,
  "base_match_score": 92,
  "priority_bonus": 0,
  "evaluation_complete": true,
  "evidence_status": "verified",
  "sector_key": "scada",
  "sector": "בקרה ואוטומציה תעשייתית",
  "company_domain_product": "ניהול רשתות אנרגיה מתחדשת וחדרי בקרה",
  "company_summary": "חברה מובילה בתחום פתרונות בקרה לתחנות כוח ואגירת אנרגיה.",
  "job_summary": "תפעול שוטף של חדר הבקרה המרכזי 24/7, ניטור מערכות SCADA וטיפול בתקלות רשת בזמן אמת.",
  "company_requirements": "הנדסאי מכונות / חשמל / בקרה, ניסיון בחדרי בקרה תעשייתיים, היכרות עם פרוטוקולי תקשורת.",
  "experience_strengths": "התאמה מלאה של הרקע בבקרת תהליכים ומערכות אנרגיה, ניסיון במשמרות חדר בקרה ומנהיגות תפעולית.",
  "reasoning": "התאמה גבוהה במיוחד: ניסיון מעשי מוכח בחדרי בקרה 24/7, תפעול מערכות SCADA והשכלה כהנדסאי.",
  "key_highlights": "עבודה בסביבה טכנולוגית מתקדמת, מעורבות בפרויקטי תשתית לאומיים ואופק קידום.",
  "salary_range": "18,000 - 22,000 ₪",
  "salary_source_type": "market_range",
  "salary_source_label": "טווח שוק ממוצע לתפקידי בקרת SCADA",
  "salary_evidence": "מבוסס על נתוני שכר תעשייתיים לתפקידי מפעיל חדר בקרה 24/7",
  "salary_source_url": "",
  "p25": 18000,
  "p75": 22000,
  "logo": "clean_energy.png",
  "company_logo_url": "https://www.example-jobs.com/assets/logo.png",
  "snippet": "דרוש/ה מפעיל/ת חדר בקרה SCADA לתפעול שוטף של מערכות האנרגיה...",
  "stable_job_id": "clean_energy_scada_op_1029384",
  "content_hash": "a1b2c3d4e5f6789012345678abcdef01",
  "requirement_assessments": [
    {
      "requirement": "הנדסאי מכונות / חשמל / בקרה",
      "importance": "required",
      "ad_evidence": {
        "quote": "הנדסאי מכונות / חשמל",
        "source_field": "ad_requirements"
      },
      "profile_evidence": {
        "quote": "Certified Practical Mechanical Engineer (הנדסאי מכונות)",
        "source_field": "profile_credentials"
      },
      "assessment": "match",
      "explanation": "המועמד בעל דיפלומת הנדסאי מכונות מאומתת."
    }
  ],
  "fit_gaps": "אין פערי סף מהותיים; המועמד עונה על דרישות התפקיד.",
  "is_direct_ats": false,
  "is_field_work": false,
  "provides_company_car": false,
  "is_shifts_24_7": true,
  "is_junior_friendly": false,
  "curated_tags": [
    "חדר בקרה 24/7",
    "SCADA",
    "אנרגיה"
  ]
}
```


# 8. קריאות ל-LLM

## 8.1 רשימת המקומות בקוד שבהם מתבצעת קריאה ל-LLM

| מיקום בקוד | פונקציה קוראת | מודל / בריכת מודלים | מנגנון Retry | מטמון (Cache) | Batching |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `src/gemini_runtime.py:133-138` | `GeminiPool.evaluate` | `GEMINI_MODELS` (ברירת מחדל: `gemini-3.8-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`) | retry מובנה עם השהיה מעריכית + jitter, circuit breaker מבוסס זמן לפי סוג שגיאה | נשמר בפנקס `data/evaluation_state.json` (משרה שהוערכה לא נקראת שוב) | ללא (קריאה נפרדת לכל משרה) |
| `tools/cv_tailor/src/analyzer.py:94-101` | `analyze_job_match` | `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]` | לולאת fallback פשוטה במעבר למודל הבא | ללא | ללא |
| `tools/cv_tailor/src/generator.py:129-136` | `generate_tailored_package` | `["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]` | לולאת fallback פשוטה במעבר למודל הבא | ללא | ללא |

## 8.2 הערכת מספר הקריאות בהרצה אחת ונימוק מהקוד
1. **הרצה יומית של מנוע האיתור (`main.py`):**
   - **מספר קריאות ממוצע בהרצה:** בין 20 ל-45 קריאות LLM.
   - **נימוק מהקוד:**
     - איסוף המשרות ב-`main.py` מושך בין 50 ל-150 משרות גולמיות (2 דפי LinkedIn לאנרגיה, 2 דפי LinkedIn לרחפנים, דף אחד של Drushim, ופורטל Comeet).
     - פונקציית `EvaluationLedger.select` מסננת את כל המשרות שכבר עובדו בעבר (`handled_links` מ-`jobs_state.json` ומשרות בסטטוס `COMPLETE` ב-`evaluation_state.json`).
     - על המשרות הנותרות מופעלת פונקציית `evaluate_candidates` ב-`src/pipeline.py`.
     - בכל איטרציה נבדק תחילה `deterministic_filter(job)`. כ-50%–70% מהמשרות הגולמיות נפסלות כאן (משרות שיווק, HR, כספים, שכר מתחת ל-15k, מעסיקים מוחרגים) ואינן מגיעות כלל ל-LLM.
     - עבור כל משרה חדשה שעברה את הסינון הדטרמיניסטי מתבצעת קריאת Gemini בודדת דרך `GeminiPool.evaluate`.
     - במקרה של שגיאת רשת או timeout מתבצע ניסיון נוסף אחד (max_attempts=2). במקרה של חסימת מודל או חריגת מכסה, המודל מועבר ל-circuit breaker והקריאה מופנית למודל הבא בבריכה.
2. **הרצת כלי התאמת קו"ח (`tools/cv_tailor/tailor.py`):**
   - בדיוק 2 קריאות לכל הרצה: קריאה ראשונה לניתוח והתאמת ATS (`analyze_job_match`), וקריאה שנייה להפקת קורות החיים והמכתב המקדים (`generate_tailored_package`).


# 9. תזמון, פריסה והרצה

## 9.1 קובץ תזמון הריצה היומית - `.github/workflows/daily_job_search.yml` (קוד מלא)
```yaml
name: Daily Job Search Automation

on:
  schedule:
    - cron: '17 4 * * 0-5'
    - cron: '17 5 * * 0-5'
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: "daily-job-search"
  cancel-in-progress: false

jobs:
  schedule-gate:
    runs-on: ubuntu-latest
    permissions:
      contents: read
    outputs:
      run: ${{ steps.gate.outputs.run }}
    steps:
      - id: gate
        env:
          EVENT_NAME: ${{ github.event_name }}
          EVENT_SCHEDULE: ${{ github.event.schedule }}
        run: |
          python - <<'PYTHON'
          import os
          from datetime import datetime
          from zoneinfo import ZoneInfo
          local = datetime.now(ZoneInfo("Asia/Jerusalem"))
          utc_hour = 7 - int(local.utcoffset().total_seconds() // 3600)
          expected = f"17 {utc_hour} * * 0-5"
          enabled = os.environ["EVENT_NAME"] == "workflow_dispatch" or os.environ["EVENT_SCHEDULE"] == expected
          with open(os.environ["GITHUB_OUTPUT"], "a") as output:
              output.write(f"run={str(enabled).lower()}\n")
          PYTHON

  job-search-daily:
    permissions:
      contents: write
    needs: schedule-gate
    if: needs.schedule-gate.outputs.run == 'true'
    runs-on: ubuntu-latest
    timeout-minutes: 60
    name: "Daily Job Search - <REDACTED_NAME>"

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          ref: main
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version-file: .python-version
          cache: 'pip'

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Test Suite (Quality & Reliability Gate)
        run: |
          python -m unittest discover tests/ -v

      - name: Run Daily Energy & Drone Job Searches
        id: search
        continue-on-error: true
        timeout-minutes: 40
        env:
          PYTHONUNBUFFERED: '1'
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
          SENDER_APP_PASSWORD: ${{ secrets.SENDER_APP_PASSWORD }}
          GEMINI_MODELS: ${{ vars.GEMINI_MODELS }}
        run: |
          python -u main.py

      - name: Persist checkpoints even when search fails
        if: ${{ always() && (steps.search.outcome == 'success' || steps.search.outcome == 'failure') }}
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          
          for path in data/jobs_state.json data/evaluation_state.json data/weekly_archive.json data/historical_catalog.json docs/index.html docs/data/jobs.json docs/data/historical_catalog.json docs/dashboard.css docs/dashboard.js docs/assets; do
            if test -e "$path"; then git add -- "$path"; fi
          done
          
          if ! git diff --staged --quiet; then
            git commit -m "chore: save job evaluations and dashboard [skip ci]"
          fi

          # Discard any remaining unstaged changes or untracked scratch files to guarantee clean working tree
          git checkout -- . 2>/dev/null || true
          git clean -fd 2>/dev/null || true

          # Push only if local HEAD is ahead of origin/main
          if [ $(git rev-list --count origin/main..HEAD) -gt 0 ]; then
            pushed=false
            for attempt in 1 2 3; do
              echo "Push attempt $attempt..."
              if git pull --rebase -X theirs origin main && git push origin HEAD:main; then
                pushed=true
                echo "Successfully pushed to origin/main on attempt $attempt"
                break
              fi
              if test -d .git/rebase-merge || test -d .git/rebase-apply; then
                git rebase --abort 2>/dev/null || true
              fi
              echo "Push attempt $attempt failed. Waiting before retry..."
              sleep $(( attempt * 5 ))
            done

            if [ "$pushed" = false ]; then
              echo "Error: Failed to push to origin/main after 3 attempts"
              exit 1
            fi
          else
            echo "No changes to commit or push."
          fi

      - name: Preserve checkpoint recovery artifact
        if: ${{ failure() && steps.search.outcome != 'skipped' }}
        uses: actions/upload-artifact@v4
        with:
          name: checkpoint-recovery-${{ github.run_id }}
          retention-days: 3
          path: |
            data/jobs_state.json
            data/evaluation_state.json
            data/weekly_archive.json
            data/historical_catalog.json

      - name: Verify Search Outcome
        id: report
        if: ${{ always() && (steps.search.outcome == 'success' || steps.search.outcome == 'failure') }}
        env:
          SEARCH_OUTCOME: ${{ steps.search.outcome }}
        run: |
          if test "$SEARCH_OUTCOME" != 'success'; then
            echo 'Search failed; checkpoints were attempted above. Inspect the state commit step.' >> "$GITHUB_STEP_SUMMARY"
            exit 1
          fi

      - name: Send Urgent Failure Alert Email (Exceptions Only)
        if: failure() || cancelled()
        env:
          SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
          SENDER_APP_PASSWORD: ${{ secrets.SENDER_APP_PASSWORD }}
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          python3 -c "
          import os, smtplib
          from email.mime.text import MIMEText
          from email.mime.multipart import MIMEMultipart
          from email.header import Header

          sender = os.environ.get('SENDER_EMAIL')
          pwd = os.environ.get('SENDER_APP_PASSWORD')
          run_url = os.environ.get('RUN_URL')
          recipient = '<REDACTED_EMAIL>'

          if sender and pwd:
              msg = MIMEMultipart()
              msg['Subject'] = Header('[התראת תקלה] ריצת חיפוש המשרות נכשלה | <REDACTED_NAME>', 'utf-8')
              msg['From'] = Header(f'Job Search Alert <{sender}>', 'utf-8')
              msg['To'] = Header(recipient, 'utf-8')
              body = f'<div dir=\"rtl\" style=\"font-family: Arial; padding: 20px;\"><h2 style=\"color: #dc2626;\">[שגיאה] התרחשה שגיאה בריצת חיפוש המשרות</h2><p>ריצת האוטומציה נתקלה בשגיאה באחד השלבים.</p><p><a href=\"{run_url}\" style=\"background: #dc2626; color: white; padding: 10px 16px; text-decoration: none; border-radius: 6px; display: inline-block;\">צפה ביומן הריצה ב-GitHub Actions ↗</a></p></div>'
              msg.attach(MIMEText(body, 'html', 'utf-8'))
              server = smtplib.SMTP('smtp.gmail.com', 587, timeout=20)
              server.starttls()
              server.login(sender, pwd)
              server.sendmail(sender, recipient, msg.as_string())
              server.quit()
              print('[+] Failure alert email dispatched.')
          "

```

## 9.2 קובץ בדיקות ובנייה רציפה - `.github/workflows/ci.yml` (קוד מלא)
```yaml
name: CI

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  test-and-verify:
    name: Test Suite & Build Verification
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5

      - name: Set up Python
        uses: actions/setup-python@v6
        with:
          python-version-file: .python-version
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Validate Zero Emoji
        run: |
          python scripts/validate_zero_emoji.py

      - name: Run Unit Tests
        run: |
          python -m unittest discover tests/ -v

      - name: Verify Dashboard Build & Sync
        run: |
          python -c "
          import tempfile
          from src.ui_builder import build_and_save_docs_app
          with tempfile.TemporaryDirectory() as root:
              build_and_save_docs_app([], [], root, is_weekly=False)
          print('CI build test passed successfully')
          "
          cmp docs/dashboard.css frontend/css/dashboard.css
          cmp docs/dashboard.js frontend/js/dashboard.js
          echo "Verified: docs/ CSS and JS are synchronized with frontend/ source of truth."

```

## 9.3 Dockerfile, סקריפטי פריסה ותזמונים נוספים
- **Dockerfile / Docker Compose:** לא קיים בפרויקט.
- **Crontab מקומי / Systemd:** לא קיים בפרויקט. התזמון מנוהל במלואו באמצעות GitHub Actions Cron (`17 4 * * 0-5` ו-`17 5 * * 0-5` לתמיכה בשעון חורף/קיץ בישראל).
- **פריסת הדשבורד:** הפריסה מבוצעת באמצעות GitOps ישירות ל-GitHub Pages ע"י כתיבה לתיקיית `docs/` וביצוע Git Push של `docs/index.html` ו-`docs/data/jobs.json`.


# 10. תצורה ותלויות

## 10.1 קובץ התלויות - `requirements.txt` (תוכן מלא)
```text
google-genai>=1.47.0,<2
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
pydantic>=2.13.4,<3
rich>=13.0.0

```

## 10.2 קובץ הנעילה - `requirements-lock.txt` (תוכן מלא)
```text
# Exact pinned dependencies for reproducible builds (Python 3.11)
annotated-types==0.7.0
anyio==4.12.1
beautifulsoup4==4.15.0
certifi==2026.7.22
cffi==2.0.0
charset-normalizer==3.4.9
cryptography==50.0.0
exceptiongroup==1.3.1
google-auth==2.50.0
google-genai==1.47.0
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.18
markdown-it-py==3.0.0
mdurl==0.1.2
pyasn1==0.6.4
pyasn1_modules==0.4.2
pycparser==2.23
pydantic==2.13.4
pydantic_core==2.46.4
Pygments==2.21.0
PyNaCl==1.6.2
python-dotenv==1.2.1
requests==2.32.5
rich==15.0.0
soupsieve==2.8.4
tenacity==9.1.2
typing-inspection==0.4.2
typing_extensions==4.16.0
urllib3==2.6.3
websockets==15.0.1

```

## 10.3 גרסת Python - `.python-version`
```text
3.11

```

## 10.4 קובץ `pyproject.toml` או `package.json`
- `pyproject.toml`: לא קיים בפרויקט.
- `package.json`: לא קיים בפרויקט.

## 10.5 קובץ תצורת מדיניות פרויקט - `.save-and-sync.yml` (תוכן מלא)
```yaml
# save-and-sync Project Policy Configuration
# Project: job_search_automation
version: 1
project: job_search_automation
expected_remote: origin
expected_branch: main

# Tier 1: Protected Paths (Never delete or relocate under any circumstance)
protected_paths:
  - "main.py"
  - "src/**"
  - "data/**"
  - "docs/**"
  - ".agents/**"
  - ".github/**"
  - ".env"
  - ".gitignore"
  - "requirements*.txt"
  - "tests/**"
  - "tools/**"
  - "frontend/**"
  - "scripts/**"
  - "PROJECT_CONTEXT.md"
  - "README.md"

# Tier 2: Ephemeral & Disposable Patterns (Immediate safe removal on CLEAN / SYNC_AND_CLEAN)
disposable_patterns:
  - "**/*.bak"
  - "**/*.tmp"
  - "**/*.temp"
  - "**/.DS_Store"
  - "**/Thumbs.db"
  - "**/__pycache__"
  - "**/*.pyc"
  - "**/*.pyo"

# Tier 3: Log Retention Rules
log_retention:
  max_age_days: 7
  max_lines: 500
  paths:
    - "logs/*.log"

# Tier 4: Safe Recovery & Staging
recovery:
  enabled: true
  path: ".recovery"
  retention_days: 14

# Validation Checks
validation:
  python_syntax_check: true
  json_syntax_check: true
  secret_scan: true
  run_unit_tests: true

```

## 10.6 רשימת משתני הסביבה (שמות בלבד)
- `EVENT_NAME`
- `EVENT_SCHEDULE`
- `EXCLUDED_EMPLOYERS`
- `GEMINI_API_KEY`
- `GEMINI_MODELS`
- `GITHUB_STEP_SUMMARY`
- `GITHUB_TOKEN`
- `GOOGLE_SEARCH_API_KEY`
- `GOOGLE_SEARCH_CX`
- `GROQ_API_KEY`
- `PREFER_GROQ`
- `PYTHONUNBUFFERED`
- `RUN_URL`
- `SEARCH_OUTCOME`
- `SENDER_APP_PASSWORD`
- `SENDER_EMAIL`
- `SENDER_PASSWORD`
