# PROJECT_CONTEXT.md

## 1. Project Overview & Goal
- **Product Purpose:** Autonomous job search, evaluation, salary prediction, and triage platform developed for Ido Gal.
- **Core Problem Solved:** Eliminates noise from non-technical, administrative, and irrelevant listings by executing deterministic pre-filtering followed by structured Gemini LLM evaluation and salary benchmarking.
- **Target Audience & Profile:** Ido Gal, a certified practical mechanical engineer (הנדסאי מכונות מוסמך) specializing in solar energy (PV & BESS site management, commissioning, QA inspection), natural gas, SCADA/PLC control systems, and UAV/drone operations across Israel. Primary search target calibrated (Nov 2026): Junior/Mid-Entry Solar Site Management, BESS Commissioning, CleanTech startups with training potential, strict 24/7 shift disqualification, and non-energy SCADA filtering.

---

## 2. Tech Stack & Environment
- **Runtime & Backend:** Python 3.9+ / Python 3.14 (core pipeline, fetchers, evaluators, salary engine, unit test suite).
- **Frontend & Dashboard:** Pure Vanilla HTML5, Modern CSS3 (CSS Grid, Flexbox, CSS Variables, Glassmorphism canvas and card surfaces with nested-radius law and 3-tier control heights, CSS Cascade Layers `@layer base, dashboard, studio`), ES6+ JavaScript (Zero-framework, single-page application).
- **AI & LLM Services:** Google Gemini API via official `google-genai` SDK (`GeminiPool` utilizing `gemini-3.8-flash`, `gemini-3.5-flash-lite`, and `gemini-3.5-flash` with strict Pydantic JSON schema enforcement; Groq API is completely decommissioned and removed).
- **Client Libraries & Icons:** Phosphor Icons (vector SVG web font), Chart.js (sector distribution visualization).
- **Scraping & Data Extraction:** BeautifulSoup4, Requests, Urllib (custom User-Agent spoofing, exponential backoff, rate limiting).
- **Storage & State:** Flat atomic JSON files under `data/` (`jobs_state.json`, `weekly_archive.json`, `historical_catalog.json`, `evaluation_state.json`), Browser LocalStorage for client-side user triage state, and Supabase Cloud Database (PostgreSQL with RLS limited to the authenticated owner email via Supabase Auth email/password login, and REST API, project `wvwdxpttwsrdbvvtiyoh`) for real-time bi-directional triage sync between desktop and mobile devices.
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
├── DESIGN.md                       # Single source of truth visual style reference (tokens, components, layout, agent prompt guide)
├── requirements.txt                # Python package dependencies
├── requirements-lock.txt           # Exact pinned dependencies for reproducible builds
├── .python-version                 # Target Python runtime anchor (Python 3.11 / 3.9+)
├── AGENTS.md                        # Official Google Antigravity project root rules and mission specification
├── .agents/                        # Operational policies and domain skills
│   ├── rules/                      # System rules (always_on: zero-emojis.md, pre-push-verification-and-living-docs.md, single-source-and-replaceability-guard.md, critical-thinking-quality.md; model_decision: mcp-policy.md, project-tree-display.md; glob: dual-template-sync-guard.md, supabase-state-integrity-guard.md, ui-invariants-symmetry-guard.md, realism-grounding.md, scoped CV policies)
│   └── skills/                     # Specialized project skills (salary-intelligence, ui-review, cv-tailor, ai-quality-evaluation, etc.)
├── .github/
│   └── workflows/
│       ├── ci.yml                  # Continuous integration: test suite, UI build check, zero emoji guard on PRs
│       └── daily_job_search.yml    # Active scheduled daily GitHub Actions cron workflow (07:17 IST / 04:17 UTC)
├── frontend/                       # Source files for the web application (modular separation)
│   ├── templates/index.html        # HTML layout shell and metadata slots
│   ├── templates/email_report.html # Externalized HTML email digest template
│   ├── css/dashboard.css           # Modular dashboard CSS styles
│   ├── css/ui-fixes.css            # Specialized UI/BiDi/dark-mode fixes stylesheet
│   ├── js/dashboard.js             # Client-side SPA application logic and data fetcher
│   ├── js/ui-fixes.js              # Client-side UI, BiDi, and auto-fix runtime script
│   ├── data/studio_profile.json    # Tracked non-PII excluded employers config synced to Career Studio UI
│   ├── data/career_studio_profile.json # Unified Career Studio profile schema (candidate facts, roles, STAR stories, exclusions)
│   └── assets/                     # Local static assets and company logos
├── prompts/                        # Versioned LLM prompts extracted from code
│   ├── job_evaluation_v1.txt       # Core job evaluation structured prompt
│   ├── cv_analysis_v1.txt          # CV gap analysis prompt
│   └── cv_generation_v1.txt        # CV tailoring generator prompt
├── src/
│   ├── pipeline.py                 # Core orchestration pipeline managing run health, stages, and metrics
│   ├── config.py                   # Centralized configuration loader (keywords, aliases, thresholds, ats_boards)
│   ├── prompts.py                  # Prompt template loader with caching
│   ├── ats_client.py               # Shared direct ATS API client (Greenhouse, Lever, Ashby, Comeet) for API-first lookup & inactive checks
│   ├── fetchers.py                 # Multi-source scrapers with JobFetcher registry & CircuitBreaker (LinkedIn, Drushim, Comeet, Greenhouse, Lever)
│   ├── job_policy.py               # Deterministic blacklist filters, technical keyword sets, and title rules
│   ├── gemini_runtime.py           # Multi-model Gemini fallback pool with structured output validation and retry
│   ├── evaluators.py               # Match score evaluator (0-100), target company bonuses, and keyword fallback
│   ├── salary_engine.py            # Evidence-based salary prediction, comparable role calibration, confidence scoring
│   ├── state_manager.py            # Job deduplication, status tracking (QUALIFIED/DISQUALIFIED/RETRY_PENDING), storage
│   ├── supabase_feedback.py        # Few-Shot feedback loop engine retrieving triage history from Supabase/local sync for LLM calibration
│   ├── ui_builder.py               # Build orchestrator compiling frontend/ assets and data into docs/
│   ├── url_guard.py                # Shared anti-SSRF guard (is_global IP check, redirect re-validation, peer verification)
│   ├── company_matcher.py          # Normalized quote-unified word-boundary company & employer blacklist matcher
│   ├── closure_signatures.json     # Canonical job closure signature definitions shared by Python scanner and Cloudflare Worker
│   ├── url_utils.py                # URL validation, normalization, and sanitization
│   └── publishers.py               # Email dispatch and notification services
├── docs/
│   ├── PRD.md                      # מסמך אפיון מובנה של 37 הסעיפים התקניים (Single Source of Truth לדרישות ולקוד)
│   ├── decisions/                  # יומן החלטות ארכיטקטורה ומוצר (Architecture Decision Records)
│   │   └── template-decision.md    # תבנית מסמך החלטה מאושרת לפי פרוטוקול ההחלטות
│   ├── index.html                  # Lightweight production SPA shell (~31KB) hosted on GitHub Pages
│   ├── dashboard.css               # Compiled dashboard styles
│   ├── ui-fixes.css                # Specialized UI/BiDi/dark-mode fixes stylesheet
│   ├── dashboard.js                # Compiled application script
│   ├── ui-fixes.js                 # Client-side UI, BiDi, and auto-fix runtime script
│   ├── theme.css                   # Global design tokens, color variables, and base responsive styles
│   ├── fonts.css                   # Local font declarations
│   ├── data/
│   │   ├── jobs.json               # Current jobs payload (schema version 2.0.0, UI-compacted)
│   │   └── historical_catalog.json # Historical catalog for on-demand lazy lookup
│   ├── UPGRADE_STATUS.md           # Upgrade implementation tracking matrix for tasks U1-U7
│   ├── AUDIT_2026-10-26.md         # Comprehensive local audit and integration verification report
│   ├── assets/                     # Static UI assets, fonts, and local company logos
│   └── archive/                    # Archived planning specifications and historical declarations
├── data/
│   ├── jobs_state.json             # Active tracked job identifiers and links
│   ├── weekly_archive.json         # Complete weekly archive containing full metadata, AI scores, and salary data
│   ├── historical_catalog.json     # Historical job catalog for cross-cycle deduplication
│   ├── evaluation_state.json       # Evaluation cache and retry pending queues
│   └── evaluation_benchmark_template.json # Benchmark schema and ground-truth dataset template
├── tools/                          # Standalone modular tooling
│   └── cv_tailor/                  # Fact-based CV tailoring and interview prep engine
├── tests/                          # Automated unit and integration test suite (229 passing Python tests)
│   ├── test_supabase_feedback_loop.py # Few-Shot dynamic prompt feedback loop & Supabase/local triage sync tests
│   ├── test_strict_ai_gate_and_prioritization.py # Strict AI-only gate & new job prioritization over retry queues
│   ├── test_career_studio_v3_flow.py # Career Studio v3.0 4-step workflow, layout invariants & STAR simulator tests
│   ├── test_studio_bridge.py       # Unified Career Studio HTTP bridge, schema, SSRF, blacklist & generator tests
│   ├── test_studio_bridge_security.py # Bridge Origin/Host/Token/Content-Length & URL guard SSRF/redirect tests
│   ├── test_phase0_phase2_security.py # Client PII redaction, Supabase CAS/RLS, XSS onclick & SRI verification tests
│   ├── test_phase3_to_5_regressions.py # 30-page HTML closure corpus, company word-boundary matching, hygiene, stratified eval & email outbox tests
│   ├── test_template_docs_sync.py  # 1:1 dual-template synchronization guard between frontend/ and docs/
│   ├── test_recovery.py            # Degradation and error recovery tests
│   ├── test_salary_intelligence.py # Salary prediction engine tests
│   ├── test_requeue.py             # Evaluation requeue and retry tests
│   ├── test_main_integration.py    # Pipeline integration tests
│   ├── test_evidence_assessments.py# Requirement assessments & evidence validation tests
│   ├── test_benchmark_metrics.py   # Benchmark dataset evaluation tests
│   ├── test_comeet_connector.py    # Direct Comeet ATS connector tests
│   ├── test_ats_connectors.py      # Multi-provider ATS connectors, CircuitBreaker, API-first Career Studio scraper & inactive check tests
│   ├── test_cv_tailor.py           # CV Tailor engine verification tests
│   ├── test_phase_b_precision.py   # AI evaluation precision and schema tests
│   └── test_reliability_phase_a.py # Scraper and fallback reliability tests
└── scripts/
    ├── studio_bridge.py            # Loopback HTTP bridge connecting Career Studio UI to tools/cv_tailor and GeminiPool
    ├── evaluate_dataset.py         # Confusion matrix, Precision/Recall/F1 and False Negatives evaluator
    ├── requeue_jobs.py             # Utility script for re-evaluating pending or cached jobs
    ├── project_hygiene.py          # Project integrity, secret scanning, and deterministic hygiene cleanup
    ├── validate_zero_emoji.py      # Zero-emoji enforcement scanner
    ├── inspect_state.py            # Compact CLI state inspection utility
    └── scan_inactive_jobs.py       # Automated detection of closed/expired job postings (HTTP 404/410 and closed notices)
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
   ↓ Dispatches HTML email digest if qualified jobs are found (calibrated via is_incomplete_run: transient keyword retries do not trigger '[חלקי]' status)
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
- `priority_bonus`: Integer (+10 bonus for Tier 1 target employers, +5 bonus for Tier 2 target employers, capped at 100, applied when base_match_score >= 75).
- `concrete_matches_count`: Integer (count of confirmed technical requirement matches).
- `reasoning`: String (concise Hebrew explanation of evaluation rationale).
- `salary_min`: Integer (predicted minimum monthly gross compensation in ILS).
- `salary_max`: Integer (predicted maximum monthly gross compensation in ILS).
- `salary_confidence`: String (`HIGH`, `MEDIUM`, `LOW`, `NONE`).
- `salary_benchmark_source`: String (reference market evidence or role comparable).

### 4.3 Target Employers Strategy (75 Companies & Tiered Priority Bonus Model)
- **Sector Coverage (75 Companies Across 5 Key Domains, 15 per Sector):**
  1. *Solar & CleanTech (סולאר וקלינטק):* Enlight Renewable Energy, SolarEdge Technologies, Doral Group, Energix Renewable Energies, Nofar Energy, Shikun & Binui Energy, EDF Renewables Israel, Meshulam Levinstein, Afcon Solar, Brenmiller Energy, Baran Group, Electra Energy, Ormat Technologies, Solegreen, GenCell.
  2. *Natural Gas & Energy Systems (גז טבעי ומערכות אנרגיה):* Supergas Energy, Paz Oil Company, Delek Israel, Sonol Israel, Dor Alon Energy, Israel Natural Gas Lines (INGL), OPC Energy, Dorad Energy, Dalia Power Energies, Rapac Energy, Shapir Energy, Ashtrom Energy, Shafir Engineering, Ludan Group, Meptagon.
  3. *SCADA/PLC & Industrial Automation (בקרה תעשייתית, SCADA ו-PLC):* mPrest Systems, Afcon Control & Automation, Contel Technologies, Baran Automation, Elspec Engineering, Unitronics, Tadiran Holdings, Schneider Electric Israel, Siemens Israel, ABB Israel, YSB Group, Danel Group, Galil Engineering, Agan Engineering, Mashav.
  4. *Drones & Defense Operations (רחפנים, כטב"ם ומערכות ביטחוניות):* Percepto, XTEND, D-Fend Solutions, Aerostar / Aeronautics, Elbit Systems, Israel Aerospace Industries (IAI), Rafael Advanced Defense Systems, BlueBird Aero Systems, Heven Drones, Steadicopter, High Lander, FlyTech, CopterPIX, Airobotics / Ondas, SpearUAV.
  5. *High-Tech Energy & Mobility (הייטק אנרגיה, אגירה ותחבורה חכמה):* Augury, Driivz, StoreDot, Electreon Wireless, Chakratec, Phinergy, EV-Edge, Zooz Power, BladeRanger, Brenmiller, RayZone Group, Thermal Energy Systems, Nostromo Energy, Apollo Power, SolarPaint.
- **Tiered Priority Bonus Architecture:**
  - *Tier 1 Target Employers (Ranks 1-5 per sector, 25 companies total):* Granted `+10` priority bonus points when AI base score evaluates at `base_match_score >= 65`.
  - *Tier 2 Target Employers (Ranks 6-15 per sector, 50 companies total):* Granted `+5` priority bonus points when AI base score evaluates at `base_match_score >= 65`.
  - *Cap & Ceiling:* Match score is strictly capped at `100`. Ineligible roles (`< 65`) receive `+0` bonus.
- **Batched Company-Centric Querying (`main.get_target_company_queries`):**
  - Formulates 5-company Boolean batches `("CompA" OR "CompB" OR ...)` generating 15 LinkedIn queries covering all 75 companies.
  - Mitigates rate limiting and request overhead compared to querying 75 single company URLs while ensuring complete employer coverage.

---

## 5. Implementation Status

### 5.1 Functional Components (Done)
- **Multi-source automated scrapers:** Working scrapers for LinkedIn (Energy, Drones), Drushim (Industry, Energy, Operations), and config-driven direct ATS connectors (10 verified boards across 3 ATS systems: `Comeet`: Enlight, Driivz, Percepto, XTEND, mPrest, SolarEdge Technologies, BIRD Aerosystems; `Greenhouse`: Augury, Electreon; `Lever`: D-Fend Solutions) guarded by `CircuitBreaker`. Decommissioned Indeed and Glassdoor due to persistent anti-bot gating.
- **Deterministic zero-token filter:** Instant regex-based rejection of non-technical roles (accounting, HR, sales, legal) and blacklisted operators (Chevron, Energean, INGL).
- **Structured Gemini LLM evaluation:** Multi-model pool with Pydantic JSON schemas, automatic backoff, jitter, and quota error isolation.
- **Evidence-based salary engine:** Predicts salary brackets and confidence scores based on sector benchmarks and role equivalencies.
- **Crash-resilient persistence:** Atomic file updates preventing corruption during execution interruptions.
- **Interactive multi-view web dashboard:**
  - View modes: Grid (Cubes) and List (Compact single-column).
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
- **Career Studio v3.0 Ground-Up Rebuild (TASK-98, `docs/CAREER_STUDIO_V3_SPEC.md`):**
  - App Switcher & Symmetrical Header Strip: Seamless mode switching between Job Radar and Career Studio with bidirectional `#studio` hash routing. Unified `.studio-context-bar` with active vacancy selector (`#atsJobSelector`), 4-step progressive navigation bar (`#studioStepItem1` through `#studioStepItem4`), dynamic ATS match indicator, and CV switch button.
  - Contextual 55/45 Responsive Split-Screen: Desktop (`>= 1120px`) runs a 55/45 split (`.studio-split-grid`) with right interactive work column (`#studioWorkColumn`) and contextual left side column (`#studioSideColumn`). In Steps 1-2, the side column displays the Live Editable A4 preview card (`#studioA4PreviewCard`); in Steps 3-4, it automatically swaps to the Job Brief Card (`#studioJobBriefCard`) for instant reference to role requirements. For mobile (`< 1120px`), side preview opens dynamically inside `<dialog id="studioMobilePreviewDialog">` with dual wraps (`#studioMobileA4Wrap` and `#studioMobileJobBriefWrap`) and guaranteed `>= 44x44px` touch targets with zero horizontal overflow.
  - 4-Stage Progressive Pipeline:
    1. *Step 1 — Focus & Hard Gates (`#studioPaneStep1`):* Folded statutory hard gates (`#studioPassedGatesAccordion`), graded match gaps from `/api/ats/analyze` or local fallback, and forward CTA to Step 2.
    2. *Step 2 — Keywords & A4 Tailoring (`#studioPaneStep2`):* Missing keywords injection chips, line-by-line enhancer, live editable A4 paper sheet (`#studioLiveA4Sheet`), and print/PDF export.
    3. *Step 3 — LinkedIn & Application Kit (`#studioPaneStep3`):* Tailored Headline, About, and Skills pills with 1-click copy-to-clipboard, recruiter outreach message card, direct apply link with state tracking, and forward CTA to Step 4.
    4. *Step 4 — STAR Interview Simulator (`#studioPaneStep4`):* Domain-tailored question bank covering 6 sectors (Energy, Solar/BESS, Gas, SCADA, UAV, PM), structured answer textarea with sample outline loader, "Check Answer" evaluation with `studio_bridge.py` API integration and local fallback, 4-card S/T/A/R scoring grid, and golden answer tips.
  - Testing & Verification: Dedicated unit test suite `tests/test_career_studio_v3_flow.py` (5 tests passing in 3.3s), all 217 unit tests passing in 11.7s, zero emojis confirmed (`scripts/validate_zero_emoji.py`), clean secrets and hygiene (`scripts/project_hygiene.py --check-secrets --validate`), clean JavaScript syntax check (`node -c`), and 100% 1:1 dual-template parity verified.
  - Design Tokens, Light/Dark Mode, Responsive Container & Interaction Parity (`TASK-39`, `TASK-41`, `TASK-53`, `TASK-72`, `TASK-73`): Organized `frontend/css/dashboard.css` into `@layer base, dashboard, studio;`, implemented WCAG AA (>= 4.5:1) Light (`#F8FAFC` canvas, `#FFFFFF` surface, `#0F172A` text, `#0369A1` accent) and Dark (`#0B0F19` canvas, `#131B2E` surface, `#F8FAFC` text, `#38BDF8` accent) design tokens with complete light-mode container overrides (`.studio-context-bar`, `.studio-target-bar`, `.studio-live-doc-viewer`, `.writer-audit-text`), `@container studio-main` 2-column layouts (`>= 640px`), sticky job bar containment, zero hardcoded dark styling in light mode, and removed competitor brand names (`Jobscan`, `Teal`, `Resume Worded`) from UI templates. Neutralized Phosphor Duotone RTL `-1em` margin drift on `:after` across all interactive buttons/chips, normalized label/summary horizontal flex alignment, expanded header progress info to 135px preventing text collisions, and added RTL select padding for native dropdown arrows (`TASK-41`, `TASK-53`).
  - Unified Single-Source Profile & Blacklist Guard: `frontend/data/career_studio_profile.json` (version 2.0.0, synchronized 1:1 to `docs/career/career_studio_profile.json`) is the canonical primary Single Source of Truth for Ido Gal's verified candidate profile, roles, technical skills, and STAR stories catalog across both the web dashboard and `tools/cv_tailor` (`load_base_profile()` and `load_candidate_profile_data()` with automatic markdown serialization and headless CI template fallback), while non-PII `excluded_employers` compile deterministically into `docs/career/studio_profile.json`.
  - 3-Tier Gap Severity Engine & Junior PM Realism Grounding (TASK-79): Implemented structured gap severity classification (`AtsCategorizedGap` in `src/gemini_runtime.py`, `tools/cv_tailor/src/analyzer.py`, and `prompts/cv_analysis_v1.txt`) categorizing requirements into `blocking` (unbridgeable statutory/licensing gaps), `important` (bridgeable operational gaps), and `nice_to_have`, displayed directly in Career Studio with 1-click writer injection. Upgraded `prompts/cv_generation_v1.txt` with `{lang_instruction}` support and dedicated Junior Project Manager / Coordinator guidance highlighting schedule tracking, contractor/vendor coordination, operational shift control (Energean), and combat team leadership (Sayeret Nahal) while strictly locking all 5 original role titles with zero credential fabrication.
  - Loopback AI Bridge (`scripts/studio_bridge.py` on `127.0.0.1:8765`): Wraps `tools/cv_tailor/src/` (`scraper.py`, `researcher.py`, `analyzer.py`, `generator.py`) and Pydantic-validated `GeminiPool` schemas (`AtsStudioAnalysisSchema`, `TailoredCvPackageSchema`, `CvTailoredBulletSchema`, `StarInterviewEvaluationSchema`) with strict Origin enforcement on `POST`, per-process `X-Studio-Token` authentication (`hmac.compare_digest` via `/api/session`), loopback `Host` header validation against DNS rebinding, strict `Content-Length` bounds `[0, 1MiB]`, and `src/url_guard.py` anti-SSRF redirect/peer verification, saving tailored packages to `tools/cv_tailor/output/` while falling back transparently to client-side local matching when offline.
  - Client Privacy & XSS Hardening: Removed personal phone/email/military/employer PII from client bundles (`CANONICAL_CV_PROFILE`, `ORIGINAL_CV_SUMMARY_TEXT`, and static `cv_he.html`/`cv_en.html`), dynamically hydrating `CANONICAL_CV_PROFILE` in memory only when authenticated against `/api/profile`; moved uploaded CV storage from `localStorage` to `sessionStorage`; hardened all dynamic `onclick` attributes with `escapeHtml(JSON.stringify(...))` and `sanitizeUrl` with `new URL()` protocol allowlisting; SRI on Chart.js and on-demand lazy loading for `pdf.js`/`mammoth`.
  - Interactive Clarifications, Review & A4 PDF Export: Supports URL ingestion, interactive pre-generation clarification questions, safe DOM Markdown preview, unmatched requirements alerts, applied bullet carry-over, and A4 `@page` print/PDF export.
  - Honest Interview & Anonymizer Modules: Real browser `SpeechRecognition` guard (zero fabricated voice transcripts), Gemini STAR evaluation + `LocalStorage` practice history when connected, and `base_profile.md`-derived anonymization.
- **Neo-Job Board Architecture & Pastel Cards System (TASK-70):** Redesigned the primary job radar dashboard based on reference screenshot analysis (`ui-from-screenshot`). Implemented: 1) `.search-capsule-ribbon`: dark translucent floating search and filter capsule bar for keyword search, geographic region, technical sector, sort order, and modal triggers; 2) `.radar-split-layout`: 2-column desktop layout featuring a 300px sidebar with the dark obsidian Copilot card (`.copilot-promo-card`), sector distribution chart (`#sectorChart`), and contextual action bars alongside the responsive main content area; 3) 3-column responsive grid (`#cardsContainer`) with 6 rotating soft pastel card themes (`.card-pastel-peach`, `.card-pastel-mint`, `.card-pastel-lavender`, `.card-pastel-sky`, `.card-pastel-rose`, `.card-pastel-slate`) with adaptive high-contrast dark-mode support; 4) Modern 20px rounded card anatomy with floating date pills (`.card-date-pill`), verified company logos with smooth error fallback to clean typography, soft tag pills, BiDi-isolated salary & location block, and black `Details` pill CTA (`.btn-details-pill`) wired to `openJobModal(id)`. Dual-template parity preserved.
- **GitOps Save & Sync protocol:** Unified zero-waste cleanup (purged obsolete `integration/` templates and caches), syntax validation, pre-commit secret scanning, zero-emoji verification, and two-way GitHub push.
- **Streamlined header UI (TASK-55):** Scaled down Brand headline typography (`clamp(0.85rem, 0.82rem + 0.15vw, 0.95rem)`), subtitle (`0.74rem`), and circle icon (38px / 18px Phosphor briefcase); removed theme toggle button (`#themeToggleBtn`) and locked runtime permanently to 'dark'; modernized cloud button (`#headerCloudBtn` / `.header-cloud-btn`) into a compact icon-only pill (28px height, Phosphor cloud icon, status dot); downscaled mode switcher controls (`לוח משרות`, `סטודיו קריירה`) to compact 35px height, 13px font size; and optimized category stat tab buttons (`.stat-cube-btn`) to 52px min-width, 4px 6px padding, 6px gap, completely eliminating horizontal container overflow and ensuring all 4 tabs sit comfortably inside the header boundary across dual templates (`frontend/` -> `docs/`).
- **Career Studio Ergonomic Modernization (TASK-56):** Reclaimed ~300px of vertical viewport height by streamlining `.studio-sticky-job-bar` (44px) and `.studio-context-bar` (44px compact input grid), closing `.studio-job-details-accordion` by default, and converting `.studio-subnav-pipeline` into a sleek single-row tab strip (40px, hiding multi-line descriptions); refactored ATS Score & KPI row (`.ats-kpi-row`) from a massive 120px circular gauge into a compact, low-noise horizontal card (58px gauge, 16px font, 52px KPI ribbon); softened visual glare and contrast in the sticky live A4 preview card (`.studio-sticky-preview-card`) by replacing bright cyan borders with subtle 1px glass outlines (`rgba(255, 255, 255, 0.08)`). Dual-template parity preserved.
- **Streamlined Contextual Action Buttons & Chart Chip Stabilization (TASK-97):** Relocated contextual actions from heavy sidebar action bars below the sector chart to elegant pill buttons (`.btn-action-pill`) inside `.cards-view-header` next to the jobs count summary, matching standard web dashboard patterns. Replaced verbose labels with concise 2-word labels with duotone icons (`ייצוא לאקסל` and `מחיקה ואיפוס`) with tailored Dark and Light mode theme tokens. Enforced `white-space: nowrap !important;` across `.dashboard-chip` and `#chartChip`, preventing multiline wrapping of `משרות` in the sector distribution card. Dual-template parity preserved.
- **Cloud Sync (Supabase only):** The dashboard header holds a single minimal pill (`#headerCloudBtn`) opening `#cloudModal` (email/password sign-in, sign-out; public self-signup disabled). Triage state (starred, saved, rejected, purged) syncs between desktop and phone exclusively through the Supabase `sync_state` table under owner-only `user_id = (select auth.uid())` RLS (`supabase/migrations/20261109222817_create_sync_state.sql` and `supabase/migrations/20261115011000_harden_sync_state_cas_and_rls.sql`) using true Compare-And-Swap (`PATCH` with `Prefer: return=representation` and automatic conflict reconciliation + retry). All active job multi-identifiers (`link`, canonical ID, and `content_hash`) are guarded against accidental purge masking; sign-in triggers authoritative remote mirroring (`fetchCloudSync(true)`) with version-bump reconciliation (version 15). No GitHub tokens, share links or static `sync_state.json` fallback exist client-side; `docs/data/sync_state.json` is no longer published. The page embeds only the Supabase URL and publishable key. Manual job-search runs are triggered from GitHub Actions directly.
- **Streamlined 3-Anchor Job Card Architecture (Option 1):** Replaced 5 repetitive and verbose sub-categories across job cards and full modal dialogs with 3 concise, high-signal information anchors: 1) `תחום ותפקיד` (intelligent unification of domain and role summary), 2) `דרישות סף` (concise core requirements), and 3) `התאמה ופערים` (punchy candidate strengths with explicit `[OK] ללא פערי סף` or `[פער]` status badge). Evaluation prompt sharpened to 1-sentence responses, eliminating ~65% of redundant text. Modernized with 8px rounded-md badges, deep emerald score/salary tints, recessed requirements container with relaxed 1.5 line-height, and real-time RTL edge indicator stripes on Career Studio hard gates (TASK-52). Dual-template parity preserved.
- **Automated Inactive Jobs Detection & Zero-Worker Architecture:** Integrated scheduled daily detection of expired/closed postings via `scripts/scan_inactive_jobs.py` running in `.github/workflows/daily_job_search.yml` and publishing to `docs/data/inactive_jobs.json`, enhanced with direct ATS API verification (`src/ats_client.py`) alongside HTML/JSON-LD checks. Replaced unreliable external Cloudflare Worker proxy with direct static JSON consumption in `#inactiveJobsModal`. Enriched UI with header count badge `#inactiveJobsCountBadge`, closed warning chips on job cards in `renderCards()`, warning banners in job modals, and 1-click bulk removal (`handleRemoveAllInactiveJobs`) that syncs instantly to Supabase.
- **API-First ATS Integration (`src/ats_client.py`):** Unified direct ATS URL parsing and JSON extraction across `tools/cv_tailor/src/scraper.py` (Tier 1 API-first before Firecrawl credits), `src/pipeline.py` (`enrich`), and `scripts/scan_inactive_jobs.py`, plus deterministic `gh_`/`lever_`/`ashby_` job IDs in `src/url_utils.py`. Native Python HTTP/JSON connectors bypass external browser automation and conserve credits.
- **Modern Web Platform Standards (Modern Web Guidance):** 1) Native scrollbar standardization: applied standard CSS `scrollbar-color` and `scrollbar-width` (`thin` and `none`) with WebKit `@supports not` fallbacks in `dashboard.css`, fully eliminating legacy vendor warnings; 2) Subresource Integrity (SRI) & CORS: added `integrity="sha384-..."`, `crossorigin="anonymous"`, and `referrerpolicy="no-referrer"` across all version-pinned external CDN assets (Phosphor Icons, Chart.js, PDF.js, Mammoth.js) in `frontend/templates/index.html` and `docs/index.html`; 3) Native `<dialog>` light-dismiss: implemented universal backdrop click dismissal across modal dialogs (`#cloudModal`, `#studioGlossaryDialog`, `#studioExportDialog`, `#studioMobilePreviewDialog`); verified via `modern-web-guidance legacy-scan` (0 findings across 35 rules).
- **Target Companies 46 Refinement & Core Brain Policy (TASK-78):** Refined target employers from 75 to 46 focus companies across 2 core sectors — Tier 1 (32 energy, solar, BESS & gas infrastructure firms, +10 bonus) and Tier 2 (14 drones/UAV firms, +5 bonus). Added proactive Junior Project Manager, Assistant PM, and Coordinator search queries with domain anchor protection against non-technical PM leaks. Enforced deterministic ~45-50 min commute radius from Tel Aviv (`location_out_of_range`), raised advertised salary floor to 16,000 ILS/mo (`below_salary_floor`), raised quality threshold to 75+, and fixed line 199 `RETRY_PENDING` infinite loop by cleanly separating statutory blockers (`DISQUALIFIED`) from flexible experience gaps (`QUALIFIED` with `fit_gaps`).
- **Target Companies 75 Expansion & Batched Collection:** Expanded target employers from 50 to 75 companies across 5 technical sectors (Solar, Natural Gas, SCADA, Drones, High-Tech Energy & Mobility, 15 per sector) ranked by growth and recruitment velocity. Calibrated tiered priority bonus (+10 for Tier 1 ranks 1-5, +5 for Tier 2 ranks 6-15, capped at 100, applied when base match >= 65). Implemented batched LinkedIn collection via 5-company Boolean queries `("CompA" OR "CompB" ...)` reducing 75 queries to 15 network requests with zero rate-limit collisions.

- **Few-Shot Feedback Loop & Dynamic Prompt Calibration (TASK-100):** Built `src/supabase_feedback.py` enabling closed-loop active learning from user triage feedback. Safely retrieves the latest 5 starred and 5 rejected jobs from Supabase `public.sync_state` via REST API with graceful degradation to local `data/sync_state.json` (zero hard crashes in CI/offline environments without credentials). Resolves job metadata from `data/historical_catalog.json` or `data/weekly_archive.json` with strict PII filtering (no user notes/IDs) and length bounding (<= 1,200 chars). Dynamically injects `{few_shot_context}` into `prompts/job_evaluation_v1.txt` during evaluation in `src/evaluators.py` and `src/pipeline.py` to continuously align GeminiPool scoring with real candidate preferences. Verified with dedicated test suite `tests/test_supabase_feedback_loop.py` (6 tests).
- **Target ATS Connectors Expansion (10 Boards, TASK-100):** Systematically probed all 46 target employers across Comeet, Greenhouse, Lever, and Ashby APIs. Empirically validated and onboarded 2 new public Comeet boards: SolarEdge Technologies (`solaredge`, 92 live positions) and BIRD Aerosystems (`birdaero`, 18 live positions). Updated `search-preferences.json`, `src/config.py`, `src/fetchers.py` logo pipeline, and added integration tests in `tests/test_ats_connectors.py` (now 10 active direct ATS boards across Comeet, Greenhouse, and Lever).
- **AutoJob Brand Identity & Wordmark Header Integration (TASK-101):** Established official platform branding by replacing the legacy monogram title ("IG | בקרת משרות") with the "AutoJob" wordmark in the top navigation header (`frontend/templates/index.html` -> `docs/index.html`). Implemented with strict LTR isolation (`dir="ltr"`, `aria-label="AutoJob"`) to prevent BiDi text flipping in RTL Hebrew layouts, and responsive Plus Jakarta Sans typography (weight 900) with dark-mode cyan-emerald gradients and WCAG AA compliant light-mode contrast. Onboarded scalable production SVG vector assets (`autojob_logo.svg` and `autojob_icon.svg`) to `frontend/assets/images/` and `docs/assets/images/`.
- **UI Review Remediation — Stray Dot Pinning, Brand Icon Contrast & Utility Action Divider (TASK-102):** Anchored `.sync-status-dot` strictly inside `.cloud-pill.header-cloud-btn` (`position: relative; height: 28px;`) at `top: 3px; left: 3px; width: 6px; height: 6px;` to eliminate stray dots at the viewport top-left. Upgraded `.brand-icon-pill` executive briefcase to token `var(--dashboard-cyan, #38BDF8)`. Partitioned header utility controls (`#headerCloudBtn`, `#themeToggleBtn`) into `.brand-utility-group` with a 1px vertical divider (`border-inline-start: 1px solid rgba(255, 255, 255, 0.12)`) and 8px padding to establish clear visual breathing room for the AutoJob brand identity.
- **Learned Rule & Skill Persistence — Mandatory DESIGN.md Synchronization & Living Docs Guard (TASK-103):** Updated Step 2 in `.agents/rules/pre-push-verification-and-living-docs.md` to mandate that whenever any UI component, CSS rule, design token, color, typography, or layout is modified, `DESIGN.md` must be updated in the same commit. Upgraded global skill `~/.gemini/config/skills/save-and-sync/SKILL.md` (Sections 4 & 6) to verify living documentation and design specifications (`TASKS.md`, `PROJECT_CONTEXT.md`, `DESIGN.md`, `README.md`) before staging and committing across all projects.

### 5.2 In Progress (WIP)
- **Salary engine market calibration:** Fine-tuning compensation bands based on user feedback and emerging Israeli industrial salary data.

### 5.3 Backlog / Next Steps
- **Direct ATS connectors:** 10 target company boards active; continuing proactive discovery for new openings on Comeet, Greenhouse, Lever, and Ashby.
- **Scheduled cloud executions:** Regular unattended runs via GitHub Actions cron workflows.

---

## 6. Development Rules & Constraints

### 6.1 Strict Zero Emojis Policy
- **Absolute Rule:** Exactly 0 emojis are permitted across the entire repository. This includes Python source code, HTML templates, CSS styles, JavaScript logic, JSON data files, Git commit messages, documentation, and agent chat messages.
- **Enforcement:** Use Phosphor Icons (`ph-` classes) or standard vector SVG glyphs for all visual iconography.

### 6.2 Frontend Architecture & Build Orchestration
- **Source Files:** The frontend source code is cleanly separated in `frontend/` (`frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/js/dashboard.js`).
- **Build Pipeline:** `src/ui_builder.py` orchestrates the build process via `build_and_save_docs_app`, outputting the lightweight HTML shell to `docs/index.html`, bundled CSS/JS assets, and decoupled data feeds (`docs/data/jobs.json` with schema version 2.0.0 and `docs/data/historical_catalog.json`).
- **Cascade Layer Architecture & UI Fixes:** `dashboard.css` is structured into `@layer base, dashboard, studio`. Supplemental cross-browser fixes and overrides are housed unlayered in `ui-fixes.css` (`frontend/css/ui-fixes.css` and `docs/ui-fixes.css`), naturally taking higher cascade precedence over layered styles without requiring brittle `!important` flags.
- **Native Runtime Normalization & Legacy Cleanup:** Salary range inversion auto-ordering (`normalizeSalaryRange`) and duplicate city deduplication (`normalizeJobLocation`) are implemented natively in `dashboard.js`. The obsolete `ui-fixes.js` script has been removed from `frontend/js/`, `docs/`, `ui_builder.py`, and `test_template_docs_sync.py`.
- **Prohibited Action:** Never directly edit compiled production files in `docs/index.html`, `docs/dashboard.css`, `docs/dashboard.js`, or `docs/data/`. Always apply edits to `frontend/` or `src/ui_builder.py` and rebuild.

### 6.3 Bidirectional Text & RTL Formatting
- **Hebrew Layout:** The entire user interface and Hebrew conversational outputs must follow strict RTL formatting (`dir="rtl"`).
- **Text Isolation:** Mixed English terms, numbers, and technical identifiers must be isolated with `dir="auto"` or `text-align: start`.

### 6.4 Touch Targets & Responsive Layout
- **Minimum Tap Size:** Interactive controls (buttons, links, select inputs) must maintain a minimum physical hit area of 44x44 CSS pixels.
- **Mobile First:** Ensure zero horizontal overflow (`scrollWidth <= windowWidth`) and complete symmetry across viewports down to 360px.
- **Headline Brand & Job Card Compact Optimization:** The header brand pill features an executive briefcase icon (`ph-duotone ph-briefcase`) alongside the official AutoJob wordmark (`.brand-logo-text` with "Auto" in crisp white and "Job" in glowing cyan-emerald). Job cards in `#cardsContainer` feature zero dead space: single-row `.job-actions-bar` with 32x32px circular icon buttons (`.card-action-icon-btn` for Apply, Career Studio, Save/Bookmark, Dismiss/Trash, and Alt Link) alongside a compact Details toggle (`.btn-toggle-details`), reduced padding, 36x36px logos, tight meta-grid spacing, and WCAG AA accessible tooltips.

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

### 6.7 Legacy Career Studio UI Retirement (TASK-94 & TASK-98)
- **Superseded by Career Studio v3.0:** The legacy TASK-56/TASK-57 workbench implementation (including `#btnToggleStudioFocus`, dense subtabs `#atsSubtabGatesBtn`/`#atsSubtabKeywordsBtn`/`#atsSubtabResearchBtn`, legacy `#writerAuditorSection`, and segmented `#interviewColSide`/`#interviewColMain`) was retired in TASK-94 and superseded by the 4-stage progressive Career Studio v3.0 architecture (TASK-98, `docs/CAREER_STUDIO_V3_SPEC.md`).
- **Canonical Implementation:** The current production architecture is detailed in Section 6.4 and TASK-98: responsive 55/45 split-screen, unified context bar (`.studio-context-bar`), Step 1 (Hard Gates & Graded Gaps), Step 2 (Keywords & Live Editable A4 Tailoring), Step 3 (LinkedIn & Recruiter Outreach Kit), Step 4 (STAR Interview Simulator), and contextual side column swapping (`#studioA4PreviewCard` in Steps 1-2 vs `#studioJobBriefCard` in Steps 3-4).
- **Ergonomics & Fail-Safe Document Hardening (TASK-105):** CV pill ellipsis truncation (`max-width: 160px;`) with dedicated micro reset button (`#studioBtnResetCv`), active vacancy counter badge (`#studioJobCountBadge`), Stage 1 balanced two-row input grouping with 1-click sample vacancy loader (`.studio-quick-sample-btn`), full-width ATS Analyze CTA button (`.studio-btn-full`), elevated A4 document preview shadow (`0 12px 36px rgba(0, 0, 0, 0.35)`), bullet injection glow animation (`.bullet-just-injected`), and Stage 4 STAR Simulator 2-minute interview countdown timer (`#studioStarTimerBtn`). The live A4 preview verifies markdown integrity and guarantees candidate profile rendering under all upload scenarios.
- **Gemini Multi-Key API Rotation Pool (TASK-106):** Automatic discovery of multiple Gemini API keys via `GEMINI_API_KEYS` (comma/space-separated) or numbered env vars `GEMINI_API_KEY_2`..`20` (`load_gemini_api_keys()`). `GeminiClientPool` tracks per-key daily quota state and rate limits with safe log masking (`mask_api_key`), seamlessly failing over to subsequent keys upon encountering `daily_quota` without tripping model circuit breakers across `main.py` and `scripts/studio_bridge.py`.

### 6.8 CSS Stability, Responsive Layout, and Accessibility Hardening (TASK-58)
- **Modal & Dialog Parity:** `@keyframes slideUpModal` and `@keyframes pulseHeat` registered natively; `dialog.dashboard-modal-backdrop` scoped to `width: 100% / max-inline-size: 100%` with transparent dialog background to prevent double-darkening with `::backdrop` and eliminate horizontal overflow; non-standard `overscroll-behavior: contain` removed from `::backdrop`.
- **Responsive Navigation Alignment:** Breakpoint unified from 880px to 900px across `.dashboard-app` bottom padding and `.mobile-bottom-nav`. Toast notifications (`.dashboard-toast`) and back-to-top button (`.btn-back-to-top`) positioned at `calc(56px + 16px + env(safe-area-inset-bottom, 0px))` with `z-index: 10000`, preventing occlusion by the 56px bottom navigation.
- **Focus & A11y Standards (WCAG 2.4.7 / 2.4.11):** High-contrast `:focus-visible` outlines (2px solid with outline-offset) restored across `.stat-box`, `.stat-cube-btn`, `.controls-inputs-stack select/input`, `.form-input/select/textarea`, and Studio inputs (`.studio-text-input`, `.ats-textarea`, `.studio-clarification-input`).
- **Layout Coordination & Padding Leak Isolation:** Resolved 32px squashed icon on `.card-action-icon-btn.btn-toggle-details` by isolating `padding: 0 !important` and explicit 32px box constraints; eliminated sticky overlap by configuring `.studio-sticky-preview-col` with `calc(var(--sticky-bar-h, 56px) + 16px)` top offset; removed dead flex container queries on `.studio-package-workbench`.
- **Touch & Tooltip Polishing:** Wrapped all desktop hover states (`.cloud-pill`, `.ats-subtab-btn`, `.studio-guided-nav-btn`, `.live-preview-editable-text`, `.apply-icon-btn`, `#btnFetchJobUrl`, `.job-key-requirements`) in `@media (hover: hover)` preventing sticky hover on touch devices; added keyboard `:focus-visible` support to floating action tooltips; added `background-attachment: scroll` for mobile/touch.

### 6.9 PRD Build Protocol & Numbered Requirements Architecture (TASK-59)
- **Single Source of Truth (`docs/PRD.md`):** Complete standard 37-section PRD anchored to actual project systems and pipelines. Every feature, refactor, or automation must trace directly to a numbered requirement (`REQ-01` through `REQ-15`). Code without an explicit requirement is never written.
- **Decision Architecture (`docs/decisions/`):** All major architectural shifts, module divisions, or provider replacements require a documented Architecture Decision Record (`docs/decisions/DEC-XXX.md`) created from `template-decision.md` before implementation.
- **Contract Standardization:** Standard envelope `{ caller, action, payload }` and response `{ ok, data, error }` enforced across all modules and APIs.
- **Secrets & Isolation:** Secrets strictly in `.env`, variable thresholds in configuration, and absolute isolation across projects.

### 6.10 Mobile Accessibility, Micro-Typography, and Touch Target Hardening (TASK-60)
- **Micro-Typography Enhancements:** Scaled up sub-11px labels across dashboard and studio for improved readability: `.stat-cube-label` (11px, line-height: 1.15), `.badge-importance` (11.5px), `.hub-badge` (11.5px), `.q-badge` (11.5px), `.skill-time` (11.5px, `#94a3b8`), `.step-status-pill` and `.step-issues-badge` (0.76rem).
- **WCAG Touch Targets (2.5.5 / 2.5.8 >= 44x44px):** Expanded hitboxes using `::before` / `::after` on `.icon-button` (::before 44x44px), `.apply-icon-btn` (::before 44x44px), and `.live-preview-action-btn` (::after 44x44px); enforced 40x40px with margin on `#cardsContainer .card-action-icon-btn` on mobile; enforced min-height 44px on `.cloud-pill`, `.interview-btn`, `.writer-preset-btn`, `.writer-icon-btn`, `.q-chip`, `.studio-reset-cv-btn`, and navigation mode switches.
- **Color Contrast Hardening:** Upgraded CTA buttons to high-contrast emerald palettes: `.btn-apply.btn-apply-elegant` (`linear-gradient(135deg, #059669 0%, #047857 100%)`, contrast >= 5.5:1), `.apply-icon-btn` (`#047857`, contrast 8.0:1), and `.studio-url-input-group #btnFetchJobUrl` (`#047857`, contrast >= 5.5:1).
- **iOS WebKit Auto-Zoom Elimination:** Applied `font-size: 16px !important` across all inputs, textareas, and dropdowns under `@media (pointer: coarse), (max-width: 900px)` to prevent viewport zooming on mobile Safari.

### 6.11 Theme Cascade Consolidation and Retirement of `theme.css` (TASK-61)
- **Cascade Layer Precedence Fix:** Eliminated legacy unlayered stylesheet `theme.css` which was overriding `@layer base` and `@layer dashboard` via W3C cascade precedence rules.
- **Immediate Theme Initialization:** Added `data-theme="dark"` directly onto `<html lang="he" dir="rtl" data-theme="dark">` to ensure instant dark-mode token evaluation without waiting for client-side JavaScript execution.
- **Container Resets:** Reset `.dashboard-app` (`background-color: var(--bg-canvas); background-image: none;`) and `.dashboard-card` (`background: var(--glass-bg-card);`) in `dashboard.css`, ensuring full visual parity across local and deployed environments.

### 6.12 Structural CSS Recovery & Safe Deep-Purple Theme Overrides (TASK-62)
- **CSS Brace & Layer Recovery:** Fixed the premature closing brace in `.apply-icon-btn` that had previously caused Blink to discard all 674 rules of `@layer studio` (`.studio-master-split`, `.ats-gauge-svg`, desktop `.dashboard-header` overrides), restoring exact `depth=0` balance.
- **Layered `docs/theme.css` Baseline:** Restored `docs/theme.css` (preserving `.dashboard-app` padding, `.dashboard-main` centering, `.dashboard-topbar`, `.dashboard-two-col`, and filter grids) and wrapped its rules inside `@layer base` (after `@layer base, dashboard, studio;`), preventing unlayered overrides of `.ats-gauge-svg` (`58x58`) and Studio controls while preserving layout geometry.
- **Header Cube & Theme Overrides:** Restored desktop `.stat-cube-label` to `9px` inside `68px` cubes (retaining `11px` on mobile), updated `:root[data-theme="dark"]` with deep-purple tokens (`#0b0e14`, `#131722`, `#8b5cf6`, `#a78bfa`), and appended targeted unlayered overrides at the end of `dashboard.css` for clean canvas background (`background-image: none !important`), `.btn-apply-elegant`, and `.btn-open-in-studio`.

### 6.13 Permanent Job Purge Resilience & Cloud Sync Tombstone Architecture (TASK-68)
- **Excised Premature Un-Purging in Background Sync:** Removed aggressive logic in `fetchCloudSync` that previously purged local `purged` status when a job was not yet present in the remote `data.purged` array, eliminating the race condition where local purges were wiped before the remote CAS write completed.
- **Persistent Tombstone Tracking (`purgedMap`):** Introduced `ido_job_purged_keys` in `localStorage` backed by `loadPurgedJobs()` and `savePurgedJobs()`. Applied across single-job permanent deletion (`purgeJobPermanently`), bulk deletion (`clearAllRejected`), and triage toggling (`toggleAction`), mirroring the architectural pattern of `loadRestoredJobs()`.
- **Remote Resurrection Protection:** Hardened both `shouldMirrorFromRemote` and standard incremental reconciliation to cross-check `purgedMap` before adding jobs to `rejected`, `saved`, or `starred`, strictly preventing stale cloud records from reviving purged jobs.
- **Atomic CAS Cloud Partitioning:** Enhanced `pushCloudSync` to build `purgedSet` across local states and `purgedMap`, strictly excluding purged identifiers from `payload.rejected`, `payload.saved`, and `payload.starred` prior to transmission to Supabase.

### 6.14 Apple-Style High-End Visual Design & Collision-Proof 2-Tier Job Cards (TASK-71)
- **Elimination of Card Bottom Overlaps:** Refactored `.card-bottom-row` into a dedicated 2-tier vertical stack: Upper tier provides 100% width for `.card-salary-location` (`.card-salary-val` wrapped in `<bdi dir="auto">` and `.card-location-text`), Lower tier houses `.card-actions-cluster` with prominent Apple primary pill CTA (`.btn-details-pill` with chevron indicator) and circular utility controls (`.apply-icon-btn`, `.btn-open-in-studio`, `.action-reject-btn`). Collision count dropped from 44/44 to 0/44.
- **Requirements Preview Descender Fix:** Updated `.card-reqs-preview` with generous line-height (`1.55`) and padding (`10px 12px`), preventing vertical clipping of Hebrew/Latin text descenders.
- **Career Studio Accordion Overlap Resolution:** Enforced `.studio-job-details-accordion:not([open]) > :not(summary) { display: none !important; }`, preventing closed `<details>` body contents (`.ats-sample-chips`, `.ats-input-label`) from leaking vertically onto `.studio-subnav-pipeline` (dropping studio overlaps from 12 to 0).
- **Apple & 3D Web Experience Craft:** Implemented Apple-inspired double-bezel concentric border-radii (`20px` card, `12px` inner snippets, `999px` pills), top specular edge highlight (`inset 0 1px 0 rgba(255, 255, 255, 0.12)`), multi-layered ambient drop shadows (`0 6px 24px rgba(0, 0, 0, 0.35)`), smooth tactile lift on hover (`translateY(-3px)`), and tactile press on buttons (`scale(0.97)`).

### 6.15 Light Mode Color System Upgrade & Dark-Override Neutralization (TASK-75, TASK-76)
- **Minimal Slate + Cobalt Architecture:** Configured `:root[data-theme="light"]` with crisp surfaces (`--bg-canvas: #F4F6FA`, `--bg-surface: #FFFFFF`, `--glass-bg-card: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)`), slate borders (`--border-subtle: 1px solid #E2E8F0`, `--glass-border: 1px solid #CBD5E1`), high-contrast typography (`--text-primary: #0F172A`, `--text-secondary: #475569`), and cobalt brand accents (`--accent-primary: #1D4ED8`, `--dashboard-cyan: #1E3A8A`, `--status-fail: #991B1B`).
- **Neutralized Hardcoded Dark Components:** Refactored top header to clean white (`#FFFFFF`) with subtle border/shadows; neutralized dark stat cubes into high-contrast soft pastels (new green `#ECFDF5`/`#065F46`, saved blue `#EFF6FF`/`#1E40AF`, starred yellow `#FFFBEB`/`#92400E`, rejected red `#FEF2F2`/`#991B1B`); converted `.copilot-promo-card` from obsidian black to soft violet gradient (`linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)`) with border `#DDD6FE` and `#1E1B4B` text; and styled `.search-capsule-ribbon` with `#F8FAFC` capsules and `#CBD5E1` borders.
- **Button & Control Accents:** Styled `.mode-switch-btn`, `.copilot-promo-btn`, `.btn-apply`, `.btn-apply-elegant` with clean white surfaces, dark slate typography, cobalt border (`1.5px solid #1D4ED8`), and soft blue active/hover states (`#EFF6FF`).
- **Layer & Constraint Hygiene:** Maintained strict brace depth `0` across `@layer base, dashboard, studio;`, wrapped hover effects in `@media (hover: hover)`, eliminated all `backdrop-filter:`, `transition: all`, and `100vw`. Full parity verified by `test_template_docs_sync.py`, `test_phase6_design_and_a11y.py`, zero emojis, and clean hygiene.

### 6.16 Design System Consolidation & CSS Token Hardening (TASK-93, Nov 2026)
- **Token Harmonization in `frontend/css/dashboard.css` (compiled to `docs/`):**
  - Consolidated interactive accent colors: Eliminated hardcoded `#38bdf8` in active rules and teal gradients in `.btn-apply`, unifying all controls onto `var(--accent-primary)` and `var(--dashboard-cyan)`. Retained `#7FB2E5` in `:root` fallback for contrast verification tests.
  - Replaced dark surface hardcodes: Dialog and overlay dark blue values (`#0b1120`, `#0b101b`) replaced with `var(--bg-canvas)`, `var(--bg-surface)`, and `var(--glass-bg-elevated)`.
  - Semantic Status Routing: Replaced hardcoded status hex values with semantic tokens (`var(--status-pass)`, `var(--status-warn)`, and `var(--status-fail)`).
  - Responsive Breakpoints: Consolidated fragmented media queries onto the 3 standard breakpoints (`1120px`, `900px`, `640px`) plus `400px` for ultra-narrow viewports.
  - Logical Properties for Back-to-Top: Removed duplicate `.btn-back-to-top` positioning rules and implemented a single canonical rule using CSS Logical Properties (`inset-inline-start: 16px; inset-block-end: 16px;`).
  - Corner Radii Alignment: Snapped non-token radii (14px -> `var(--radius-control)` / `var(--radius-card)`, 18px -> `var(--radius-modal)`).
- **Volume & Storage Diagnostics (`evaluation_state.json`):**
  - Identified storage driver: 30MB+ file size driven by 3,540 `COMPLETE` records storing verbose `snippet` (~6.6MB) and full `description` (~5.9MB) along with 2-space indentation.
  - Verified safety: All 3,540 completed URLs are already captured in `data/jobs_state.json` (6,469 handled links). Proposed safe atomic pruning pipeline preserving deduplication integrity.
- **U5 Evaluation Benchmark Preparation:**
  - Sampled 18 balanced real-world Israeli market jobs across target positive roles, borderline roles, and disqualified negatives into `data/evaluation_benchmark_template.json` for human ground-truth calibration.
- **Career Studio Legacy UI Reset (TASK-94):**
  - Reset legacy Career Studio UI markup, buttons, and CSS rules in `frontend/` to allow a clean-slate redesign.
  - Preserved all backend scripts (`scripts/studio_bridge.py`, `tools/cv_tailor/`, `src/url_guard.py`), Pydantic schemas, baseline CV profiles (`frontend/data/career_studio_profile.json`, `studio_profile.json`, `frontend/data/cv/`), and candidate realism rules.
  - Job Radar, duplicate handling, inactive jobs scanning, and Supabase CAS sync continue to operate with 100% test integrity.
- **Light Mode Canvas & Component Surface Coherence (TASK-96):**
  - Screen-Reader Utility: Added standard `.visually-hidden` in `@layer base` for accessible hiding of header title and theme toggles without raw text leakage.
  - Full Canvas Neutralization: Neutralized dark background leaks in Light Mode by enforcing `#F8FAFC` background across `:root[data-theme="light"]`, `html[data-theme="light"]`, and `.dashboard-app`.
  - Clean Slate Cards & Empty State: Structured `.dashboard-card`, `.empty-state`, headers, chips, and subheaders in Light Mode with pure white surfaces (`#FFFFFF`), crisp slate borders (`#CBD5E1`), and dark typography (`#0F172A` / `#475569`).
  - Dynamic Chart Theme Sync: Chart.js sector distribution chart dynamically adapts axes, grid lines, and tooltip styling to Light Mode palette upon theme switching.

---

## 7. MCP Servers Usage Policy & Operational Protocol

### 7.1 Allowed MCP Servers Table
| MCP Server | System Role | Required Trigger | Operational Restrictions |
| :--- | :--- | :--- | :--- |
| **`tavily`** | Discovery layer (Tier 1): finding new job vacancies on the web and domain mapping. | When searching new postings from target firms (energy, gas, drones, SCADA) or verifying company URLs/domains. | Forbidden for deep scraping of complex portals (use native Python scrapers or Firecrawl instead); no non-job general searches. |
| **`firecrawl`** | Deep extraction layer (Tier 3 - last resort): complex career pages (heavy JS / SPA). | Strictly when a job link fails simple extraction, or when heavy JS rendering prevents full requirement parsing. | Forbidden as primary discovery search (credit conservation); execute surgically on single links only, never mass crawl. |
| **`chrome-devtools`** | UI verification: responsive dashboard layout inspection and browser debugging. | When editing or fixing dashboard interface code (`src/ui_builder.py` / `docs/index.html`) or verifying mobile layouts. | Strictly forbidden in unattended automation runs (Cron/Headless); forbidden when task has no UI component. |
| **`github`** | CI/CD monitoring: GitHub Actions run logs, release tracking, version synchronization. | When reporting on failed daily GitHub Actions cron runs, or when checking remote run histories. | Forbidden for redundant calls when required information already exists in the local workspace. |
| **`supabase_mcp`** | Cloud database & sync management: PostgreSQL schema, `public.sync_state` table, RLS policies, security advisors. | When verifying, debugging, or updating cross-device sync state (Mobile/Desktop), table migrations, or advisory checks. | Forbidden in routine scraping runs without database changes; destructive operations (DDL/DML delete) require explicit confirmation. |
| **`gemini-api-docs`** | Official library documentation: Google Gemini API and SDK references. | Strictly when upgrading `google-genai` SDK code, syntax, or modifying structured JSON output schemas. | Forbidden if connection and schema code is stable and not undergoing syntactic revision. |

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
