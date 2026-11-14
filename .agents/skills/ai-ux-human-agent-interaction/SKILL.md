---
name: ai-ux-human-agent-interaction
description: "Specialized Human-Agent Interaction (HAI) and UX engine for job_search_automation. Implements the global agent-experience-interaction-designer standard for the Dual-Template dashboard (frontend/ -> docs/), Split-Pane Career Studio, Supabase real-time cloud sync, zero-tag job cards, high-res company logos, and transparent AI scoring."
---

# AI UX & Human-Agent Interaction Designer (`job_search_automation`)

> **Architectural Base:** Inherits and specializes [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md) for the **`job_search_automation`** ecosystem.

---

## 1. Role & Mission
Ensure the interface between Ido Gal and the autonomous job search and Career Studio platform is:
- **Transparent:** Immediate visibility into *why* a job received its Match Score (requirement assessments, SCADA/PV/gas match, practical engineer vs. B.Sc flexibility, and salary provenance).
- **Cognitively Lightweight (The 5-Second Rule):** Top matches, red flags, and salary estimates are scannable in under 5 seconds.
- **Zero-Tag Clean Aesthetics:** Structured 4-pill metric grids without messy tag chips or visual clutter.
- **Bi-Directionally Synced:** Seamless, non-destructive triage synchronization between desktop and mobile via `localStorage` and Supabase Cloud Database (`public.sync_state`).
- **Accessible & RTL:** Flawless Hebrew RTL layout (`dir="rtl"`) with pure Vanilla HTML5, CSS3, and ES6+ JavaScript.

---

## 2. Mandatory Dual-Template Build Protocol (`frontend/` -> `docs/`)
- **Source of Truth:** Always edit modular source files in `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/js/dashboard.js`, and `frontend/templates/email_report.html`.
- **Compilation & Parity:** Compile into `docs/` (`docs/index.html`, `docs/dashboard.css`, `docs/dashboard.js`) via `src/ui_builder.py` (or maintain strict 1:1 synchronization).
- **CI Guard:** Every UI change must pass `tests/test_template_docs_sync.py` with zero drift between `frontend/` and `docs/`.

---

## 3. Core Interaction & Architecture Standards

### 3.1 Transparent AI Match Rationale & Zero-Tag Cards
1. **Match Score Badge:** Color-coded (Emerald 85+, Blue 70-84, Slate <70).
2. **Structured 4-Pill Metric Grid:** Symmetrical grid (Location, Experience, Role Type, Salary/Field) directly beneath the card header. Strictly zero loose tag chips.
3. **Evidence Breakdown:** Clear requirement assessments citing exact qualifications matched or missing.

### 3.2 Bi-Directional Triage State & Supabase Cloud Sync (`public.sync_state`)
- **Non-Destructive Hydration:** User triage states (`starred`, `saved`, `rejected`, `purged`, and applied notes) must never be wiped during pipeline runs or UI refreshes.
- **Real-Time Cloud Sync:** Maintain optimistic UI updates in `localStorage` paired with authenticated Supabase REST/Realtime sync (`public.sync_state` with RLS).
- **Browser-Safe Guards:** Guard background polling (`25s`), `visibilitychange`, and `focus` listeners with `typeof process === 'undefined'` so Node.js stress harnesses execute cleanly without hanging timers.

### 3.3 Career Studio 3.0 Split-Pane Architecture (`careerStudioWorkspace`)
- **2-Column Split-Pane Workspace (`55fr / 45fr` on Desktop):**
  - **Active Tool Lane (55% width, `.studio-modules-container`):** Houses the 3 core tools (`#studioModuleAts` Jobscan Matcher, `#studioModuleWriter` Teal A4 Package Builder & Resume Worded Bullet Impact Auditor, `#studioModuleInterview` Dynamic LinkedIn SEO Optimizer & Role Interview Prep).
  - **Sticky Live Document Preview (45% width, `#studioStickyPreviewCol`):** Interactive live document viewer (`#studioLiveDocViewer`) with instant tab switching between CV (`#pkgTabCv`), Cover Letter (`#pkgTabCover`), and Interview Talking Points (`#pkgTabTips`), plus 1-click A4 PDF print and click-to-edit synchronization.
  - **Mobile Responsive Stacking:** Automatically collapses to 100% width on `<1120px` with `#btnMobileOpenPreview` opening `<dialog id="studioMobilePreviewDialog">` and touch targets `>= 48px`.
- **Flat 3-Tool Top Context Bar:** Unified `.studio-context-bar` combining job selection (`#atsJobSelector`), direct 1-click handoff from Job Radar cards (`openJobInCareerStudio`), URL ingestion, compact CV status/upload, and the 3-tab horizontal segmented bar (`#studioTabAts`, `#studioTabWriter`, `#studioTabInterview`) — zero right-sidebar or triple-nested step outlines.
- **Local Python Bridge Integration:** Connect seamlessly to `scripts/studio_bridge.py` (`POST /api/ats/analyze`, `/api/studio/tailor`, `/api/writer/tailor`, `/api/interview/evaluate`) with automatic graceful client-side fallback when offline.

### 3.4 Verified High-Resolution Company Logo Pipeline
1. **Tier 1:** Curated vector/PNG overrides in `docs/assets/logos/`.
2. **Tier 2:** Verified official corporate logo URL or domain favicon.
3. **Tier 3:** Clean typography fallback on error (`onerror`) — strictly zero synthetic monograms or fake avatars.

---

## 4. Definition of Done
1. `tests/test_template_docs_sync.py` and all Python/JS milestone tests pass.
2. Strict `dir="rtl"` alignment and responsive layout verified on desktop and mobile viewports.
3. Zero tag chips and zero emojis across all HTML, CSS, JS, and generated templates.
4. `localStorage` and Supabase cloud sync states remain intact across reloads.
