# job_search_automation — Style Reference

Single source of truth for the visual design system of `job_search_automation` (Job Radar Dashboard and Career Studio).  
**Directionality:** Hebrew RTL (`<html lang="he" dir="rtl" data-theme="dark">`).  
**Primary CSS Sources:** `frontend/css/dashboard.css` (compiled to `docs/dashboard.css`), `frontend/css/ui-fixes.css` (compiled to `docs/ui-fixes.css`), `docs/theme.css`, `docs/fonts.css`.  
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
| Apply CTA gradient | `.btn-apply-elegant` | `linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)` | Primary external apply button on cards |
| Status — Pass / Match / New | `--status-pass` / `--dashboard-lime` | `#10b981` | Passing gates, high match scores, active "New" cube |
| Status — Warning / Starred | `--status-warn` / `--dashboard-gold` | `#f59e0b` | Gaps, warnings, active "Starred" cube |
| Status — Fail / Rejected | `--status-fail` | `#ef4444` | Hard-gate failures, inactive jobs, active "Rejected" cube |

### Base Fallback & Light Theme (`:root[data-theme="light"]`)

| Role | Token | Dark Fallback (`:root`) | Light Mode (`data-theme="light"`) |
| :--- | :--- | :--- | :--- |
| Canvas background | `--bg-canvas` / `--glass-bg-canvas` | `#0B0F19` | `#F4F6FA` |
| Surface background | `--bg-surface` | `#131B2E` | `#FFFFFF` |
| Elevated surface | `--glass-bg-elevated` | `#1A233A` | `#FFFFFF` |
| Card glass surface | `--glass-bg-card` | `rgba(19, 27, 46, 0.72)` | `linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)` |
| Subtle border | `--border-subtle` | `1px solid rgba(255, 255, 255, 0.08)` | `1px solid #E2E8F0` |
| Glass border | `--glass-border` / `--dashboard-edge` | `1px solid rgba(255, 255, 255, 0.08)` | `1px solid #CBD5E1` |
| Hover border | `--glass-border-hover` | `1px solid rgba(56, 189, 248, 0.35)` | `1px solid rgba(109, 40, 217, 0.45)` |
| Primary text | `--text-primary` | `#F8FAFC` | `#0F172A` |
| Secondary text | `--text-secondary` | `#94A3B8` | `#475569` |
| Primary accent | `--accent-primary` | `#38BDF8` | `#6D28D9` |
| Highlight accent | `--dashboard-cyan` | `#38BDF8` | `#5B21B6` |
| Status — Pass | `--status-pass` | `#34D399` | `#047857` |
| Status — Warn | `--status-warn` | `#FBBF24` | `#B45309` |
| Status — Fail | `--status-fail` | `#F87171` | `#DC2626` |

*Note:* The dark tokens (`#0B0F19`, `#131B2E`, `#F8FAFC`, `#94A3B8`, `#38BDF8`, `#34D399`, `#FBBF24`, `#F87171`) and light tokens (`#F8FAFC`, `#FFFFFF`, `#0F172A`, `#475569`, `#0369A1`, `#047857`, `#B45309`, `#DC2626`) are verified for WCAG AA `>= 4.5:1` contrast by `tests/test_phase6_design_and_a11y.py`. Keep them defined in `:root`.

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
| Micro-Label Floor | `11px` | `600`–`800` | `1.2` | `.progress-pct-chip`, `.badge-assessment`, `.studio-drop-formats`, `.map-pin-score-badge`, `.skill-tag` |
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

- **Primary Button (`.btn-apply.btn-apply-elegant`, `.dashboard-primary`):** Pill (`999px`), `min-height: 44px`, `padding: 9px 18px`, violet gradient (`#7c3aed` to `#6d28d9`) on apply CTAs. States: `@media (hover: hover)` lift (`translateY(-1px)`), `:focus-visible` high-contrast outline (`2px`–`3px` with `outline-offset`), `:active` `scale(0.98)`.
- **Secondary / Quiet Button (`.tool-btn`, `.studio-dialog-close-btn`):** Glass surface (`rgba(255, 255, 255, 0.05)`), `1px` border, `min-height: 44px` (`40px` in Studio drawers). Hover increases border opacity under `@media (hover: hover)`.
- **Compact Action Icon Button (`.card-action-icon-btn`, `.icon-button`):** `32x32px` circle (`40x40px` for `.icon-button`). Uses `::before` pseudo-element (`min-width: 44px; min-height: 44px`) on `pointer: coarse` with `gap: 12px` in `.job-actions-cluster` so touch hitboxes never overlap. Supports `[data-tooltip]` on both `:hover` and `:focus-visible`.
- **Stat Cubes (`.stat-cube-btn`):** Vertical column (`flex-direction: column`), `min-width: 52px`, `max-width: 68px` desktop (`height: 64px` 4-column grid on narrow mobile). Active state highlights border and tinted background strictly in its semantic color (`--status-pass` new, `--status-warn` starred, `--accent-primary` saved, `--status-fail` rejected).
- **Job Card (`.job-card`):** `border-radius: 20px`, `padding: 20px 22px`, flex column, `contain: layout style`. Follows the Neo-Job Board architecture with Apple-inspired double-bezel depth (specular top highlight `inset 0 1px 0 rgba(255, 255, 255, 0.12)`, ambient layered shadow `0 6px 24px rgba(0, 0, 0, 0.35)`, smooth tactile hover lift `translateY(-3px)`). Features 6 rotating pastel color themes, status date capsule (`.card-date-pill`), top triage controls (`.btn-star`, `.action-save-btn`, `.btn-copy-link`), company title stack, circular logo (`44x44px`), soft tag pills, unclipped requirements snippet (`line-height: 1.55`), and a collision-proof 2-tier footer: upper tier houses full-width salary & location (`.card-salary-location`), lower tier houses the Apple primary pill CTA (`.btn-details-pill` with chevron) alongside secondary action icons (`.apply-icon-btn`, `.btn-open-in-studio`, `.action-reject-btn`). Cards `:nth-child(n+7)` use `content-visibility: auto; contain-intrinsic-size: auto 340px`.
- **Copilot Promo Card (`.copilot-promo-card`):** Dark obsidian floating card (`#14171f`, `border-radius: 20px`) with geometric line pattern, bold white heading ("שדרג את מועמדותך בסטודיו קריירה"), and light blue pill button (`.copilot-promo-btn`).
- **Capsule Search & Filter Ribbon (`.search-capsule-ribbon`, `.search-capsule`):** Horizontal container with dark translucent capsules (`border-radius: 999px`) for free-text search, region selection, sector selection, sort selection, and modal quick-launchers.
- **Form Inputs & Selects (`input`, `select`, `textarea`, `.cloud-input`, `.ats-select`):** Custom inline SVG chevron in `ui-fixes.css` (`appearance: none`, `padding-left: 2.5rem` for RTL arrow clearance). Enforces `font-size: 16px !important` under `@media (pointer: coarse), (max-width: 900px)`.
- **Native Dialogs & Drawers (`<dialog>`):** Opened exclusively via `showModal()` (native inert backdrop, `Esc` dismissal, focus return). Always includes `aria-labelledby` (or `aria-label` when title is dynamic, e.g. `#jobDetailsModal`). Uses `overscroll-behavior: contain` on both `dialog:modal` and `dialog::backdrop` (`overflow: hidden` on `::backdrop`), and `inline-size` capped via `100%` (never `100vw`).
- **Salary & Numeric Chips (`.job-salary-chip`, `.job-tag-pill.tag-salary`, `.salary-badge`):** `direction: ltr; unicode-bidi: isolate;` (no `!important` in `dashboard.css`), `border-radius: 8px`, `font-size: 11.5px`.
- **Toast (`.dashboard-toast`) & Back-to-Top (`#btnBackToTop`):** Toast uses native `popover="manual"` with `role="status" aria-live="polite"` and `max-inline-size: min(460px, calc(100% - 32px))`. Floating controls offset above the fixed mobile bottom nav via `calc(56px + 16px + env(safe-area-inset-bottom, 0px))`.
- **Loading & Error States (`.jobs-loading-state`, `.jobs-error-banner`):** Centered `44px` circular spinner (`0.8s linear infinite`); error banner uses tinted red surface (`rgba(239, 68, 68, 0.12)`) with explicit retry button (`.btn-retry-load`).

---

## Layout

- **Max Content Width:** `1400px` centered (`.dashboard-main`, `.dashboard-sidebar`). Outer padding: `max(12px, env(safe-area-inset-top, 0px)) clamp(12px, 3vw, 16px) calc(76px + env(safe-area-inset-bottom, 0px))`.
- **Header Grid (Desktop):** Symmetrical 3-column CSS Grid (`1fr auto 1fr`) keeping the primary mode switcher (`לוח משרות` / `סטודיו קריירה`) centered at exact 50% viewport geometry between branding/tools (inline-start) and KPI stat cubes (inline-end).
- **Job Radar Grid (`#cardsContainer`):** `grid-template-columns: repeat(auto-fill, minmax(min(100%, 285px), 1fr)); gap: 12px;` (switches to 2-col or 1-col on compact screens).
- **Career Studio Split-Pane (`.studio-master-split`):** 2-column desktop layout (`minmax(0, 55fr) minmax(0, 45fr); gap: 20px;`) with sticky live A4 preview column (`.studio-sticky-preview-col` at `inset-block-start: calc(var(--sticky-bar-h, 56px) + 16px)`). Focus Mode (`.is-focus-mode`) expands active tool to `100%` single column. Uses `@container studio-main` (`min-width: 640px` / `max-width: 639px`) for internal module responsiveness.
- **Scroll Ergonomics:** Sticky job bar (`inset-block-start: 8px; z-index: 25`), `scrollbar-gutter: stable` and `overscroll-behavior: contain` on all scrollable panels/modals, and `html { scroll-padding-bottom: calc(56px + 16px + env(safe-area-inset-bottom, 0px)); }` under `@media (max-width: 900px)` so keyboard focus is never hidden behind the mobile nav.
- **Key Breakpoints:** `1119px` (Studio split-pane collapses to 1 column + mobile preview drawer button), `900px` (mobile bottom nav, touch sizing, `scroll-padding-bottom`), `767px` (compact pills/controls), `400px` (ultra-narrow phone adjustments).

---

## Do's and Don'ts

- **Do** declare all stylesheet additions inside the existing Cascade Layers (`@layer base, dashboard, studio;`) and keep brace depth at exact `0`.
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

Read `DESIGN.md` before changing any HTML, CSS, or UI JavaScript in `job_search_automation`. This is a Hebrew RTL (`dir="rtl"`), dark-mode-first (`data-theme="dark"`), vanilla HTML/CSS/JS glassmorphism workspace using `#0b0e14` canvas, `#131722` surfaces, `#8b5cf6` / `#a78bfa` violet interactive accents, and strict semantic status colors (`#10b981` pass, `#f59e0b` warn, `#ef4444` fail). Reuse existing CSS custom properties and `@layer base, dashboard, studio;` rules in `frontend/css/dashboard.css` instead of inventing inline styles or new hex codes. Maintain zero emojis, zero `transition: all`, zero `backdrop-filter:`, zero `100vw` widths, `>= 44x44px` coarse-pointer touch targets, and `>= 11px` micro-typography. After any edit in `frontend/`, run `python3 src/ui_builder.py` and confirm `tests/test_template_docs_sync.py`, `tests/test_phase6_design_and_a11y.py`, and `scripts/validate_zero_emoji.py` all pass.

---

## Open questions

Real inconsistencies found in the current CSS that are worth deciding on directly in this file before cleaning them up:

1. **Accent Hue Consolidation (Violet vs. Sky Cyan vs. Teal):** Active dark mode uses `#8b5cf6` / `#a78bfa` (`:root[data-theme="dark"]` and `.btn-apply-elegant`), while 21 hardcoded rules still use `#38bdf8` (sky cyan), `.btn-apply` base still defines teal (`#0d9488` -> `#0f766e`), and `:root` fallback defines `#7FB2E5`. **Suggested fix:** Standardize all interactive accents onto `var(--accent-primary)` (`#8b5cf6`) and `var(--dashboard-cyan)` (`#a78bfa`), keeping `#7FB2E5` only in the base `:root` token tested by `test_phase6_design_and_a11y.py`.
2. **Dark Surface Near-Duplicates:** Active dark mode defines `#0b0e14` / `#131722` / `#1a1f2e`, while dialogs and overlays still hardcode `#0b1120`, `#0f172a` (7x), and `#0b101b` (5x). **Suggested fix:** Replace those hardcoded dark blues with `var(--bg-canvas)`, `var(--bg-surface)`, and `var(--glass-bg-elevated)`.
3. **Hardcoded Status Colors vs. Tokens:** Rules mix `#34d399` (14x), `#10b981` (5x), `#47CD89`, `#fca5a5` (13x), `#f87171` (5x), and `#ef4444` (6x). **Suggested fix:** Route status borders/icons to `var(--status-pass)`, `var(--status-warn)`, and `var(--status-fail)`, reserving lighter tints (`#6ee7b7`, `#fca5a5`) only for badge foreground text over tinted backgrounds.
4. **Overlapping Responsive Breakpoints:** Media queries currently fragment across `1120px`, `1119px`, `1024px`, `950px`, `900px`, `880px` (`ui-fixes.css`), `820px`, `768px`, `767px`, `640px`, and `400px`. **Suggested fix:** Consolidate onto 3 standard widths (`1120px`, `900px`, `640px`) plus `400px` for ultra-narrow phones.
5. **Duplicate `.btn-back-to-top` Positioning:** Desktop position is defined at line 2120 (`bottom: 26px; left: 26px;`) and overridden at line 8137 (`left: 14px; bottom: 16px;`). **Suggested fix:** Keep a single canonical rule using logical properties (`inset-inline-start: 16px; inset-block-end: 16px;`).
6. **Non-Token Radii (`14px`, `18px`):** `14px` appears 22 times and `18px` is used on `dialog.studio-modal-dialog` instead of the declared scale (`8px`, `10px`, `12px`, `16px`, `20px`). **Suggested fix:** Snap `14px` to `var(--radius-control)` (`12px`) or `var(--radius-card)` (`16px`), and `18px` to `var(--radius-modal)` (`20px`).
