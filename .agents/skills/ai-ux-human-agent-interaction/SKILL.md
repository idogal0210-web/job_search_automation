---
name: ai-ux-human-agent-interaction
description: "Specialized Human-Agent Interaction (HAI) and UX engine for job_search_automation. Implements the global agent-experience-interaction-designer standard for the Dual-Template Glassmorphism dashboard (frontend/ -> docs/), Split-Pane Career Studio with Focus Mode and WYSIWYG A4 editing, version-aware Supabase CAS cloud sync, compact single-row action job cards, verified company logos, and transparent AI scoring."
---

# AI UX & Human-Agent Interaction Designer (`job_search_automation`)

> **Architectural Base:** Inherits and specializes [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md) for the **`job_search_automation`** ecosystem.

---

## 1. Role & Mission
Ensure the interface between Ido Gal and the autonomous job search and Career Studio platform is:
- **Transparent:** Immediate visibility into *why* a job received its Match Score (3 concise anchors, SCADA/PV/gas/UAV match evidence, practical engineer vs. B.Sc flexibility, and salary provenance).
- **Cognitively Lightweight (The 5-Second Rule):** Top matches, statutory hard gates, and salary estimates are scannable in under 5 seconds.
- **Coherent Dark Glassmorphism Aesthetics:** Permanent dark theme lock (`<html lang="he" dir="rtl" data-theme="dark">`), deep-purple/slate glass tokens (`#0b0e14`, `#131722`, `#8b5cf6`), nested-radius law (`inner = outer - padding`), and strict CSS Cascade Layers (`@layer base, dashboard, studio;`).
- **Bi-Directionally Synced:** Seamless, non-destructive triage synchronization between desktop and mobile via `localStorage` and version-aware Supabase Cloud Database (`public.sync_state`).
- **Accessible & RTL:** Flawless Hebrew RTL layout (`dir="rtl"`), BiDi numeric isolation (`direction: ltr; unicode-bidi: isolate;`), WCAG 2.2 AA touch targets (`>= 44x44px`), and pure Vanilla HTML5, CSS3, and ES6+ JavaScript.

---

## 2. Mandatory Dual-Template Build Protocol (`frontend/` -> `docs/`)
- **Source of Truth:** Always edit modular source files in `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/css/ui-fixes.css`, `frontend/js/dashboard.js`, and `frontend/templates/email_report.html`.
- **Cascade Layer Encapsulation:** Keep `docs/theme.css` wrapped inside `@layer base` so `@layer dashboard` and `@layer studio` in `dashboard.css` maintain deterministic cascade precedence. Verify brace depth `0` across stylesheets.
- **Compilation & Parity:** Compile into `docs/` via `python3 src/ui_builder.py` (or maintain strict 1:1 byte synchronization).
- **CI Guard:** Every UI change must pass `python3 tests/test_template_docs_sync.py` with zero drift between `frontend/` and `docs/`.

---

## 3. Core Interaction & Architecture Standards

### 3.1 Transparent AI Match Rationale & Compact Job Cards
1. **Header & Symmetrical Layout:** Desktop header uses `1fr auto 1fr` CSS Grid symmetry with executive briefcase brand (`IG | בקרת משרות`), compact icon-only cloud pill (`#headerCloudBtn`), centered mode switchers (`לוח משרות`, `סטודיו קריירה`), and 4 compact category cubes (`stat-cube-btn`).
2. **Rounded-md Score & BiDi Salary Badges:** Sleek `8px` radius `.badge-score` and LTR-isolated `.job-salary-chip` (`normalizeSalaryRange`), paired with deduplicated locations (`normalizeJobLocation`).
3. **Recessed 3-Anchor Requirements Box:** `.job-key-requirements` displays 3 concise evaluation anchors (`condenseMatchInsight` / `condenseFitGap`) with 3-line clamping and zero loose tag chips.
4. **Single-Row Bottom Action Bar (`.job-actions-bar`):** Compact action row pinned to card bottom (`margin-top: auto`) containing the circular emerald apply button (`.apply-icon-btn` with paper plane SVG and `[data-tooltip="הגש מועמדות"]`), 1-click Career Studio handoff (`.btn-open-in-studio` / `openJobInCareerStudio`), 32x32px icon cluster (`.card-action-icon-btn`), and details toggle (`.btn-toggle-details`).

### 3.2 Version-Aware Triage State & Supabase Cloud Sync (`public.sync_state`)
- **Non-Destructive Hydration & CAS:** User triage states (`starred`, `saved`, `rejected`, `purged`, and notes) use authenticated conditional `PATCH` (`supabaseSyncAdapter.compareAndSwap` with `version` column and conflict merge) against `public.sync_state`.
- **Version Tracking & Purge Reconciliation:** Track `ido_job_last_cloud_version` in `localStorage` (`isNewRemoteVersion`) so remote version increments trigger full state mirroring and bidirectional pruning of stale local `purged` entries, supported by manual `"סנכרן מחדש עכשיו"` in `#cloudModal`.
- **Privacy & Browser-Safe Guards:** Personal PII is excluded from client JS bundles and hydrated dynamically in-memory (`applyStudioProfileSync`); uploaded CV text lives in `sessionStorage`. Guard background polling (`25s`), `visibilitychange`, and `focus` listeners with `typeof process === 'undefined'`.

### 3.3 Career Studio Split-Pane & Focus Workbench (`careerStudioWorkspace`)
- **Compact Sticky Bars & Focus Mode:**
  - **Sticky Target Job Bar (`#studioStickyJobBar`, 44px):** Displays active target job, horizontal match threshold bar (`#studioStickyMatchBar` with 75% mark), stage status pills (`טרם הופעל` / `בעבודה` / `הושלם` / `חסום`), and Focus Mode toggle (`#btnToggleStudioFocus`) expanding the active workspace to `100%` width or restoring the `55fr / 45fr` split.
  - **Unified Top Context Bar (`.studio-context-bar`):** Houses curated starred/saved job selector (`#atsJobSelector`), URL ingestion (`#atsJobUrlInput` + `#btnFetchJobUrl`), CV upload/reset status (`#studioCurrentCvStatus`), and single-row 3-tool pipeline strip (`#studioTabAts`, `#studioTabWriter`, `#studioTabInterview` with `focusgroup="tablist nomemory"`, `hidden="until-found"`, and `beforematch`).
- **2-Column Container-Query Split (`55fr / 45fr` via `@container studio-main`):**
  - **Stage 1 — ATS Matcher (`#studioModuleAts`):** Compact 58px circular score gauge + KPI ribbon (thresholds `[80, 65, 50]`), severity-sorted gap list (`#atsSeveritySortedGapsCard`), and 3 progressive pill subtabs: Statutory Hard Gates (`#atsSubtabGatesBtn` with 4px RTL edge indicator stripe), 4-Bucket Keywords (`#atsSubtabKeywordsBtn` with 1-click `injectKeywordToWriter`), and Company Research (`#atsSubtabResearchBtn`).
  - **Stage 2 — Tailoring & Bullet Impact Auditor (`#studioModuleWriter`):** Collapsible Target Job Context card, line-by-line Bullet Impact Auditor (`#writerBulletAuditList` with tracked `קבל` / `דחה` / `ערוך` actions and in-place CV markdown replacement), 3 professional tone presets, and 3-word active-verb / 12-25 word grammar checker (`validateBulletGrammar`).
  - **Stage 3 — Interview & LinkedIn Optimizer (`#studioModuleInterview`):** Segmented control (`#interviewSegmentedBar`) toggling STAR Simulator (20/20/40/20 rubric across Gas, Solar/BESS, Mechanical, and UAV domains with dynamic factor status badges) vs. Dynamic LinkedIn SEO Optimizer (`renderLinkedInOptimizer`).
  - **Sticky Live A4 Document Viewer (45% width, `#studioStickyPreviewCol` / `#studioLiveDocViewer`):** Supports direct inline WYSIWYG editing (`contenteditable="true"` on `.live-preview-editable-text`, synced via `onLiveDocLineEdited`), instant tab switching (`#pkgTabCv`, `#pkgTabCover`, `#pkgTabTips`), mobile `<dialog id="studioMobilePreviewDialog">`, and 1-click A4 PDF print.
- **Local Python Bridge Integration:** Connects to loopback `scripts/studio_bridge.py` (`GET /api/session`, `GET /api/profile`, `POST /api/ats/analyze`, `/api/studio/tailor`, `/api/writer/tailor`, `/api/interview/evaluate`) authenticated with `X-Studio-Token` and protected by `src/url_guard.py`, with automatic graceful client-side fallback when offline.

### 3.4 Verified High-Resolution Company Logo Pipeline
1. **Tier 1:** Curated vector/PNG overrides in `docs/assets/logos/` matched via word-boundary `src/company_matcher.py`.
2. **Tier 2:** Verified official corporate logo URL or domain favicon in dark-tinted container (`rgba(255, 255, 255, 0.06)`).
3. **Tier 3:** Clean typography fallback on error (`onerror` / `naturalWidth === 0`) — strictly zero synthetic monograms or fake avatars.

---

## 4. Definition of Done
1. `python3 tests/test_template_docs_sync.py`, `python3 scripts/validate_zero_emoji.py`, `python3 scripts/project_hygiene.py --check-secrets --validate`, and all 388 Python unit tests pass.
2. Strict `dir="rtl"` alignment, BiDi number isolation, and responsive layout verified on desktop and mobile viewports.
3. Zero competitor brand names, zero loose tag chips, and zero emojis across all HTML, CSS, JS, and generated templates.
4. `localStorage` and versioned Supabase cloud sync states remain intact across reloads.
