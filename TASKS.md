# Project Task Lifecycle Tracker — job_search_automation

Tracking document for project milestones, bug fixes, and feature implementations.
Strictly adheres to the zero-emoji policy and evidence-based completion.

---

## Active Backlog

*(No open backlog tasks. All milestones TASK-01 through TASK-30 are verified complete and archived below.)*

---

## Completed Tasks Archive

### Phase 1: State Invariants & Persistence
- [x] **TASK-01**: Fix state reconciliation to prevent purged/rejected jobs from reverting after scraper runs.
  - Target files: `src/ui_builder.py`, `src/url_utils.py`, `data/sync_state.json`, `data/weekly_archive.json`, `data/historical_catalog.json`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Implemented `purged` and `rejected` reconciliation across canonical URLs, `stable_job_id`, and `content_job_hash` in `update_weekly_archive` (`src/ui_builder.py`), plus client-side tombstones in `frontend/js/dashboard.js` (`commit 5222229`, 2026-11-02). Verified via `tests/test_state_and_counters_consistency.py`.
- [x] **TASK-02**: Enforce deterministic job ID hashing across all scrapers and build stages.
  - Target files: `src/url_utils.py`, `src/ui_builder.py`, `frontend/js/dashboard.js`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Implemented deterministic `stable_job_id` (LinkedIn/Comeet/Drushim IDs + fallback) and normalized `content_job_hash` (`ch_<sha256[:12]>`) in `src/url_utils.py` (`commit 5222229`, 2026-11-02). Legacy paths (`src/scrapers/`, `daily_job_search_unified.py`) were superseded by `src/fetchers.py` and `main.py`. Verified via `test_stable_job_id_deterministic` and `test_content_job_hash_resilience`.

### Phase 2: Mobile UI & Tab Counters Synchronization
- [x] **TASK-03**: Unify badge counters logic between Desktop and Mobile views.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Unified single-source-of-truth counter updates across `stat*Count` (Desktop), `summary*Count` (Mobile), and `count*` DOM elements in `frontend/js/dashboard.js` (`commit 5222229`, 2026-11-02). Verified via `test_js_has_unified_counter_and_resize`.
- [x] **TASK-04**: Remove "More Filters" completely and reclaim layout dead space.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Removed `.advanced-job-filters`, `scoreFilter`, and `salaryFilter` markup/styles/listeners across `frontend/` and `docs/` (`commit 5222229`, 2026-11-02). Verified via `test_advanced_filters_removed_from_template_and_docs`.
- [x] **TASK-05**: Implement iOS Safari form guard (`font-size >= 16px` on inputs, 44x44px touch targets).
  - Target files: `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Added mobile media-query rules enforcing `font-size: 16px !important` on inputs/selects and `min-height: 44px !important` / `min-width: 44px !important` touch targets (`commits 093b988`, `5222229`, 2026-11-01 to 2026-11-02). Verified via `test_mobile_input_font_size_and_touch_targets`.

### Phase 3: Company Logo Fidelity (Zero Synthetic Logos)
- [x] **TASK-06**: Implement official company logo extraction pipeline and zero synthetic monogram fallback.
  - Target files: `src/fetchers.py`, `src/ui_builder.py`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_state_and_counters_consistency.py`
  - Evidence: Extracted official LinkedIn/Drushim/local logos in `src/fetchers.py` and `src/ui_builder.py`; removed synthetic `.job-company-avatar` monogram fallback in `frontend/js/dashboard.js` with clean `hideCompanyLogoElement` `onerror` handling (`commit 5222229`, 2026-11-02). Verified via `test_zero_synthetic_logos_policy`.
- [x] **TASK-07**: Backfill existing job records with verified official company logos.
  - Target files: `scripts/backfill_company_logos.py`, `data/historical_catalog.json`, `data/weekly_archive.json`, `docs/data/historical_catalog.json`, `docs/data/jobs.json`
  - Evidence: Created and ran `scripts/backfill_company_logos.py` across `data/historical_catalog.json` and `data/weekly_archive.json` (`commit 5222229`, 2026-11-02), resolving verified LinkedIn/Drushim/local assets and nulling unverified entries.

### Phase 4: Energy Target Roles & Policy Expansion (Grill-Me Alignment)
- [x] **TASK-08**: Implement 7 high-demand energy roles and updated screening & tiering policy.
  - Target files: `main.py`, `src/job_policy.py`, `src/evaluators.py`, `.agents/skills/job-search-automation-state/references/search-preferences.json`
  - Evidence: Verified via 305/305 unit tests passing (`tests/test_policy_expansion.py`), zero-emoji audit passed (0 emojis), hygiene validation clean. Completed 2026-11-04.

### Phase 5: Architecture Modularization & External Refactoring
- [x] **TASK-09**: Implement architectural review recommendations (modular pipeline, configuration centralization, prompt externalization, unified GeminiPool, deduplicated salary extraction).
  - Target files: `main.py`, `src/config.py`, `src/prompts.py`, `prompts/`, `src/fetchers.py`, `src/job_policy.py`, `src/gemini_runtime.py`, `tools/cv_tailor/`, `.save-and-sync.yml`
  - Evidence: Monolithic `main()` decomposed, prompts extracted under `prompts/`, search keywords & aliases centralized in `src/config.py`, `JobFetcher` registry and `GeminiPool.generate_json` wired across tools, 305/305 tests passing (`524ca08`, `cf807e8`, `90b4d2e`). Completed 2026-11-05.

### Phase 6: Career Studio Workspace, Cloud Sync & Stabilization
- [x] **TASK-10**: Career Studio Core Architecture & Multi-Module Workspace (Milestone 1).
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_m1_challenger_stress.py`, `tests/stress_m1_harness.js`
  - Evidence: Symmetrical App Switcher between Job Radar and Career Studio with bidirectional `#studio` hash sync, WCAG AA 44x44px touch targets, client-side CV file upload/parsing, verified via 306 Python tests and Node.js stress harness. Completed 2026-11-05.
- [x] **TASK-11**: ATS Matcher & Statutory Hard Gates Engine (Milestone 2).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m2_ats_spec.py`, `tests/stress_m2_harness.js`
  - Evidence: Statutory hard gates scanner, 4-bucket keyword taxonomy, and ATS structural compliance checklist verified via spec tests. Completed 2026-11-05.
- [x] **TASK-12**: AI Writer, 3-Mode Tone Switcher & Industrial Terminology Engine (Milestone 3).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m3_writer_spec.py`, `tests/test_m3_grammar_dict_challenger.py`
  - Evidence: 3 professional tone profiles, STAR formula bullet transformer, active-verb grammar checker, and bilingual energy terminology search. Completed 2026-11-05.
- [x] **TASK-13**: AI Interview Simulator, STAR Evaluation & LinkedIn Optimization (Milestones 4-6).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `tests/test_m456_studio_spec.py`
  - Evidence: Scenario-based interview practice, STAR answer breakdown, LinkedIn headline/summary generator, and skills gap matrix with anonymization export. Completed 2026-11-05.
- [x] **TASK-14**: Career Studio Curated ATS Selector & Progressive Step Glow.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `tests/test_m2_ats_spec.py`, `tests/stress_m2_harness.js`
  - Evidence: Dropdown selector (`atsJobSelector`) strictly displaying Starred and Saved jobs, progressive focus glow (`studio-step-active-glow`), verified via 17 ATS spec tests and 2,489 stress assertions (`commit 262404b`). Completed 2026-11-06.
- [x] **TASK-15**: Indeed and Glassdoor Multi-Source Scrapers Integration.
  - Target files: `src/fetchers.py`, `src/config.py`, `main.py`, `src/pipeline.py`, `src/publishers.py`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `requirements.txt`, `requirements-lock.txt`, `tests/test_new_fetchers.py`
  - Evidence: Added Indeed and Glassdoor scrapers (later decommissioned in TASK-25), verified 313/313 unit tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-16**: Remove Obsolete About-System Modal and Header Info Trigger.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`
  - Evidence: Removed `.header-about-btn`, `#aboutModal`, and handlers; verified 1:1 dual-template parity, 313/313 tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-17**: Implement Manual Cloud Job Search Trigger via GitHub Actions.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Added `#headerRunSearchBtn` and `#runSearchModal` (later streamlined in TASK-22); verified 1:1 dual-template parity, 313 tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-18**: Streamline Job Card Sub-Categories (Option 1: 3 Focused Anchors).
  - Target files: `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`, `prompts/job_evaluation_v1.txt`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Streamlined job card and modal details to 3 concise anchors with `condenseMatchInsight` and `condenseFitGap`; verified 1:1 dual-template parity, 313/313 unit tests passing, zero emojis. Completed 2026-11-07.
- [x] **TASK-19**: Supabase Cloud Live Sync Architecture for Desktop & Mobile Dashboard.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Created Supabase project in `eu-central-1` (`sync_state` PostgreSQL table, RLS, Realtime) and dependency-free client adapter with background polling (`commits bf336ae`, `521442f`). Completed 2026-11-08.
- [x] **TASK-20**: Formalize Supabase MCP Server Operational Policy in Agent Rules.
  - Target files: `.agents/rules/mcp-policy.md`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Added `supabase` server governance triggers and safety restrictions to `.agents/rules/mcp-policy.md` (`commit 8eaf91e`). Completed 2026-11-08.
- [x] **TASK-21**: Re-provision Supabase project and add owner-only authentication with in-modal UI.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`
  - Evidence: Provisioned project `wvwdxpttwsrdbvvtiyoh` with owner-only RLS policies (`authenticated` role) and native in-modal email/password auth UI (`commits ca974f9`, `3567ba9`). Verified 1:1 dual-template parity, 313/313 unit tests passing, zero emojis. Completed 2026-11-10.
- [x] **TASK-22**: Supabase-only sync, removal of GitHub tokens and minimal cloud UI.
  - Target files: `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `frontend/css/dashboard.css`, `docs/dashboard.css`
  - Evidence: Removed GitHub dispatch/token flow and static sync fallback; replaced dual header buttons/modals with `#headerCloudBtn` and `#cloudModal` (`commit 21e86ce`); 313/313 unit tests passing, zero emojis. Completed 2026-11-10.
- [x] **TASK-23**: Automated Daily Inactive Jobs Detection & Zero-Worker Modal Overhaul.
  - Target files: `scripts/scan_inactive_jobs.py`, `.github/workflows/daily_job_search.yml`, `data/inactive_jobs.json`, `docs/data/inactive_jobs.json`, `frontend/templates/index.html`, `docs/index.html`, `frontend/js/dashboard.js`, `docs/dashboard.js`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Automated daily execution in GitHub Actions, eliminated Cloudflare Worker dependency, added `#inactiveJobsCountBadge`, card warning chip, and 1-click bulk removal (`commit 5a3e2c5`); 313/313 unit tests passing, zero emojis. Completed 2026-11-10.
- [x] **TASK-24**: Email Report Partial-Status Calibration (`is_incomplete_run`).
  - Target files: `src/publishers.py`, `tests/test_audit_regressions.py`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Implemented `is_incomplete_run` guard in `src/publishers.py` with regression tests for secondary failures vs core breakdowns (`commit 374d983`); 315/315 unit tests passing, zero emojis. Completed 2026-11-10.
- [x] **TASK-25**: Decommission Indeed and Glassdoor Scrapers and Remove Platform Directives.
  - Target files: `main.py`, `src/fetchers.py`, `src/config.py`, `src/pipeline.py`, `.agents/skills/job-search-automation-state/SKILL.md`, `.agents/skills/job-search-automation-state/references/search-preferences.json`, `tests/test_new_fetchers.py`, `tests/test_main_integration.py`, `tests/test_audit_regressions.py`, `PROJECT_CONTEXT.md`, `README.md`, `TASKS.md`
  - Evidence: Removed Indeed and Glassdoor directives and active scraper invocations due to persistent anti-bot 403 gating, replacing adapters with safe no-op stubs (`commit 6316dbf`). Verified 311/311 unit tests passing, zero emojis. Completed 2026-11-11.
- [x] **TASK-26**: Redefinition of Job Types, Search Queries & AI Evaluation Policy.
  - Target files: `src/job_policy.py`, `.agents/skills/job-search-automation-state/references/search-preferences.json`, `prompts/job_evaluation_v1.txt`, `tests/test_policy_expansion.py`, `tests/test_job_profile_redefinition.py`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Calibrated autonomous search and evaluation for Junior/Mid-Entry Solar Site Management, BESS Commissioning, QA Inspection, CleanTech startups, Gas & Pressure Systems, UAV, strict 24/7 shift disqualification, and 14,000 ILS gross floor (`commit 43af65c`). Verified 318/318 unit tests passing, zero emojis. Completed 2026-11-11.
- [x] **TASK-27**: Unified Career Studio Split-Pane UX & Local AI Bridge Integration.
  - Target files: `src/gemini_runtime.py`, `src/ui_builder.py`, `prompts/cv_analysis_v1.txt`, `prompts/cv_generation_v1.txt`, `tools/cv_tailor/tailor.py`, `tools/cv_tailor/src/utils.py`, `tools/cv_tailor/src/analyzer.py`, `tools/cv_tailor/src/generator.py`, `scripts/studio_bridge.py`, `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/js/dashboard.js`, `frontend/data/studio_profile.json`, `docs/index.html`, `docs/dashboard.css`, `docs/dashboard.js`, `docs/career/studio_profile.json`, `tests/test_studio_bridge.py`, `tests/test_template_docs_sync.py`, `PROJECT_CONTEXT.md`, `README.md`, `TASKS.md`
  - Evidence: 1) Parsed `tools/cv_tailor/base_profile.md` (with `base_profile.template.md` CI fallback) dynamically via `load_candidate_profile_data` and `/api/profile`, synced non-PII `excluded_employers` deterministically into `studio_profile.json`, and added Pydantic schemas (`AtsStudioAnalysisSchema`, `TailoredCvPackageSchema`, `CvTailoredBulletSchema`, `StarInterviewEvaluationSchema`) in `src/gemini_runtime.py`; 2) Fixed `generator.py` `NameError` bug and removed fake 85% degraded fallback score in `analyzer.py`; 3) Created loopback-only `scripts/studio_bridge.py` wrapping `tools/cv_tailor/` with SSRF/CORS/PNA guards; 4) Implemented responsive Split-Pane (45%/55% desktop, stacked >=48px touch mobile) in Career Studio with interactive clarifications, real SpeechRecognition guard (replacing fake toast), AI/offline status clarity, `LocalStorage` STAR history, safe DOM Markdown preview, A4 PDF print export, and atomic saves to `tools/cv_tailor/output/`; 5) Verified 326/326 Python tests (including mocked CI no-`base_profile.md` fallback), 2,489 JS stress assertions, 1:1 `frontend/` -> `docs/` sync, Chrome DevTools desktop/mobile layout checks, hygiene/secret scans, and zero emojis. Completed 2026-11-12.
- [x] **TASK-28**: Career Studio v2 Master Split-Screen (`60/40`), Sticky Live Preview, Native Dialogs & Bidirectional Editing.
  - Target files: `docs/CAREER_STUDIO_V2_SPEC.md`, `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/js/dashboard.js`, `docs/index.html`, `docs/dashboard.css`, `docs/dashboard.js`, `tests/test_studio_bridge.py`, `PROJECT_CONTEXT.md`, `README.md`, `TASKS.md`
  - Evidence: 1) Created scoped technical spec `docs/CAREER_STUDIO_V2_SPEC.md` resolving DOM contract, privacy/CI boundary, Vanilla ES6+ `StudioState`, RTL logical layout, and accessibility requirements; 2) Implemented `60fr / 40fr` `.studio-master-split` with Sticky Live CV Preview (`#studioStickyPreviewCol`, `#studioLiveDocViewer`), bidirectional click-to-edit (`selectPreviewLineForEditing`) and `applyBulletToCv()` highlighting, header-triggered `#studioMobilePreviewDialog` on `<1120px` (no `#btnBackToTop` collision, `48px` touch height), `<details class="studio-passed-gates-accordion">` grouping passing/inactive gates below priority gates, `<dialog id="studioGlossaryDialog">` for the 20-term dictionary, `<dialog id="studioExportDialog">` for focused A4 preview/export, Tab 3 Segmented Control (`#interviewSegmentedBar`) toggling STAR simulator vs LinkedIn alignment, and Tab 4 real-time `redactSensitiveText` + `printAnonymizedCvA4()`; 3) Verified via `tests/test_studio_bridge.py` (`TestCareerStudioV2SplitScreenAndDialogs`), 332/332 Python tests, 2,489/2,489 JS stress assertions, 1:1 `frontend/` -> `docs/` sync, Chrome DevTools desktop (`1440px`) and mobile (`<=500px`) interactive runs, zero-emoji audit, and hygiene/secret validation. Completed 2026-11-12.
- [x] **TASK-29**: Dashboard Visual, Specificity & Responsive UI/UX Audit Remediation.
  - Target files: `frontend/css/dashboard.css`, `frontend/js/dashboard.js`, `frontend/templates/index.html`, `docs/dashboard.css`, `docs/dashboard.js`, `docs/index.html`, `tests/test_studio_bridge.py`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Resolved `theme.css` specificity collisions against `.profile-title` (mobile `#headerCloudBtn` overlap), `.btn-clear-search` (hidden properly on empty search), `.mode-switch-btn` (`white-space: nowrap`), `.cloud-pill`, `.tool-btn-compact`, `.btn-reset-filters`, and `.live-preview-line` (`flex: 0 0 auto`, `10px` radius, zero vertical text overlap); restored `.studio-subnav-pipeline` 2x2 horizontal grid above Career Studio Split-Screen; added `dir="auto"` to mixed-language requirement/anchor text, `naturalWidth === 0` company logo fallback, `.job-card-topbar-badges` wrapping, and `>= 44px` mobile touch targets across Job Radar & Career Studio (`0` small touch targets and `0` horizontal overflow in Chrome DevTools desktop `1440x900` & mobile `500px`); verified 332/332 Python tests, 2,489/2,489 JS assertions, 1:1 `frontend/` -> `docs/` sync, zero-emoji, and hygiene/secret validation. Completed 2026-11-12.
- [x] **TASK-30**: Configure `api-anything` Project MCP Plugin & Dedicated API-First Skill.
  - Target files: `.agents/plugins/api-anything/plugin.json`, `.agents/plugins/api-anything/mcp_config.json`, `.agents/skills/api-anything/SKILL.md`, `.agents/skills/api-anything/references/authoring.md`, `.agents/skills/api-anything/references/writes.md`, `.agents/rules/mcp-policy.md`, `PROJECT_CONTEXT.md`, `TASKS.md`
  - Evidence: Configured project-scoped MCP plugin (`api-anything@0.4.0` via `/usr/local/bin/npx -y api-anything mcp`), authored `.agents/skills/api-anything/SKILL.md` with authoring/writes references instructing API-first querying over browser launching, registered `api-anything` governance in `.agents/rules/mcp-policy.md` and `PROJECT_CONTEXT.md`; verified JSON validity, live MCP stdio handshake (`10` tools discovered), YAML frontmatter, and zero-emoji compliance. Completed 2026-11-12.
- [x] **TASK-31**: Phased API-First ATS Expansion, Career Studio Scraper Optimization, Inactive Scanner Upgrade & Governance Sync.
  - Target files: `src/ats_client.py`, `src/fetchers.py`, `src/config.py`, `src/url_utils.py`, `src/pipeline.py`, `main.py`, `tools/cv_tailor/src/scraper.py`, `scripts/scan_inactive_jobs.py`, `.agents/skills/job-search-automation-state/references/search-preferences.json`, `.agents/skills/resilient-automation-patterns/SKILL.md`, `.agents/skills/job-search-automation-state/SKILL.md`, `.agents/skills/cv-tailor/SKILL.md`, `tests/test_ats_connectors.py`, `tests/test_main_integration.py`, `tests/test_audit_regressions.py`, `PROJECT_CONTEXT.md`, `README.md`, `TASKS.md`
  - Evidence: 1) Discovered and verified live ATS boards across target companies (`Comeet`: Enlight, Driivz, Percepto, XTEND, mPrest; `Greenhouse`: Augury, Electreon; `Lever`: D-Fend Solutions) and registered them under `ats_boards` in `search-preferences.json` via `get_ats_boards()`; 2) Built unified `src/ats_client.py`, added `fetch_greenhouse_jobs`, `fetch_lever_jobs`, `GreenhouseFetcher`, `LeverFetcher`, and per-source `CircuitBreaker` in `src/fetchers.py`, extended `stable_job_id` (`gh_`, `lever_`, `ashby_`) in `src/url_utils.py`, and wired multi-board ATS collection in `main.py`; 3) Integrated API-first ATS extraction into `tools/cv_tailor/src/scraper.py` (bypassing Firecrawl credits on supported ATS URLs), `src/pipeline.py` (`enrich` + `final_status`), and `scripts/scan_inactive_jobs.py` (`check_job_url`); 4) Synchronized 3-tier `api-anything` guidance across skills and living docs; 5) Verified 340/340 Python unit tests passing (`tests/test_ats_connectors.py` + full suite), zero-emoji audit passed, and secret scan clean. Completed 2026-11-12.
