---
name: ui-ux-review
description: "Unified UI design, Human-Agent Interaction (HAI), and coherence review skill for job_search_automation. Enforces design tokens, CSS Cascade Layers (@layer base, dashboard), WCAG 2.2 AA accessibility, iOS/mobile touch hardening, BiDi isolation, version-aware Supabase CAS cloud sync, verified company logos, and dual-template parity (frontend/ -> docs/)."
---

# Unified UI Design & Human-Agent Interaction Review (`job_search_automation`)

> **Architectural Base:** Combines design coherence review with [`agent-experience-interaction-designer`](file:///Users/ido/.gemini/config/skills/agent-experience-interaction-designer/SKILL.md) for the **`job_search_automation`** ecosystem.

## 1. Core UX & Visual Craft Laws ("One Choice Per Axis")
- **5-Second Scannability & Transparency:** Top matches, statutory hard gates, SCADA/PV/gas/UAV evidence, and salary provenance must be scannable in under 5 seconds via concise evaluation anchors with zero loose tag chips.
- **Nested-Radius Law:** Any element inside a rounded container must satisfy `inner_radius = outer_radius - padding` (e.g., `8px` rounded-md badges inside `14-16px` cards).
- **One Accent Color & Semantic Severity:** Primary accent is reserved for interactive emphasis and focus states; emerald, red, and amber are strictly for status severity and verification gates.
- **Zero Emojis & Zero Dingbats:** Absolutely no pictorial Unicode emojis or Dingbats (`U+2700..U+27BF`) in HTML, CSS, JS, or alerts. Use Phosphor Icons (`currentColor`) or inline SVG.
- **Consistent Control Heights:** Standardize interactive controls across ergonomic touch and desktop heights (32px, 38px, 42-44px).

## 2. Design Tokens, Cascade Layers & Dual-Template Parity
- **Source of Truth (`frontend/` -> `docs/`):** Edit only modular source files in `frontend/templates/index.html`, `frontend/css/dashboard.css`, `frontend/css/ui-fixes.css`, `frontend/js/dashboard.js`, and `frontend/templates/email_report.html`. Compile into `docs/` via `python3 src/ui_builder.py`.
- **Theme Variables:** Use semantic CSS tokens (`var(--bg-canvas)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--accent-primary)`). Avoid scattered arbitrary hex codes.
- **CSS Cascade Layers (`@layer base, dashboard;`):** Keep `docs/theme.css` base rules wrapped inside `@layer base` so `@layer dashboard` in `dashboard.css` maintains deterministic cascade precedence. Verify brace depth equals `0` across every stylesheet.
- **GPU-Safe Transitions:** Never use `transition: all` or unguarded heavy `backdrop-filter`; specify explicit properties (`transform`, `opacity`, `background-color`, `border-color`).

## 3. Accessibility (WCAG 2.2 AA), BiDi & Mobile Hardening
- **RTL & Logical Properties:** Full RTL alignment (`dir="rtl"`) using CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline`).
- **BiDi Text Isolation:** Explicit `<bdi>` wrapping or `direction: ltr !important; unicode-bidi: isolate !important;` on salary ranges (`normalizeSalaryRange`), phone numbers, percentages, and numeric intervals.
- **Touch Targets & iOS Guard:** Enforce `>= 44x44px` touch targets on mobile controls and `font-size: 16px !important` on `<input>`, `<select>`, and `<textarea>` under `@media (pointer: coarse), (max-width: 900px)`. Wrap desktop hover effects in `@media (hover: hover)`.
- **Keyboard Focus & ARIA:** High-contrast `:focus-visible` outlines, typography floor `>= 11px`, explicit `aria-label` and `title` on icon-only buttons, and zero viewport overflow (`max-inline-size: 100%`, never `100vw`).

## 4. State Sync, Bridge API & Verified Company Logos
- **Version-Aware Supabase CAS Sync (`public.sync_state`):** User triage states (`starred`, `saved`, `rejected`, `purged`, notes) use authenticated conditional `PATCH` (`supabaseSyncAdapter.compareAndSwap` with `version` column and conflict merge), bidirectional purge reconciliation, and `typeof process === 'undefined'` guards. Keep personal PII out of client JS bundles.
- **Local Python Bridge (`scripts/studio_bridge.py`):** Authenticate with `X-Studio-Token`, protect external URLs with `src/url_guard.py`, and provide graceful offline fallback.
- **Verified Company Logo Pipeline:** Tier 1 curated overrides in `docs/assets/logos/` (`src/company_matcher.py`) -> Tier 2 verified corporate URL/favicon -> Tier 3 clean typography fallback (`onerror` / `naturalWidth === 0`). Strictly zero synthetic monograms or fake avatars.

## 5. Verification & Definition of Done
Before marking any UI/UX work complete, verify zero errors across:
- `python3 tests/test_template_docs_sync.py`
- `python3 scripts/validate_zero_emoji.py`
- `python3 scripts/project_hygiene.py --check-secrets --validate`
- `node -c frontend/js/dashboard.js docs/dashboard.js`
