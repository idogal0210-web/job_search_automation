# PROJECT_CONTEXT.md

## 1. Project Overview & Goal
- **Product Purpose:** Autonomous job search, evaluation, salary prediction, and triage platform developed for Ido Gal.
- **Core Problem Solved:** Eliminates noise from non-technical, administrative, and irrelevant listings by executing deterministic pre-filtering followed by structured Gemini LLM evaluation and salary benchmarking.
- **Target Audience & Profile:** Ido Gal, a certified practical mechanical engineer (הנדסאי מכונות מוסמך) specializing in solar energy (PV), natural gas, SCADA/PLC control systems, and UAV/drone operations across Israel.

---

## 2. Tech Stack & Environment
- **Runtime & Backend:** Python 3.9+ / Python 3.14 (core pipeline, fetchers, evaluators, salary engine, unit test suite).
- **Frontend & Dashboard:** Pure Vanilla HTML5, Modern CSS3 (CSS Grid, Flexbox, CSS Variables, Backdrop-Filter glassmorphism), ES6+ JavaScript (Zero-framework, single-page application).
- **AI & LLM Services:** Google Gemini API via official `google-genai` SDK (`GeminiPool` utilizing `gemini-3.8-flash`, `gemini-3.5-flash-lite`, and `gemini-3.5-flash` with strict Pydantic JSON schema enforcement; Groq API is completely decommissioned and removed).
- **Client Libraries & Icons:** Phosphor Icons (vector SVG web font), Leaflet.js 1.9.4 with Leaflet.markercluster (geographic map view and coordinate clustering), Chart.js (sector distribution visualization).
- **Scraping & Data Extraction:** BeautifulSoup4, Requests, Urllib (custom User-Agent spoofing, exponential backoff, rate limiting).
- **Storage & State:** Flat atomic JSON files under `data/` (`jobs_state.json`, `weekly_archive.json`, `historical_catalog.json`, `evaluation_state.json`), Browser LocalStorage for client-side user triage state.
- **Hosting & Infrastructure:** GitHub Pages (static web app hosting from `docs/`), GitHub Actions (scheduled daily runs and CI/CD), internal `save-and-sync` protocol for atomic GitOps deployments.
- **Critical Environment Variables:**
  - `GEMINI_API_KEY`: API authentication key for Google Gemini LLM evaluation.
  - `GEMINI_MODELS`: Comma-separated fallback model list (defaults to `gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.5-flash`).
  - `SENDER_EMAIL`: Gmail account used for dispatching daily email job alerts.
  - `SENDER_APP_PASSWORD` (or `SENDER_PASSWORD`): Gmail App Password for SMTP dispatch authentication.
  - `GITHUB_TOKEN`: Automated GitHub Actions token used to commit daily state checkpoints to `main`.
  - `GITHUB_STEP_SUMMARY`: Workflow step summary path in GitHub Actions for execution metrics.

---

## 3. Directory Structure & Key Files
```
job_search_automation/
├── main.py                         # Application CLI entrypoint; coordinates fetch, evaluation, storage, and build
├── PROJECT_CONTEXT.md              # Single source of truth context anchor for AI agents and developers
├── requirements.txt                # Python package dependencies
├── .python-version                 # Target Python runtime anchor (Python 3.14 / 3.9+)
├── .agents/                        # Operational policies and domain skills
│   ├── rules/                      # System rules (mcp-policy.md, hebrew-rtl.md, critical-thinking-quality.md)
│   └── skills/                     # Specialized skills (salary-intelligence, cloud-sync, health-audit, etc.)
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Continuous integration: test suite, UI build check, zero emoji guard on PRs
│       └── daily_job_search.yml    # Active scheduled daily GitHub Actions cron workflow (07:17 IST / 04:17 UTC)
├── frontend/                       # Source files for the web application (modular separation)
│   ├── templates/index.html        # HTML layout shell and metadata slots
│   ├── css/dashboard.css           # Modular dashboard CSS styles
│   └── js/dashboard.js             # Client-side SPA application logic and data fetcher
├── src/
│   ├── pipeline.py                 # Core orchestration pipeline managing run health, stages, and metrics
│   ├── fetchers.py                 # Multi-source scrapers for LinkedIn, Drushim, and direct Comeet ATS
│   ├── job_policy.py               # Deterministic blacklist filters, technical keyword sets, and title rules
│   ├── gemini_runtime.py           # Multi-model Gemini fallback pool with structured output validation and retry
│   ├── evaluators.py               # Match score evaluator (0-100), target company bonuses, and keyword fallback
│   ├── salary_engine.py            # Evidence-based salary prediction, comparable role calibration, confidence scoring
│   ├── state_manager.py            # Job deduplication, status tracking (QUALIFIED/DISQUALIFIED/RETRY_PENDING), storage
│   ├── ui_builder.py               # Build orchestrator compiling frontend/ assets and data into docs/
│   └── publishers.py               # Email dispatch and webhook notification services
├── docs/
│   ├── index.html                  # Lightweight production SPA shell (~31KB) hosted on GitHub Pages
│   ├── dashboard.css               # Compiled dashboard styles
│   ├── dashboard.js                # Compiled application script
│   ├── theme.css                   # Global design tokens, color variables, and base responsive styles
│   ├── fonts.css                   # Local font declarations
│   ├── data/
│   │   ├── jobs.json               # Current jobs payload (schema version 2.0.0, UI-compacted)
│   │   └── historical_catalog.json # Historical catalog for on-demand lazy lookup
│   ├── UPGRADE_STATUS.md           # Upgrade implementation tracking matrix for tasks U1-U7
│   └── assets/                     # Static UI assets and fonts
├── data/
│   ├── jobs_state.json             # Active tracked job identifiers and links
│   ├── weekly_archive.json         # Complete weekly archive containing full metadata, AI scores, and salary data
│   ├── historical_catalog.json     # Historical job catalog for cross-cycle deduplication
│   ├── evaluation_state.json       # Evaluation cache and retry pending queues
│   └── evaluation_benchmark_template.json # Benchmark schema and ground-truth dataset template
├── scripts/
│   └── evaluate_dataset.py         # Confusion matrix, Precision/Recall/F1 and False Negatives evaluator
├── tests/                          # Automated unit and integration test suite (73 passing tests)
│   ├── test_curated_tags.py        # Curated operational tags positive triggers & negative guards tests (14 tests)
│   ├── test_recovery.py            # Degradation and error recovery tests
│   ├── test_salary_intelligence.py # Salary prediction engine tests
│   ├── test_requeue.py             # Evaluation requeue and retry tests
│   ├── test_main_integration.py    # Pipeline integration tests
│   ├── test_evidence_assessments.py# U4: Requirement assessments & evidence validation tests
│   ├── test_benchmark_metrics.py   # U5: Benchmark dataset evaluation tests
│   ├── test_comeet_connector.py    # U7: Direct Comeet ATS connector tests
│   ├── test_phase_b_precision.py   # AI evaluation precision and schema tests
│   └── test_reliability_phase_a.py # Scraper and fallback reliability tests
└── scripts/
    └── requeue_jobs.py             # Utility script for re-evaluating pending or cached jobs
```

---

## 4. Architecture & Data Flow

### 4.1 Pipeline Data Flow
```
1. Fetchers (LinkedIn, Drushim, Comeet)
   ↓ Raw job postings (title, company, link, location)
2. Deterministic Filtering (job_policy.py)
   ↓ Immediate exclusion of non-technical titles (NON_TECHNICAL_TITLES) and blocked firms (BLACKLIST)
3. State Deduplication (state_manager.py)
   ↓ Verification against historical_catalog.json; drops seen jobs
4. AI Evaluation Pool (gemini_runtime.py & evaluators.py)
   ↓ Structured LLM evaluation (base score, priority bonus, concrete matches, Hebrew rationale)
5. Salary Intelligence (salary_engine.py)
   ↓ Predicts salary range (min, max, confidence, benchmark source)
6. State Persistence (data/*.json)
   ↓ Atomic disk updates to weekly_archive.json and jobs_state.json
7. Web Dashboard Generation (ui_builder.py)
   ↓ Generates docs/index.html from weekly_archive.json data
8. Notification Publisher (publishers.py)
   ↓ Dispatches HTML email digest if qualified jobs are found
```

### 4.2 Core Data Models (`Job` Schema)
- `id`: String (deterministic SHA-256 hash derived from job URL).
- `link`: String (original canonical vacancy URL).
- `title`: String (scraped job title).
- `company`: String (employer name).
- `location`: String (geographic city/region in Israel).
- `date`: String (`YYYY-MM-DD` publication date).
- `sector`: String (technical sector: `solar`, `gas`, `scada`, `drones`, `energy`, `operations`).
- `description`: String (extracted job description text).
- `status`: String (`QUALIFIED`, `DISQUALIFIED`, `RETRY_PENDING`).
- `match_score`: Integer (overall weighted fit score, 0 to 100).
- `base_match_score`: Integer (raw AI evaluation score).
- `priority_bonus`: Integer (+5 bonus for verified target employers).
- `concrete_matches_count`: Integer (count of confirmed technical requirement matches).
- `reasoning`: String (concise Hebrew explanation of evaluation rationale).
- `salary_min`: Integer (predicted minimum monthly gross compensation in ILS).
- `salary_max`: Integer (predicted maximum monthly gross compensation in ILS).
- `salary_confidence`: String (`HIGH`, `MEDIUM`, `LOW`, `NONE`).
- `salary_benchmark_source`: String (reference market evidence or role comparable).
- `coordinates`: Object (optional `lat`, `lng` for Leaflet map markers).

---

## 5. Implementation Status

### 5.1 Functional Components (Done)
- **Multi-source automated scrapers:** Working scrapers for LinkedIn (Energy, Drones) and Drushim (Industry, Energy, Operations).
- **Deterministic zero-token filter:** Instant regex-based rejection of non-technical roles (accounting, HR, sales, legal) and blacklisted operators (Chevron, Energean, INGL).
- **Structured Gemini LLM evaluation:** Multi-model pool with Pydantic JSON schemas, automatic backoff, jitter, and quota error isolation.
- **Evidence-based salary engine:** Predicts salary brackets and confidence scores based on sector benchmarks and role equivalencies.
- **Crash-resilient persistence:** Atomic file updates preventing corruption during execution interruptions.
- **Interactive multi-view web dashboard:**
  - View modes: Grid (Cubes), List (Compact single-column), and Map (Leaflet MarkerCluster spiderfy).
  - Client-side triage system: Star, Save, Reject with LocalStorage persistence and bulk actions.
  - Search and filter controls: Sector filter, region filter, realtime keyword search with clear button, and dynamic sorting.
  - Mobile optimization: Tested on iPhone 14 (390px) and iPhone SE (375px) featuring a symmetrical 4-pill metric toggle, non-overlapping 2-tier filter grid, zero horizontal overflow, and strictly centered sort icon.
  - Accessibility: WCAG AA compliant 44x44px touch targets on all interactive controls.
- **Automated test suite:** 49 comprehensive unit and integration tests passing in under 0.1 seconds.
- **High-resolution company logo pipeline:**
  - Scraper extraction: Direct capture of high-res CDN logo URLs in `fetch_linkedin_jobs` (`artdeco-entity-image`) and `fetch_drushim_jobs` (`webapi.drushim.co.il/logos`).
  - Curated dictionary & word-boundary matching: Curated dictionary of 60+ Israeli and international companies with regex word boundary matching preventing substring collisions (`ratio` inside `corporation`). Verified official corporate domains (e.g. `nextcomgroup.com`, `mechanical-devices.com`, `eladsoft.com`, `michlolltd.co.il`, `e2eil.co.il`, `assatec.co.il`, `nyga-chef.co.il`, `zoll.com`, etc.).
  - 4-Tier client-side logo fallback chain: Direct CDN logo -> Google Favicon S2 (sz=128) -> Unavatar API -> DuckDuckGo Icons API -> Branded monogram avatar with deterministic color gradient.
  - Complete data backfill: 100% of jobs in `data/weekly_archive.json` (80/80) and 200+ historical catalog records enriched with authentic logos.
- **Complete Tag & Chip Elimination & Desktop-Mobile Structural Parity:**
  - Zero-tag clean architecture: Complete removal of all tags and chips from job cards, modal dialogs, and filters (sector tag chips, header condition chips, salary chips, experience chips, AI score driver chips, and quick filter chips strip).
  - Dead code cleanup: 1,456 lines of dead chip DOM, helper functions (`getExperienceChip`, `getExplicitConditionChips`, `formatCompactSalary`, `getAiScoreDrivers`, `selectQuickChip`, `isJuniorFriendly`), and unused CSS completely purged.
  - 100% structural parity between Desktop and Mobile: Identical component hierarchy across viewports: topbar (star, share, match score badge), company logo + cyan company name + white title, 2 distinct content bubbles (Domain & Product, Job Requirements), progressive disclosure toggle ("הרחב ניתוח מלא" / "הסתר ניתוח מלא" enabled on both desktop and mobile), collapsible summary & AI insight (including full salary intelligence and benchmark links directly inline without popups), and a balanced 2-tier action structure (Row 1: Save + Reject triage buttons, Row 2: prominent full-width Apply link).
  - State integrity & self-healing: Automated remediation for browser LocalStorage starred state, preventing bulk injection while strictly safeguarding user-marked favorites (6-7 starred jobs).
- **GitOps Save & Sync protocol:** Unified zero-waste cleanup (purged obsolete `integration/` templates and caches), syntax validation, pre-commit secret scanning, zero-emoji verification, and two-way GitHub push.

### 5.2 In Progress (WIP)
- **Salary engine market calibration:** Fine-tuning compensation bands based on user feedback and emerging Israeli industrial salary data.

### 5.3 Backlog / Next Steps
- **Direct ATS connectors:** Adding scrapers for direct Comeet and Greenhouse job board endpoints of target companies.
- **Scheduled cloud executions:** Regular unattended runs via GitHub Actions cron workflows.

---

## 6. Development Rules & Constraints

### 6.1 Strict Zero Emojis Policy
- **Absolute Rule:** Exactly 0 emojis are permitted across the entire repository. This includes Python source code, HTML templates, CSS styles, JavaScript logic, JSON data files, Git commit messages, documentation, and agent chat messages.
- **Enforcement:** Use Phosphor Icons (`ph-` classes) or standard vector SVG glyphs for all visual iconography.

### 6.2 Frontend Architecture & Build Orchestration
- **Source Files:** The frontend source code is cleanly separated in `frontend/` (`frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/js/dashboard.js`).
- **Build Pipeline:** `src/ui_builder.py` orchestrates the build process via `build_and_save_docs_app`, outputting the lightweight HTML shell to `docs/index.html`, bundled CSS/JS assets, and decoupled data feeds (`docs/data/jobs.json` with schema version 2.0.0 and `docs/data/historical_catalog.json`).
- **Prohibited Action:** Never directly edit compiled production files in `docs/index.html`, `docs/dashboard.css`, `docs/dashboard.js`, or `docs/data/`. Always apply edits to `frontend/` or `src/ui_builder.py` and rebuild.

### 6.3 Bidirectional Text & RTL Formatting
- **Hebrew Layout:** The entire user interface and Hebrew conversational outputs must follow strict RTL formatting (`dir="rtl"`).
- **Text Isolation:** Mixed English terms, numbers, and technical identifiers must be isolated with `dir="auto"` or `text-align: start`.

### 6.4 Touch Targets & Responsive Layout
- **Minimum Tap Size:** Interactive controls (buttons, links, select inputs) must maintain a minimum physical hit area of 44x44 CSS pixels.
- **Mobile First:** Ensure zero horizontal overflow (`scrollWidth <= windowWidth`) and complete symmetry across viewports down to 360px.

### 6.5 Secret Hygiene & Security
- **No Hardcoded Credentials:** Never place API keys, passwords, or tokens in source code, commit history, or logs.
- **Pre-commit Scan:** All staged files must pass regex scanning for credentials before committing.

### 6.6 Curated Job Tags & Triage State Parity
- **5 Curated Tags (Dual-Layer Architecture with Negative Guards):** The dashboard strictly displays up to 5 verified operational tags positioned directly beneath `.job-card-main-header` and above `.job-bubbles-wrapper`, extracted via Backend data enrichment (`src/job_policy.py`, `src/ui_builder.py`) and validated with client-side regex fallback in `frontend/js/dashboard.js`:
  1. `שכר` (Stated Salary): Only when explicitly stated in the job ad (`salary_source_type === 'job_ad'`); displays the exact figures. Never model-predicted.
  2. `עבודת שטח` (Field Work): Triggered on hands-on field technician/engineer/maintenance duties. Protected by negative guard (e.g. excludes office-only / "ללא עבודת שטח").
  3. `רכב חברה` (Company Car): Triggered only on company vehicle/attached car. Protected by negative guard (driver license alone never triggers car).
  4. `משמרות 24/7` (24/7 Shifts / NOC): Triggered on explicit 24/7 rotation, night shifts, or 24/7 control room/NOC. Protected by negative guard.
  5. `Junior` (Entry-Level / Beginners): Triggered on 0-2 years experience, "Junior", or entry-level beginner wording. Excludes Senior/lead titles or explicit non-junior requirements.
- **Triage Tabs Parity:** Starred jobs automatically transfer from "חדשות" to "בכוכב", and saved jobs transfer to "נשמרו". Default sort is `date_desc`, ensuring newest jobs are prominently displayed first.

---

## 7. MCP Servers Usage Policy & Operational Protocol

### 7.1 Allowed MCP Servers Table
| MCP Server | System Role | Required Trigger | Operational Restrictions |
| :--- | :--- | :--- | :--- |
| **`tavily`** | Discovery layer: finding new job vacancies on the web and domain mapping. | When searching new postings from target firms (energy, gas, drones, SCADA) or verifying company URLs/domains. | Forbidden for deep scraping of complex portals (use Firecrawl instead); no non-job general searches. |
| **`firecrawl`** | Deep extraction layer: complex career pages (SPA, Comeet, Workday, Greenhouse). | Strictly when a job link fails simple extraction or when heavy JS rendering prevents full requirement parsing. | Forbidden as primary discovery search (credit conservation); execute surgically on single links only, never mass crawl. |
| **`chrome-devtools`** | UI verification: responsive dashboard layout inspection and browser debugging. | When editing or fixing dashboard interface code (`src/ui_builder.py` / `docs/index.html`) or verifying mobile layouts. | Strictly forbidden in unattended automation runs (Cron/Headless); forbidden when task has no UI component. |
| **`github`** | CI/CD monitoring: GitHub Actions run logs, release tracking, version synchronization. | When reporting on failed daily GitHub Actions cron runs, or when checking remote run histories. | Forbidden for redundant calls when required information already exists in the local workspace. |
| **`sequential-thinking`** | Deep logical decomposition: match scoring algorithms and filter debugging. | When upgrading match score logic or debugging complex screening edge cases in `src/evaluators.py`. | Forbidden during routine job evaluation runs (Gemini model handles routine evaluation directly). |
| **`gemini-api-docs`** | Official library documentation: Google Gemini API and SDK references. | Strictly when upgrading `google-genai` SDK code, syntax, or modifying structured JSON output schemas. | Forbidden if connection and schema code is stable and not undergoing syntactic revision. |

### 7.2 Explicit Denylist (Strictly Prohibited)
- **`apify` (Completely Prohibited):** Heavy, expensive, and redundant. Job discovery and extraction are performed with optimal efficiency via Tavily and Firecrawl.
- **`colab-mcp` (Completely Prohibited):** Project execution relies solely on local Python virtual environment (`venv`) and GitHub Actions. Remote cloud notebook sessions are forbidden.

---

## 8. Next Session Priorities & Backlog (To Remind on Session Start)
1. **כיול מודל הערכה (U5 Benchmark Ground-Truth Labeling):**
   - ביצוע תיוג ידני של משרות מגוונות מתוך `data/historical_catalog.json` או `data/weekly_archive.json` לתוך `data/evaluation_benchmark_template.json` (הגדרת תוויות `relevant`, `irrelevant`, `borderline`).
   - הרצת סקריפט ההערכה `python3 scripts/evaluate_dataset.py` להפקת דוח דיוק, Recall, ציון F1 וניתוח פספוסים (False Negatives).
   - עדכון הסטטוס ב-`docs/UPGRADE_STATUS.md` מ-`BLOCKED: user labels` ל-`DONE`.
2. **הרחבת מקורות גיוס ישירים (ATS Connectors):**
   - הוספת מחברי ATS ישירים לחברות אנרגיה, גז ותעשייה מובילות בישראל (דוגמת חברות נוספות המשתמשות ב-Comeet, Greenhouse או Workday), בהמשך למחבר המוצלח של Enlight Renewable Energy.
3. **שיפורי סינון ותצוגה בדשבורד:**
   - המשך כוונון ודיוק של תגיות המשרות וסינוני חיפוש מתקדמים לפי צרכי המשתמש.

## עדכון ביקורת — 26.10.2026

דוח האימות העדכני: [docs/AUDIT_2026-10-26.md](docs/AUDIT_2026-10-26.md). נתונים היסטוריים במסמך זה, כגון מספר בדיקות וגדלי קבצים, אינם תוצאות הריצה הנוכחית.

- נשמרים קטלוג מלא ונתוני מועמד; קובץ פגום עוצר את התהליך במקום לאפס היסטוריה.
- תיאורי מקור מלאים ומטא־נתונים נשמרים. ראיות חסרות או סותרות אינן התאמה מאומתת.
- המקור לממשק נשאר frontend והתוצרים מסונכרנים ל־docs בבנייה.
- התזמון המיועד הוא ראשון–שישי 07:17 ב־Asia/Jerusalem, עם שער קיץ/חורף. GitHub עשוי לעכב משימה מתוזמנת.
- סנכרון פרטי דורש מתאם מאומת; אין PUT גורף לנתיב Firebase משותף.
- לא בוצעו Push, Merge, פריסה, חיפוש חי או משלוח דוא״ל. ההרשאה לעבודה מקומית אינה הרשאה לפעולות אלה.
- מיפוי Antigravity הקיים נשאר במחשב המשתמש; אין לשנות את scope.json לנתיב סביבת הביקורת הזמנית.
