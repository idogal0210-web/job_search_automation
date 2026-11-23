# Autonomous Job Discovery & Career Intelligence Platform
**Multi-Source Ingestion, Calibrated AI Evaluation, Real-Time Cloud Sync & Interactive Web Dashboard**

An autonomous, production-grade career discovery and triage platform engineered for specialized engineering disciplines (Energy, Natural Gas, Solar PV, Battery Storage / BESS, SCADA / Industrial Control, and Unmanned Autonomous Systems / UAVs).

The system continuously crawls and normalizes vacancies across job boards and native ATS APIs, executes deterministic criteria gating and calibrated Google Gemini LLM evaluations, calculates market compensation benchmarks, synchronizes triage states securely across devices via Supabase, and publishes a responsive single-page analytics dashboard.

---

## Key Highlights & Core Capabilities

- **Multi-Source Job Ingestion:** Automated daily collection across LinkedIn, regional job boards, and direct ATS API integrations (Comeet, Greenhouse, Lever, and Ashby) with circuit-breaker resilience and exponential backoff.
- **Deterministic Hard Gates & Statutory Screening:** Immediate pre-evaluation checks enforce geographic commute limits, advertised compensation floors, domain verification, and exclude non-technical or non-applicable roles prior to AI invocation.
- **Calibrated Multi-Model AI Evaluation:** Powered by Google Gemini via structured Pydantic schemas with evidence extraction, scoring candidates objectively on a 0-100 scale, evaluating qualification gaps, and factoring in tiered target company priority bonuses.
- **Evidence-Based Salary Intelligence Engine:** Extracts advertised compensation or estimates market salary bands based on verified industry baselines across specific technical domains.
- **Secure Cloud Synchronization (Supabase PostgreSQL):** Non-destructive Compare-And-Swap (CAS) state synchronization with user authentication and Row-Level Security (RLS), keeping triage records (saved, starred, rejected, and purged) mirrored across mobile and desktop devices.
- **Interactive Single-Page Dashboard:** Glassmorphism UI built with modern CSS Cascade Layers (`@layer base, dashboard`), high-contrast dark and light modes, sector distribution visualization, instant search, and one-click data export.
- **Zero-Emoji & Strict Privacy Standards:** Built under rigorous enterprise standards prohibiting pictorial emojis in code and documentation, with automated secret scans, schema validation, and complete redaction of personal identifiable information.

---

## System Architecture

```text
job_search_automation/
├── main.py                         # Primary orchestration entrypoint (CLI execution)
├── PROJECT_CONTEXT.md              # Architectural context and system specifications
├── TASKS.md                        # Task tracking, milestone verification, and roadmap
├── requirements.txt                # Production dependency declarations
├── requirements-lock.txt           # Deterministic pinned versions for reproducible builds
├── .python-version                 # Environment specification (Python 3.11)
├── .agents/                        # AI agent customization layer
│   ├── rules/                      # System invariant rules (zero-emojis, sync guard, etc.)
│   └── skills/                     # Domain skills (code review, living docs, testing)
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Automated CI test pipeline running on PRs and pushes
│       └── daily_job_search.yml    # Scheduled daily GitHub Actions cron workflow
├── frontend/                       # Source presentation assets (single source of truth)
│   ├── templates/index.html        # Clean semantic dashboard layout template
│   ├── css/dashboard.css           # Modular styling with Cascade Layers and custom design tokens
│   ├── js/dashboard.js             # Client-side reactivity, filtering, and cloud sync logic
│   └── assets/                     # Vector icons, verified company logos, and preview images
├── src/
│   ├── pipeline.py                 # Multi-stage execution pipeline and telemetry
│   ├── fetchers.py                 # Scrapers and crawlers with exponential backoff & CircuitBreaker
│   ├── ats_client.py               # Unified API-first client for Greenhouse, Lever, Ashby, Comeet
│   ├── job_policy.py               # Deterministic filtering: location gating, salary floor, target firms
│   ├── gemini_runtime.py           # Gemini model pool management and structured JSON validation
│   ├── evaluators.py               # Candidate scoring, target company bonus, and evidence auditing
│   ├── salary_engine.py            # Domain-specific compensation estimation and calibration
│   ├── state_manager.py            # Atomic state persistence and duplicate prevention
│   ├── ui_builder.py               # Dashboard compiler ensuring 1:1 parity between frontend/ and docs/
│   ├── url_utils.py                # URL sanitization, canonical ID extraction, and domain guards
│   └── publishers.py               # Structured digest generation and notification delivery
├── docs/                           # Compiled production build served via GitHub Pages
└── tests/                          # Automated unit, integration, and security test suite
```

---

## Data Pipeline & Operational Flow

1. **Ingestion & Deduplication:** Crawls vacancies via direct ATS endpoints and job boards. Unique fingerprints and canonical URLs prevent duplicate evaluations.
2. **Deterministic Hard Gate Screening:**
   - Filters out non-technical roles, entry-level garage tasks, and generic positions.
   - Enforces a geographic commute threshold from central industrial hubs.
   - Disqualifies positions explicitly advertised below statutory compensation thresholds.
3. **Structured AI Evaluation:**
   - Evaluates remaining candidates against specialized engineering criteria.
   - Extracts concrete evidence for core requirements and identifies qualification gaps.
   - Assigns a calibrated match score (0-100) and applies tiered target company bonuses.
4. **Compensation Engine:**
   - Detects advertised salary ranges directly from listing text.
   - Calibrates role estimates against domain baselines when compensation is unlisted.
5. **Atomic State & Cloud Persistence:**
   - Persists triage decisions atomically using temporary files and safe replacements.
   - Synchronizes triage changes to Supabase via authenticated CAS endpoints.
6. **Web Dashboard Compilation:**
   - Compiles static datasets into a deployment-ready web dashboard served via GitHub Pages.

---

## Getting Started & Installation

### Prerequisites
- Python 3.11+
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/idogal0210-web/job_search_automation.git
cd job_search_automation

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies from locked specification
pip install --upgrade pip
pip install -r requirements-lock.txt
```

### Environment Configuration
Create a `.env` file in the root directory (never commit this file to version control):
```bash
# Google Gemini API key for structured evaluations
GEMINI_API_KEY="your-gemini-api-key"

# Optional: Preferred model hierarchy fallback order
GEMINI_MODELS="gemini-3.8-flash,gemini-3.5-flash-lite,gemini-3.5-flash"

# Optional: Supabase configuration for cloud triage synchronization
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_KEY="your-publishable-key"

# Optional: Email notification settings
SENDER_EMAIL="your-notification-sender@example.com"
SENDER_APP_PASSWORD="your-secure-app-password"
RECIPIENT_EMAIL="your-recipient@example.com"
```

### Running the System
```bash
# Execute the full pipeline (ingest, filter, evaluate, and build dashboard)
python3 main.py

# Recompile the frontend source into docs/ distribution
python3 src/ui_builder.py

# Run inactive job scanner
python3 scripts/scan_inactive_jobs.py
```

---

## Quality Gate & Verification

The project enforces deterministic automated verification across all changes:

```bash
# 1. Run comprehensive unit and integration test suite
python3 -m unittest discover -s tests -p "test_*.py"

# 2. Verify zero-emoji compliance across code, comments, and documentation
python3 scripts/validate_zero_emoji.py

# 3. Verify clean working tree, valid schemas, and absence of secrets
python3 scripts/project_hygiene.py --check-secrets --validate

# 4. Verify strict 1:1 byte parity between frontend source and docs distribution
python3 tests/test_template_docs_sync.py

# 5. Check client-side JavaScript syntax
node -c frontend/js/dashboard.js docs/dashboard.js
```

---

## Engineering Standards & Privacy Invariants

- **Zero Pictorial Emojis:** Strict invariant prohibiting pictorial Unicode emojis and Dingbats across all code, tests, documentation, and commits in favor of clean typographic indicators (`[OK]`, `[FAILED]`, `[INFO]`) and SVG vector icons.
- **Privacy & Secret Redaction:** Automated pre-commit scans inspect the working tree for secrets, credentials, and exposed tokens before every commit. No personal phone numbers, home addresses, or sensitive credentials are stored in repository files.
- **Dual-Template Sync Guard:** All UI development takes place strictly within `frontend/`. Compiled assets in `docs/` are derived deterministically through `src/ui_builder.py` with automated parity checks.
- **Fault-Tolerant Persistence:** State operations utilize atomic file swaps (`os.replace`) to prevent database corruption during sudden termination or network drops.
