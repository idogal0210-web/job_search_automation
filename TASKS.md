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


---

## Completed Tasks Archive
*(Completed tasks with verification hashes and test evidence will be archived here)*
