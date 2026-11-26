# job_search_automation — Style Reference

Single source of truth for the visual design system of `job_search_automation` (Job Radar Dashboard and Career Studio).  
**Directionality:** Hebrew RTL (`<html lang="he" dir="rtl" data-theme="dark">`).  
**Primary CSS Sources:** `frontend/css/dashboard.css` (compiled to `docs/dashboard.css`), `frontend/css/ui-fixes.css` (compiled to `docs/ui-fixes.css`), `docs/theme.css`, `docs/fonts.css`.  
**Architecture Layers:** Structured strictly under `@layer base, dashboard, studio;` (with brace depth = 0 across all layers).  
**Editing Note:** Update tokens or rules in this file first when changing the visual direction, then propagate changes into `frontend/` and compile to `docs/` via `python3 src/ui_builder.py`.

---

## Tokens — Colors

### Active Dark Theme (`:root[data-theme="dark"]` — Default)

| Role | Token | Value | Where It Is Used |
| :--- | :--- | :--- | :--- |
| Canvas background | `--bg-canvas` / `--glass-bg-canvas` | `#0b0e14` | Full-page background (`html`, `body`) |
| Surface background | `--bg-surface` | `#131722` | Modals, inputs, nested panels |
| Elevated surface | `--glass-bg-elevated` | `#1a1f2e` | Tooltips, dropdown menus, raised drawers |
| Translucent base | `--glass-bg-base` | `rgba(19, 23, 34, 0.6)` | Header shell, secondary toolbars |
| Card glass surface | `--glass-bg-card` / `--dashboard-glass` | `linear-gradient(180deg, rgba(30, 36, 48, 0.4) 0%, rgba(19, 23, 34, 0.8) 100%)` | Job cards, Career Studio cards, stat cubes |
| Subtle border | `--border-subtle` | `1px solid rgba(255, 255, 255, 0.04)` | Dividers, inner rows |
| Glass border | `--glass-border` / `--dashboard-edge` | `1px solid rgba(255, 255, 255, 0.05)` | Cards, panels, inputs |
| Hover border | `--glass-border-hover` | `1px solid rgba(167, 139, 250, 0.3)` | Interactive card and button hover borders |
| Top inset highlight | `--glass-highlight` | `inset 0 1px 0 0 rgba(255, 255, 255, 0.05)` | Top specular edge on glass cards |
| Primary text | `--text-primary` / `--dashboard-text` | `#ffffff` | Headings, job titles, active labels |
| Secondary / muted text | `--text-secondary` / `--dashboard-muted` | `#8b92a5` | Subtitles, metadata, timestamps, helper copy |
| Primary interactive accent | `--accent-primary` | `#8b5cf6` | Primary CTAs, active borders, focus glow |
| Highlight accent | `--dashboard-cyan` | `#a78bfa` | Company names, active tabs, Studio icon action |
| Apply CTA gradient | `.btn-apply-elegant` | `linear-gradient(180deg, rgba(2, 132, 199, 0.95) 0%, rgba(3, 105, 161, 0.85) 100%)` | Primary external apply button on cards (Liquid Glass) |
| Liquid Glass Button | `.btn-liquid-glass`, `.ats-primary-btn` | Dynamic refraction + specular insets | Primary CTAs, Career Studio action buttons |
| Status — Pass / Match / New | `--status-pass` / `--dashboard-lime` | `#10b981` | Passing gates, high match scores, active "New" cube |
| Status — Warning / Starred | `--status-warn` / `--dashboard-gold` | `#f59e0b` | Gaps, warnings, active "Starred" cube |
| Status — Fail / Rejected | `--status-fail` | `#ef4444` | Hard-gate failures, inactive jobs, active "Rejected" cube |

### Base Fallback & Light Theme (`:root[data-theme="light"]`)

| Role | Token | Dark Fallback (`:root`) | Light Mode (`data-theme="light"`) |
| :--- | :--- | :--- | :--- |
| Canvas background | `--bg-canvas` / `--glass-bg-canvas` | `#0B0F19` | `#F8FAFC` (enforced on `html`, `body`, `.dashboard-app`) |
| Surface background | `--bg-surface` | `#131B2E` | `#FFFFFF` |
| Elevated surface | `--glass-bg-elevated` | `#1A233A` | `#FFFFFF` |
| Card glass surface | `--glass-bg-card` | `rgba(19, 27, 46, 0.72)` | `linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)` |
| Empty state / Sidebar card | `.empty-state`, `.dashboard-card` | `--glass-bg-card` | `#FFFFFF`, border `#CBD5E1`, shadow `0 4px 16px rgba(15,23,42,0.05)` |
| Subtle border | `--border-subtle` | `1px solid rgba(255, 255, 255, 0.08)` | `1px solid #E2E8F0` |
| Glass border | `--glass-border` / `--dashboard-edge` | `1px solid rgba(255, 255, 255, 0.08)` | `1px solid #CBD5E1` |
| Hover border | `--glass-border-hover` | `1px solid rgba(56, 189, 248, 0.35)` | `1px solid rgba(29, 78, 216, 0.45)` |
| Primary text | `--text-primary` | `#F8FAFC` | `#0F172A` |
| Secondary text | `--text-secondary` | `#94A3B8` | `#475569` |
| Primary accent | `--accent-primary` | `#38BDF8` | `#1D4ED8` |
| Highlight accent | `--dashboard-cyan` | `#38BDF8` | `#1E3A8A` |
| Status — Pass | `--status-pass` | `#34D399` | `#047857` |
| Status — Warn | `--status-warn` | `#FBBF24` | `#B45309` |
| Status — Fail | `--status-fail` | `#F87171` | `#991B1B` |

*Note:* The dark tokens (`#0B0F19`, `#131B2E`, `#F8FAFC`, `#94A3B8`, `#38BDF8`, `#34D399`, `#FBBF24`, `#F87171`) and light tokens (`#F8FAFC`, `#FFFFFF`, `#0F172A`, `#475569`, `#0369A1`, `#047857`, `#B45309`, `#991B1B`) are verified for WCAG AA `>= 4.5:1` contrast by `tests/test_phase6_design_and_a11y.py`. Keep them defined in `:root`.

---

## Tokens — Typography

### Font Families
- **Primary UI (`--font-ui`):** `'Assistant', 'Google Sans', Arial, sans-serif` (applied globally on `html:lang(he) body`; `'Google Sans'` WOFF2 weights 400/500/600/700 self-hosted in `docs/assets/fonts/`).
- **Technical / Monospace (`--font-mono`):** `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace` (numeric IDs, code snippets, salary/score telemetry).

### Type Scale

| Level | Size | Weight | Line Height | Where It Is Used |
| :--- | :--- | :--- | :--- | :--- |
| Modal / Drawer Title | `18px` (`1.12rem`) | `600`–`800` | `1.25` | `.modal-heading`, `.studio-drawer-title` |
| Card / Job Title | `14.5px` | `600` | `1.25` | `.job-title-text` |
| Primary CTA / Body | `14px` | `500`–`600` | `1.45` | `.btn-apply`, body copy, `.dashboard-toast` |
| Standard Controls | `13px`–`13.5px` | `600` | `1.3` | `.tool-btn`, filter inputs/selects (desktop) |
| Mobile / Coarse Inputs | `16px !important` | `400`–`500` | `1.3` | All `<input>`, `<select>`, `<textarea>` under `@media (pointer: coarse), (max-width: 900px)` (prevents iOS auto-zoom) |
| Company Name / Meta | `12px`–`12.5px` | `600`–`700` | `1.35` | `.job-company-name`, `.evidence-item`, `.q-chip` |
| Badges & Chips | `11.5px` | `700` | `1.2` | `.badge-score`, `.job-salary-chip`, `.badge-importance` |
| Micro-Label Floor | `11px` | `600`–`800` | `1.2` | `.progress-pct-chip`, `.badge-assessment`, `.studio-drop-formats`, `.skill-tag` |
| Desktop Stat Cube Label | `9px` (strict exception) | `600` | `1.0` | `.stat-cube-label` strictly inside `68px` header KPI cubes |

---

## Tokens — Spacing & Shapes

### Spacing Scale
- `--space-1`: `4px` (tight icon-text gaps, micro padding)
- `--space-2`: `8px` (chip gaps, control padding, compact clusters)
- `--space-3`: `16px` (card internal padding, modal margins, standard grid gaps)
- `--space-4`: `24px` (section separation, major panel padding)
- `--space-5`: `32px` (workspace breathing room)
- `--space-6`: `48px` (large empty-state / vertical breaks)

### Control Heights (3-Tier System)
- `--control-h-sm`: `32px` — Compact card icon clusters (`.card-action-icon-btn`; expands to `44x44px` invisible hitbox via `::before` on `pointer: coarse`).
- `--control-h-md`: `38px` — Standard desktop inputs, compact chips, secondary buttons.
- `--control-h-lg`: `44px` — Touch-ready targets, primary CTAs (`.btn-apply`, `.tool-btn`, `.nav-btn`, `.mode-switch-btn`).
- `--sticky-bar-h`: `56px` — Sticky Career Studio job strip and mobile bottom navigation height.

### Corner Radii (Nested-Radius Law: `inner_radius = outer_radius - padding`)
- `--radius-base` / `--radius-badge`: `8px` — Score badges, salary chips, inner tags (`6px` for `.job-tag-pill`).
- `--radius-inner`: `10px` — Company logo box (`.job-company-logo`), inner sub-cards, `.evidence-item`.
- `--radius-control`: `12px` — Inputs, selects, dropdowns, compact buttons.
- `--radius-card`: `16px` — Job cards (`.job-card`), stat cubes, Studio module panels.
- `--radius-modal`: `20px` — Dialog containers (`.dashboard-modal-box`).
- Pill / Circle: `999px` (`.tool-btn`, `.btn-apply`, `.modal-close-pill`, `.studio-drop-formats`), `50%` (`.card-action-icon-btn`, `.icon-button`, `.btn-back-to-top`).

### Borders & Shadows
- **Borders:** `1px solid` glass edges (`--glass-border` -> `--glass-border-hover` on hover); `4px` RTL edge accent stripe on statutory hard-gate cards.
- **Shadows (Dark Mode):**
  - `--shadow-glass-sm`: `0 4px 12px rgba(0, 0, 0, 0.2)` — Subtle buttons, chips.
  - `--shadow-glass-md`: `0 8px 24px rgba(0, 0, 0, 0.4)` — Cards, header, resting surfaces.
  - `--shadow-glass-lg`: `0 16px 48px rgba(0, 0, 0, 0.6)` — Modals, drawers, overlays.
  - `--shadow-glass-glow`: `0 0 24px rgba(139, 92, 246, 0.15)` — Focused/active purple highlight.
  - `--shadow-floating`: `0 8px 32px rgba(0, 0, 0, 0.6)` — Floating toast and Back-to-Top button.

---

## Components

- **Brand Identity & Header Wordmark (`.brand-logo-autojob`, `.brand-logo-text`, `.brand-icon-pill`):** Official AutoJob brand identity with strict LTR isolation (`dir="ltr"`, `aria-label="AutoJob"`), rendered in Plus Jakarta Sans (weight 900, -0.5px letter-spacing).
  - **Dark Mode:** Renders `.brand-logo-auto` in crisp white (`#FFFFFF`) and `.brand-logo-job` in an ambient cyan-to-emerald gradient (`linear-gradient(135deg, #38BDF8 0%, #10B981 100%)`) with soft cyan drop-shadow (`drop-shadow(0 2px 8px rgba(56, 189, 248, 0.35))`).
  - **Light Mode:** Dynamically switches to deep slate (`#0F172A`) for `.brand-logo-auto` and high-contrast emerald-teal (`linear-gradient(135deg, #0284C7 0%, #059669 100%)`) for `.brand-logo-job` adhering to WCAG AA standards.
  - **Icon Pill & Utility Partitioning:** Paired with a 38x38px capsule (`.brand-icon-pill`) housing a Phosphor briefcase in theme token `var(--dashboard-cyan, #38BDF8)`. Utility controls (`#headerCloudBtn`, `#themeToggleBtn`) are partitioned into `.brand-utility-group` with a subtle 1px vertical divider (`border-inline-start: 1px solid rgba(255, 255, 255, 0.12)`) and 8px padding, giving visual breathing room to the brand.
  - **Contained Sync Dot:** `.sync-status-dot` is strictly contained inside `.cloud-pill.header-cloud-btn` (`position: relative; height: 28px;`) at `top: 3px; left: 3px; width: 6px; height: 6px;` with cyan glow, eliminating any stray viewport dot.
  - **Vector Assets:** Scalable SVG assets are maintained at `frontend/assets/images/autojob_logo.svg` (520x100) and `autojob_icon.svg` (100x100), mirrored in `docs/assets/images/`.
- **Primary Button (`.btn-apply.btn-apply-elegant`, `.ats-primary-btn`, `.btn-liquid-glass`, `.dashboard-primary`):** Pill (`999px`), `min-height: 44px`, `padding: 9px 18px`. Implements the Liquid Glass system:
  - **Dark Mode:** Deep cyan/sky liquid gradients (`linear-gradient(180deg, rgba(2, 132, 199, 0.95) 0%, rgba(3, 105, 161, 0.85) 100%)`), 1px cyan glass border (`rgba(56, 189, 248, 0.45)`), specular top inset (`inset 0 1px 1px rgba(255, 255, 255, 0.45)`), deep bottom shadow (`inset 0 -1px 1px rgba(0, 0, 0, 0.5)`), and ambient outer glow (`0 0 16px rgba(56, 189, 248, 0.25)`).
  - **Light Mode:** High-clarity cobalt liquid gradients (`linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%)`), crisp 1px `#1E40AF` border, white specular top highlight (`inset 0 1px 1px 0 rgba(255, 255, 255, 0.65)`), and soft ambient shadow (`0 4px 12px rgba(29, 78, 216, 0.20)`).
  - **Tactile Interaction:** States: `@media (hover: hover)` lift (`translateY(-1.5px)` with brightness `1.12`), `:focus-visible` high-contrast outline (`2px`–`3px` with `outline-offset`), `:active` tactile depression (`translateY(1px) scale(0.985)` with deepened inset shadow).
- **Secondary / Quiet Button (`.tool-btn`, `.studio-dialog-close-btn`):** Glass surface (`rgba(255, 255, 255, 0.05)`), `1px` border, `min-height: 44px` (`40px` in Studio drawers). Hover increases border opacity under `@media (hover: hover)`.
- **Compact Action Icon Button (`.card-action-icon-btn`, `.icon-button`):** `32x32px` circle (`40x40px` for `.icon-button`). Uses `::before` pseudo-element (`min-width: 44px; min-height: 44px`) on `pointer: coarse` with `gap: 12px` in `.job-actions-cluster` so touch hitboxes never overlap. Supports `[data-tooltip]` on both `:hover` and `:focus-visible`.
- **Stat Cubes (`.stat-cube-btn`):** Vertical column (`flex-direction: column`), `min-width: 52px`, `max-width: 68px` desktop (`height: 64px` 4-column grid on narrow mobile). Active state highlights border and tinted background strictly in its semantic color (`--status-pass` new, `--status-warn` starred, `--accent-primary` saved, `--status-fail` rejected).
- **Job Card (`.job-card`):** `border-radius: 20px`, `padding: 20px 22px`, flex column, `contain: layout style`. Follows the Neo-Job Board architecture with Apple-inspired double-bezel depth (specular top highlight `inset 0 1px 0 rgba(255, 255, 255, 0.12)`, ambient layered shadow `0 6px 24px rgba(0, 0, 0, 0.35)`, smooth tactile hover lift `translateY(-3px)`). Features 6 rotating pastel color themes, status date capsule (`.card-date-pill`), top triage controls (`.btn-star`, `.action-save-btn`, `.btn-copy-link`), company title stack, circular logo (`44x44px`), soft tag pills, unclipped requirements snippet (`line-height: 1.55`), and a collision-proof 2-tier footer: upper tier houses full-width salary & location (`.card-salary-location`), lower tier houses the Apple primary pill CTA (`.btn-details-pill` with chevron) alongside secondary action icons (`.apply-icon-btn`, `.action-reject-btn`). Cards `:nth-child(n+7)` use `content-visibility: auto; contain-intrinsic-size: auto 340px`.
- **Career Studio v3.0 Production Architecture (`#careerStudioWorkspace`, `@layer studio`):** Built under `@layer studio` with complete decoupling from the Job Radar feed. Powered by an App Switcher in the top header (`#modeJobRadarBtn` and `#modeCareerStudioBtn`). Operates a 4-stage progressive workbench pipeline:
  1. *Stage 1: ATS Hard Gates & Gaps* (`#stageHardGatesBtn`) — Automated statutory gate validation, missing qualification gaps, and deterministic pass/fail flags.
  2. *Stage 2: Keywords & Live A4 Tailoring* (`#stageTailorBtn`) — Side-by-side keyword alignment and real-time printable A4 CV preview with candidate-realistic formatting.
  3. *Stage 3: LinkedIn & Outreach Kit* (`#stageOutreachBtn`) — Contextual networking messages, referral request templates, and cold outreach scripts.
  4. *Stage 4: STAR Interview Simulator* (`#stageInterviewBtn`) — Structured behavioral interview practice based on vacancy requirements.
- **Capsule Search & Filter Ribbon (`.search-capsule-ribbon`, `.search-capsule`, `.contextual-actions`):** Horizontal container with dark translucent capsules (`border-radius: 999px`) for free-text search, region selection, sector selection, sort selection, and modal quick-launchers. Includes contextual actions and filter reset button (`.btn-reset-filters`).
- **Screen-Reader Utility (`.visually-hidden`):** Standard zero-pixel accessibility clipping utility in `@layer base` ensuring screen-reader text (`#themeToggleLabel`, `.dashboard-header-title`) is accessible to assistive technologies without visual text bleed.
- **Form Inputs & Selects (`input`, `select`, `textarea`, `.cloud-input`, `.ats-select`):** Custom inline SVG chevron in `ui-fixes.css` (`appearance: none`, `padding-left: 2.5rem` for RTL arrow clearance). Enforces `font-size: 16px !important` under `@media (pointer: coarse), (max-width: 900px)`.
- **Native Dialogs & Drawers (`<dialog>`):** Opened exclusively via `showModal()` (native inert backdrop, `Esc` dismissal, focus return). Always includes `aria-labelledby` (or `aria-label` when title is dynamic, e.g. `#jobDetailsModal`, `#studioMobilePreviewDialog`). Uses `overscroll-behavior: contain` on both `dialog:modal` and `dialog::backdrop` (`overflow: hidden` on `::backdrop`), and `inline-size` capped via `100%` (never `100vw`).
- **Salary & Numeric Chips (`.job-salary-chip`, `.job-tag-pill.tag-salary`, `.salary-badge`):** `direction: ltr; unicode-bidi: isolate;` (no `!important` in `dashboard.css`), `border-radius: 8px`, `font-size: 11.5px`.
- **Toast (`.dashboard-toast`) & Back-to-Top (`#btnBackToTop`):** Toast uses native `popover="manual"` with `role="status" aria-live="polite"` and `max-inline-size: min(460px, calc(100% - 32px))`. Floating controls offset above the fixed mobile bottom nav via `calc(56px + 16px + env(safe-area-inset-bottom, 0px))`.
- **Loading & Error States (`.jobs-loading-state`, `.jobs-error-banner`):** Centered `44px` circular spinner (`0.8s linear infinite`); error banner uses tinted red surface (`rgba(239, 68, 68, 0.12)`) with explicit retry button (`.btn-retry-load`).

---

## Layout

- **Max Content Width:** `1400px` centered (`.dashboard-main`, `.dashboard-sidebar`). Outer padding: `max(12px, env(safe-area-inset-top, 0px)) clamp(12px, 3vw, 16px) calc(76px + env(safe-area-inset-bottom, 0px))`.
- **Header Grid (Desktop):** Symmetrical 3-column CSS Grid (`1fr auto 1fr`) housing AutoJob branding with utility action group (`#headerCloudBtn`, `#themeToggleBtn`) on inline-start, centralized mode switcher (`#modeSwitchContainer` housing `#modeJobRadarBtn` and `#modeCareerStudioBtn`) with screen-reader title in the center, and KPI stat cubes on inline-end.
- **Job Radar Grid (`#cardsContainer`):** `grid-template-columns: repeat(auto-fill, minmax(min(100%, 285px), 1fr)); gap: 12px;` (switches to 2-col or 1-col on compact screens).
- **Career Studio Split-Screen Grid (`#careerStudioWorkspace`):** 55/45 split on desktop (`min-width: 1120px`), pairing the interactive stage workbench (55%) with a contextual right inspector (45%) that swaps between live A4 document preview and job brief / STAR prompt details. Collapses to 1 column on screens `< 1120px` with a floating trigger for `<dialog id="studioMobilePreviewDialog">`.
- **Scroll Ergonomics:** Sticky job bar (`inset-block-start: 8px; z-index: 25`), `scrollbar-gutter: stable` and `overscroll-behavior: contain` on all scrollable panels/modals, and `html { scroll-padding-bottom: calc(56px + 16px + env(safe-area-inset-bottom, 0px)); }` under `@media (max-width: 900px)` so keyboard focus is never hidden behind the mobile nav.
- **Key Breakpoints:** `1119px` (Studio split-pane collapses to 1 column + mobile preview drawer button), `900px` (mobile bottom nav, touch sizing, `scroll-padding-bottom`), `767px` (compact pills/controls), `400px` (ultra-narrow phone adjustments).

---

## Do's and Don'ts

- **Do** declare all stylesheet additions inside the existing Cascade Layers (`@layer base, dashboard, studio;`) and keep brace depth at exact `0` across all layers.
- **Do** edit only `frontend/` source files and immediately compile to `docs/` with `python3 src/ui_builder.py`, then verify via `python3 tests/test_template_docs_sync.py`.
- **Do** wrap desktop hover transforms in `@media (hover: hover)` so touch devices never get sticky hover artifacts.
- **Do** use CSS Logical Properties (`inline-size`, `block-size`, `margin-inline`, `padding-inline`, `inset-block-start`) and `100%` (never `100vw`) on overlays and toasts.
- **Do** isolate numeric/salary ranges with `direction: ltr; unicode-bidi: isolate;` (without `!important` in `dashboard.css`).
- **Do** use Phosphor Icons (`<i class="ph-bold ..."` / `ph-duotone`) with `aria-hidden="true"` inside labeled controls.
- **Don't** use emojis or Unicode Dingbats (`U+2700..U+27BF`) anywhere in HTML, CSS, JS, or UI copy.
- **Don't** use `transition: all` or `backdrop-filter:` in `dashboard.css` (both are actively forbidden by `tests/test_phase6_design_and_a11y.py`).
- **Don't** use `direction: ltr !important;` in `dashboard.css` (forbidden by `tests/test_phase6_design_and_a11y.py`).
- **Don't** add `role="dialog"`, `aria-modal`, custom focus traps, or `overflow: hidden` body locks to native `<dialog>` elements opened via `showModal()`.
- **Don't** invent or render synthetic company letter-avatar monograms; hide broken logos cleanly via `onerror`.
- **Don't** drop readable badge or label text below `11px` (only desktop `68px` `.stat-cube-label` may use `9px`).

---

## Agent Prompt Guide

Read `DESIGN.md` before changing any HTML, CSS, or UI JavaScript in `job_search_automation`. This is a Hebrew RTL (`dir="rtl"`), dark-mode-first (`data-theme="dark"`), vanilla HTML/CSS/JS glassmorphism workspace using `#0b0e14` canvas, `#131722` surfaces, `#8b5cf6` / `#a78bfa` violet interactive accents, and strict semantic status colors (`#10b981` pass, `#f59e0b` warn, `#ef4444` fail). In Light Mode (`data-theme="light"`), canvas uses clean slate `#F8FAFC`, `#FFFFFF` cards with `#CBD5E1` borders, and cobalt interactive accents (`#1D4ED8` / `#1E3A8A`). Reuse existing CSS custom properties and `@layer base, dashboard, studio;` rules in `frontend/css/dashboard.css` instead of inventing inline styles or new hex codes. Maintain zero emojis, zero `transition: all`, zero `backdrop-filter:`, zero `100vw` widths, `>= 44x44px` coarse-pointer touch targets, and `>= 11px` micro-typography. After any edit in `frontend/`, run `python3 src/ui_builder.py` and confirm `tests/test_template_docs_sync.py`, `tests/test_phase6_design_and_a11y.py`, and `scripts/validate_zero_emoji.py` all pass.

---

## Resolved Design Decisions (Consolidated & Implemented)

All previously identified CSS inconsistencies have been unified in `frontend/css/dashboard.css` (compiled to `docs/dashboard.css`):

1. **Accent Hue Consolidation (Resolved):** All interactive accents across buttons, chips, and states standardized onto `var(--accent-primary)` and `var(--dashboard-cyan)`. Teal gradients in base `.btn-apply` migrated to token-driven gradients. Base `:root` fallback retains verified `#7FB2E5` and contrast tokens tested by `tests/test_phase6_design_and_a11y.py`.
2. **Dark Surface Near-Duplicates (Resolved):** Hardcoded dialog and overlay dark blues replaced with semantic surface tokens (`var(--bg-canvas)`, `var(--bg-surface)`, and `var(--glass-bg-elevated)`).
3. **Hardcoded Status Colors vs. Tokens (Resolved):** Routed status icons, borders, and indicators to `var(--status-pass)`, `var(--status-warn)`, and `var(--status-fail)`.
4. **Responsive Breakpoints Unified (Resolved):** Consolidated fragmented media queries onto the 3 standard widths (`1120px`, `900px`, `640px`) plus `400px` for ultra-narrow phones.
5. **Canonical `.btn-back-to-top` Positioning (Resolved):** Removed duplicate declaration. Single canonical rule now enforces CSS Logical Properties (`inset-inline-start: 16px; inset-block-end: 16px;`).
6. **Non-Token Radii Snapped (Resolved):** 14px control and container radii snapped to `var(--radius-control)` (12px) or `var(--radius-card)` (16px). 18px dialog radii snapped to `var(--radius-modal)` (20px).
7. **Light Mode Canvas & Component Surfaces (Resolved):** Neutralized dark bleed-through in Light Mode by enforcing `#F8FAFC` canvas across `:root[data-theme="light"]`, `html[data-theme="light"]`, and `.dashboard-app`. Styled `.dashboard-card`, `.empty-state`, headers, and subheaders in crisp white surfaces (`#FFFFFF`), `#CBD5E1` borders, and high-contrast dark typography (`#0F172A` / `#475569`). Dynamic Chart.js theme reactivity integrated with `applyDashboardTheme`.
8. **Career Studio v3.0 Production Architecture (Resolved):** Successfully deployed the decoupled 4-stage Career Studio workbench (`#careerStudioWorkspace`) under `@layer studio` (TASK-98), featuring an App Switcher, 55/45 split desktop layout, contextual swapping side column (Live A4 Preview vs. Job Brief), and mobile preview drawer dialog. Preserves 100% candidate realism and backend bridge compatibility with zero interference to Job Radar triage.
9. **AutoJob Brand Identity & Vector Wordmark (Resolved):** Replaced legacy monogram ("IG | בקרת משרות") with official "AutoJob" wordmark (TASK-101) with strict LTR isolation (`dir="ltr"`), theme-reactive typography (Plus Jakarta Sans 900), Phosphor cyan briefcase capsule, `.brand-utility-group` divider, contained sync dot (TASK-102), and standalone scalable SVG assets (`autojob_logo.svg`, `autojob_icon.svg`).
10. **Contextual Action Toolbar & Chart Chip Stabilization (Resolved):** Standardized filter ribbon actions and contextual toolbar (`.contextual-actions`), unified chip click targets and RTL spacing, and stabilized Chart.js distribution chips (TASK-97).
11. **Career Studio Ergonomics & Live Document Hardening (Resolved - TASK-105):** Added CV pill ellipsis truncation (`max-width: 160px;`) with inline reset button (`#studioBtnResetCv`), active vacancies counter badge (`.studio-job-count-badge`), Stage 1 balanced two-row input grouping with 1-click sample vacancy loader (`.studio-quick-sample-btn`), full-width ATS Analyze CTA button (`.studio-btn-full`), elevated A4 document preview shadow (`0 12px 36px rgba(0, 0, 0, 0.35)`), bullet injection glow animation (`.bullet-just-injected`), and Stage 4 STAR Simulator 2-minute interview countdown timer (`#studioStarTimerBtn`).
12. **Job Details Modal Action Bar Isolation & Company Logo Fidelity (Resolved - TASK-108):** Hardened `.job-modal-bottom-bar .job-actions-bottom-row` flexbox layout, standardizing `.btn-apply.btn-apply-elegant` (`flex: 1 1 auto; height: 44px; border-radius: 12px;` full emerald gradient) alongside `.btn-open-in-studio` (`flex: 0 0 auto; height: 44px; border-radius: 12px;` purple accent) and `.btn-alt-source` (`height: 44px; border-radius: 12px;` gold accent) with zero visual overlap or clipping. Installed verified official company logo for ESP710 in `frontend/assets/logos/esp710.png` and `docs/assets/logos/esp710.png` to prevent WordPress fallback, and replaced raw `[OK]` bracket strings in `formatJobMatchAndGaps` with fluent Hebrew status text.
13. **Sector Distribution Chart Token Palette & Typography Stabilization (Resolved - TASK-109):** Standardized `#chartTitle` to fixed concise `התפלגות תחומים` with `white-space: nowrap;`, preventing 2-line header wrapping and redundant category repetitions. Converted Chart.js bar palette from hardcoded rainbow colors to unified design tokens (`rgba(56, 189, 248, 0.85)` / `#38bdf8` in Dark Mode, `#0284c7` in Light Mode) with flat base geometry (`borderSkipped: 'bottom'`). Upgraded footer and axis font sizes to 12px and expanded share button touch target (`min-height: 28px; padding: 4px 10px;`).
14. **Search & Filter Ribbon Accessibility, Icon Coherence & Token Compliance (Resolved - TASK-110):** Restored screen-reader accessibility across search and filter dropdowns by adding the `.sr-only` utility in `@layer base` and removing `style="display:none;"` from all `<label>` tags. Standardized all ribbon icons to Phosphor Duotone (`ph-duotone ph-magnifying-glass`, `ph-duotone ph-x`, and semantic `ph-duotone ph-arrows-down-up` for sorting). Replaced inline styles and hardcoded hex values on action buttons with dedicated `.ribbon-tool-btn` styles (`.btn-duplicates`, `.btn-inactive`, `.btn-reset`). Capped desktop search width to 380px (`max-width: 380px`) to prevent empty void space, and added mobile responsive rules (`@media (max-width: 768px)`) for clean vertical ribbon stacking.
