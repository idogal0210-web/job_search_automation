# Project Task Lifecycle Tracker — job_search_automation

Tracking document for project milestones, bug fixes, and feature implementations.
Strictly adheres to the zero-emoji policy and evidence-based completion.

---

## Active Milestone: Core Stability & Mobile UX Refinement (November 2026)

### Phase 1: State Invariants & Persistence (Critical)
- [ ] **TASK-01**: Fix state reconciliation to prevent deleted/starred jobs from reverting after scraper runs.
  - Target files: `data/jobs_state.json`, `data/historical_catalog.json`, `src/evaluators.py`
  - Success criteria: User actions (archive, star, tab moves) are permanently preserved across Cron runs.
- [ ] **TASK-02**: Enforce deterministic job ID hashing (URL + Company + Title) across all scrapers.
  - Target files: `src/scrapers/`, `daily_job_search_unified.py`
  - Success criteria: Duplicate jobs cannot respawn due to minor whitespace or formatting changes.

### Phase 2: Mobile UI & Tab Counters Synchronization
- [ ] **TASK-03**: Unify badge counters logic between Desktop and Mobile in `docs/index.html`.
  - Target files: `docs/index.html`, `src/ui_builder.py`
  - Success criteria: Tab counts (Total, Passed, Pending, Starred, Archived) match 1:1 on both views.
- [ ] **TASK-04**: Remove "More Filters" completely and reclaim layout dead space.
  - Target files: `docs/index.html`
  - Success criteria: Component, listeners, and CSS removed with zero console errors and clean feed flow.
- [ ] **TASK-05**: Implement iOS Safari form guard (`font-size >= 16px` on inputs, 44x44px touch targets).
  - Target files: `docs/index.html`
  - Success criteria: Zero auto-zoom on iPhone 14, touch targets conform to Apple HIG standards.

### Phase 3: Company Logo Fidelity (Zero Synthetic Logos)
- [ ] **TASK-06**: Implement official company logo extraction pipeline (LinkedIn / Official Domain Favicon).
  - Target files: `src/scrapers/`, `data/jobs_state.json`, `src/ui_builder.py`
  - Success criteria: Only official verified logos stored; null fallback if not found (zero generated monograms).
- [ ] **TASK-07**: Backfill existing job records in `data/jobs_state.json` with verified logos.
  - Target files: `data/jobs_state.json`
  - Success criteria: Backfill script runs cleanly and enriches verified jobs.

### Phase 4: Energy Target Roles & Policy Expansion (Grill-Me Alignment)
- [x] **TASK-08**: Implement 7 high-demand energy roles and updated screening & tiering policy.
  - Target files: `main.py`, `src/job_policy.py`, `src/evaluators.py`, `.agents/skills/job-search-automation-state/references/search-preferences.json`
  - Success criteria: 7 specialized roles added to scraping and keyword groups, salary floor (<15k) and 24/7 rules implemented, test suite passes 100%, zero emojis.
  - Evidence: Verified via 305/305 unit tests passing (`tests/test_policy_expansion.py`), zero-emoji audit passed (0 emojis), hygiene validation clean. Completed 2026-11-04.

### Phase 5: Architecture Modularization & External Refactoring (November 2026)
- [x] **TASK-09**: Implement architectural review recommendations (modular pipeline, configuration centralization, prompt externalization, unified GeminiPool, deduplicated salary extraction).
  - Target files: `main.py`, `src/config.py`, `src/prompts.py`, `prompts/`, `src/fetchers.py`, `src/job_policy.py`, `src/gemini_runtime.py`, `tools/cv_tailor/`, `.save-and-sync.yml`
  - Success criteria: Monolithic `main()` decomposed to ~20 lines, embedded prompts moved to versioned text files under `prompts/`, search keywords & aliases centralized in `src/config.py`, deduplicated salary regex into `extract_advertised_monthly_ils_amounts`, `JobFetcher` abstract registry, `GeminiPool.generate_json` wired across tools, ephemeral intake patterns added to hygiene policy, 305/305 tests passing, zero emojis.
  - Evidence: Verified via 305/305 unit tests passing (`Ran 305 tests in 10.5s OK`), zero-emoji audit passed (0 emojis), hygiene validation clean, committed & pushed in `524ca08`, `cf807e8`, `90b4d2e`. Completed 2026-11-05.

### Phase 6: Career Studio Workspace & Progressive Intelligence (November 2026)
- [x] **TASK-10**: Career Studio Core Architecture & Multi-Module Workspace (Milestone 1).
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_m1_challenger_stress.py`, `tests/stress_m1_harness.js`.
  - Success criteria: Symmetrical App Switcher between Job Radar and Career Studio with bidirectional `#studio` hash sync, WCAG AA 44x44px touch targets, client-side CV file upload and parsing (PDF, DOCX, TXT), baseline profile fallback. Verified via 306 Python tests and Node.js stress harness. Completed 2026-11-05.
- [x] **TASK-11**: ATS Matcher & Statutory Hard Gates Engine (Milestone 2).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m2_ats_spec.py`, `tests/stress_m2_harness.js`.
  - Success criteria: Statutory hard gates scanner (Mechanical Practical Engineer, Certified Electrician progress, B.Sc. gap guard), 4-bucket keyword taxonomy (methodologies, financials, systems, energy), ATS structural compliance checklist. Verified via spec tests. Completed 2026-11-05.
- [x] **TASK-12**: AI Writer, 3-Mode Tone Switcher & Industrial Terminology Engine (Milestone 3).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m3_writer_spec.py`, `tests/test_m3_grammar_dict_challenger.py`.
  - Success criteria: 3 professional tone profiles (Technical/Field, Leadership/PM, Research/Innovation), STAR formula bullet transformer, active-verb grammar checker, and bilingual energy terminology search. Completed 2026-11-05.
- [x] **TASK-13**: AI Interview Simulator, STAR Evaluation & LinkedIn Optimization (Milestones 4-6).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m456_studio_spec.py`.
  - Success criteria: Scenario-based interview practice, STAR answer breakdown, LinkedIn headline/summary generator, professional skills gap matrix with anonymization export. Completed 2026-11-05.
- [x] **TASK-14**: Career Studio Curated ATS Selector & Progressive Step Glow.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_m2_ats_spec.py`, `tests/stress_m2_harness.js`.
  - Success criteria: Dropdown selector (`atsJobSelector`) strictly displays only Starred (`starred`) and Saved (`saved`) jobs, with clear status tags and match score; progressive focus glow (`studio-step-active-glow`) initializes on Step 1 and transfers automatically to Step 2 upon ATS execution (`triggerAtsMatching`), reverting to Step 1 on clear; verified via 17 ATS spec tests, 2,489 stress assertions, and 0 emojis. Completed 2026-11-06 (commit `262404b`).
- [x] **TASK-15**: Indeed and Glassdoor Multi-Source Scrapers Integration.
  - Target files: `src/fetchers.py`, `src/config.py`, `main.py`, `src/pipeline.py`, `src/publishers.py`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `requirements.txt`, `requirements-lock.txt`, `.agents/skills/job-search-automation-state/references/search-preferences.json`, `tests/test_new_fetchers.py`.
  - Success criteria: Added Indeed and Glassdoor scrapers with structured mosaic JSON & DOM extraction, RunHealth tracking, error handling and retry with backoff, UI source badges and styling, 313/313 unit tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-16**: Remove Obsolete About-System Modal and Header Info Trigger.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`.
  - Success criteria: Cleanly remove `.header-about-btn` button, `#aboutModal` dialog markup, `openAboutModal`/`closeAboutModal` JS handlers, and associated CSS. Verified 1:1 dual-template parity via `tests/test_template_docs_sync.py`, 313/313 tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-17**: Implement Manual Cloud Job Search Trigger via GitHub Actions.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `PROJECT_CONTEXT.md`, `TASKS.md`.
  - Success criteria: Added manual play button `#headerRunSearchBtn` and `#runSearchModal` dialog connected to GitHub Actions `workflow_dispatch` API. Includes client-side token management (LocalStorage), live cloud run status detection, progress spinning state, automated polling, and automatic page reload on completion. Verified 1:1 dual-template parity, 313 tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-18**: Streamline Job Card Sub-Categories (Option 1: 3 Focused Anchors).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `prompts/job_evaluation_v1.txt`, `PROJECT_CONTEXT.md`, `TASKS.md`.
  - Success criteria: Streamline job card and modal details from 5 repetitive, verbose categories down to 3 concise, high-signal anchors: 1) תחום ותפקיד (merged domain and role scope), 2) דרישות סף (key threshold requirements), 3) התאמה ופערים (match insight with explicit `[OK]` / `[פער]` status). Added intelligent client-side text condensing (`condenseMatchInsight` and `condenseFitGap`) ensuring all legacy dataset jobs display ultra-short, punchy sentences (e.g. "התאמה טכנית ופיקודית גבוהה | [פער] חסר ניסיון בניהול ייצור תעשייתי"). Verified 1:1 dual-template parity, 313/313 unit tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-19**: Supabase Cloud Live Sync Architecture for Desktop & Mobile Dashboard.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `PROJECT_CONTEXT.md`, `TASKS.md`.
  - Success criteria: Created Supabase project `job-search-dashboard` (`wvwdxpttwsrdbvvtiyoh`) in `eu-central-1` with `sync_state` PostgreSQL table, Row-Level Security (RLS) enabled, Realtime enabled, and seeded with baseline state. Integrated dependency-free Supabase client adapter in `dashboard.js` with optimistic UI, `visibilitychange` / `focus` listeners, and 25-second background polling guarded for browser-only execution (`typeof process === 'undefined'`). Enables seamless, bi-directional sync of starred, saved, rejected, and purged jobs between desktop and mobile browsers. Verified 1:1 dual-template parity, 313/313 unit tests passing, zero emojis. Completed 2026-11-08.
- [x] **TASK-20**: Formalize Supabase MCP Server Operational Policy in Agent Rules.
  - Target files: `.agents/rules/mcp-policy.md`, `PROJECT_CONTEXT.md`, `TASKS.md`.
  - Success criteria: Integrated `supabase` into `.agents/rules/mcp-policy.md` table of authorized MCP servers following `/antigravity-project-auditor` recommendation. Established precise operational triggers (cloud project health checks, table migrations, sync state verification) and safety restrictions (no unconfirmed destructive DDL, no redundant client querying). Verified zero emojis and complete policy alignment. Completed 2026-11-08.


---

## Completed Tasks Archive
*(Completed tasks with verification hashes and test evidence will be archived here)*
- [x] **TASK-21**: Re-provision Supabase project and add owner-only authentication with in-modal UI.
  - Success criteria: New project `wvwdxpttwsrdbvvtiyoh` with `sync_state` table; old project references removed; RLS policies restricted to `authenticated` role with owner email (`idogal0210@gmail.com`); verified anon read returns no rows and anon write returns 401 (RLS violation). Native in-modal authentication panel integrated directly into `syncModal` across `frontend/templates/index.html` and `docs/index.html` with explicit email/password login, initial registration, session display, and sign out controls. Verified 1:1 dual-template parity, 313/313 unit tests passing, zero emojis. Completed 2026-11-10.
- [x] **TASK-22**: Supabase-only sync, removal of GitHub tokens and minimal cloud UI.
  - Success criteria: Removed GitHub dispatch/token code, share-link sync and static sync fallback from `frontend/js/dashboard.js` (mirrored to `docs/`); replaced header sync and run buttons plus both modals with a single `#headerCloudBtn` pill and `#cloudModal` (visible auth errors, no counters); `docs/data/sync_state.json` no longer published; owner email removed from public HTML; origin remote URL cleaned of embedded token; secret scan of repo clean; 313/313 unit tests passing; zero emojis. Completed 2026-11-10.
