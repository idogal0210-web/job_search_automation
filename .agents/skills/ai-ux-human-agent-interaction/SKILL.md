---
name: ai-ux-human-agent-interaction
description: "Specialized Human-Agent Interaction (HAI) and UX engine for job_search_automation. Implements the global agent-experience-interaction-designer standard for the Dual-Template dashboard (frontend/ -> docs/), Career Studio workbench, version-aware Supabase CAS cloud sync, verified company logos, and transparent AI scoring."
---

# AI UX & Human-Agent Interaction Designer (`job_search_automation`)

> **Architectural Base:** Inherits and specializes [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md) for the **`job_search_automation`** ecosystem.

---

## 1. Role & Mission
Ensure the interface between Ido Gal and the autonomous job search and Career Studio platform is:
- **Transparent:** Immediate visibility into *why* a job received its Match Score (concise evaluation anchors, SCADA/PV/gas/UAV match evidence, practical engineer qualification, and salary provenance).
- **Cognitively Lightweight (The 5-Second Rule):** Top matches, statutory hard gates, and salary estimates are scannable in under 5 seconds.
- **Coherent Aesthetics:** Professional theme system, nested-radius law (`inner = outer - padding`), and strict CSS Cascade Layers (`@layer base, dashboard, studio;`).
- **Bi-Directionally Synced:** Seamless, non-destructive triage synchronization between desktop and mobile via `localStorage` and version-aware Supabase Cloud Database (`public.sync_state`).
- **Accessible & RTL:** Flawless Hebrew RTL layout (`dir="rtl"`), BiDi numeric isolation (`<bdi>`, `direction: ltr; unicode-bidi: isolate;`), WCAG 2.2 AA touch targets (`>= 44x44px`), and pure Vanilla HTML5, CSS3, and ES6+ JavaScript.

---

## 2. Mandatory Dual-Template Build Protocol (`frontend/` -> `docs/`)
- **Source of Truth:** Always edit modular source files in `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/css/ui-fixes.css`, `frontend/js/dashboard.js`, and `frontend/templates/email_report.html`.
- **Cascade Layer Encapsulation:** Keep `docs/theme.css` wrapped inside `@layer base` so `@layer dashboard` and `@layer studio` in `dashboard.css` maintain deterministic cascade precedence. Verify brace depth `0` across stylesheets.
- **Compilation & Parity:** Compile into `docs/` via `python3 src/ui_builder.py` (or maintain strict 1:1 byte synchronization).
- **CI Guard:** Every UI change must pass `python3 tests/test_template_docs_sync.py` with zero drift between `frontend/` and `docs/`.

---

## 3. Core Interaction & Architecture Standards

### 3.1 Transparent AI Match Rationale & Compact Job Cards
1. **Header & Symmetrical Layout:** Desktop header uses balanced CSS Grid layout with brand anchor, compact cloud sync indicator, centered view switchers, and category counter cards.
2. **Score & BiDi Salary Badges:** Clean radius `.badge-score` and LTR-isolated `.job-salary-chip` (`normalizeSalaryRange`), paired with deduplicated locations.
3. **Evaluation Anchors:** Concise display of role fit, key requirements, and candidate strengths with zero loose tag chips.
4. **Action Cluster:** Prominent primary action button, Career Studio handoff, triage buttons (save/reject), and modal details toggle.

### 3.2 Version-Aware Triage State & Supabase Cloud Sync (`public.sync_state`)
- **Non-Destructive Hydration & CAS:** User triage states (`starred`, `saved`, `rejected`, `purged`, and notes) use authenticated conditional `PATCH` (`supabaseSyncAdapter.compareAndSwap` with `version` column and conflict merge) against `public.sync_state`.
- **Version Tracking & Purge Reconciliation:** Track cloud version in `localStorage` so remote version increments trigger full state mirroring and bidirectional pruning of stale local purged entries.
- **Privacy & Browser-Safe Guards:** Personal PII is excluded from client JS bundles and hydrated dynamically in-memory; uploaded CV text lives in `sessionStorage`. Guard background polling and event listeners with `typeof process === 'undefined'`.

### 3.3 Career Studio Workbench & Document Flow
- **Modular Studio Architecture:** Seamless workspace connecting target vacancy requirements, ATS gap analysis, bullet impact tailoring, and live A4 document preview.
- **Local Python Bridge Integration:** Connects to loopback `scripts/studio_bridge.py` (`/api/session`, `/api/profile`, `/api/ats/analyze`, `/api/studio/tailor`, `/api/writer/tailor`, `/api/interview/evaluate`) authenticated with `X-Studio-Token` and protected by `src/url_guard.py`, with automatic graceful client-side fallback when offline.
- **Factual CV Tailoring Guard:** Strictly adheres to verified candidate facts, locked original role titles, and zero credential fabrication.

### 3.4 Verified High-Resolution Company Logo Pipeline
1. **Tier 1:** Curated vector/PNG overrides in `docs/assets/logos/` matched via word-boundary `src/company_matcher.py`.
2. **Tier 2:** Verified official corporate logo URL or domain favicon.
3. **Tier 3:** Clean typography fallback on error (`onerror` / `naturalWidth === 0`) — strictly zero synthetic monograms or fake avatars.

---

## 4. Definition of Done
1. `python3 tests/test_template_docs_sync.py`, `python3 scripts/validate_zero_emoji.py`, `python3 scripts/project_hygiene.py --check-secrets --validate`, and all unit tests pass.
2. Strict `dir="rtl"` alignment, BiDi number isolation, and responsive layout verified on desktop and mobile viewports.
3. Zero competitor brand names, zero loose tag chips, and zero emojis across all HTML, CSS, JS, and generated templates.
4. `localStorage` and versioned Supabase cloud sync states remain intact across reloads.
