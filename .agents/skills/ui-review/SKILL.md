---
name: ui-review
description: "Review UI code for design system compliance, Glassmorphism dark-theme tokens, CSS Cascade Layers (@layer base, dashboard, studio), WCAG 2.2 AA accessibility, iOS/mobile touch hardening, BiDi isolation, and dual-template parity in Google Antigravity projects."
---

# UI Design & Coherence Review (Antigravity Standard)

## When to Use
Use this skill to review UI code (HTML, CSS, JavaScript) for design token compliance, CSS Cascade Layer integrity, accessibility, visual coherence, and front-end best practices.

## Core Review Principles

### 1. Coherence & Visual Craft Laws ("One Choice Per Axis")
The primary reason a UI appears disjointed or artificial is mixed visual languages. Verify that each axis adheres to one unified system:
- **One Radius Personality & Nested-Radius Law:** Any element inside a rounded container must satisfy:
  `inner_radius = outer_radius - padding`
  Never use the same large radius on an inner child element as its parent (e.g., use `8px` rounded-md badges inside `14-16px` cards).
- **One Accent Color & Semantic Severity:** Primary accent (`#8b5cf6` / `#a78bfa`) is reserved for interactive emphasis and focus states. Semantic status colors (emerald, red, amber) are reserved strictly for status severity (e.g., 4px RTL edge indicator stripe on Statutory Hard Gates).
- **Zero Emojis & Zero Dingbats as UI Icons:** Absolutely no pictorial Unicode emojis or Dingbats (`U+2700..U+27BF`) used as icons or string selectors. Use Phosphor Icons (`currentColor`, neutralizing CDN `.ph-duotone.*:after` negative margins) or inline SVG.
- **One Shadow & Glass Language:** Consistent translucent glass surfaces (`--glass-bg-card`), 1px glass borders (`rgba(255, 255, 255, 0.08..0.12)`), top-edge inset highlights, and standardized shadow tokens (`--shadow-glass-sm`, `--shadow-glass-md`, `--shadow-glass-lg`).
- **Consistent 3-Tier Control Heights:** Standardize interactive controls across `32px` (compact icon clusters), `38px` (standard buttons/inputs), and `44px` (touch-ready targets).

### 2. Design Token & CSS Cascade Layer Compliance
- **Dark Theme Lock & Semantic Variables:** Verify `<html lang="he" dir="rtl" data-theme="dark">` and semantic CSS tokens (`var(--bg-canvas)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--accent-primary)`). Avoid scattered arbitrary hex codes.
- **CSS Cascade Layers (`@layer base, dashboard, studio;`):**
  - Keep `docs/theme.css` base and component rules wrapped inside `@layer base` so `@layer dashboard` and `@layer studio` in `dashboard.css` maintain deterministic cascade precedence.
  - Keep `ui-fixes.css` minimal and synchronized between `frontend/css/ui-fixes.css` and `docs/ui-fixes.css`.
  - **Brace Balance Invariant:** Verify brace depth equals `0` across every stylesheet so premature closing braces never drop `@layer studio` rules.
- **GPU-Safe Transitions:** Never use `transition: all` or unguarded heavy `backdrop-filter`; specify explicit properties (`transform`, `opacity`, `background-color`, `border-color`).

### 3. Accessibility (a11y), Touch Targets & Mobile Hardening (WCAG 2.2 AA)
- **Touch Targets (`>= 44x44px`):** Enforce `44x44px` touch boundaries on mobile controls. On compact visual icons (`.icon-button`, `.apply-icon-btn`, `.live-preview-action-btn`), expand hitboxes using `::before` / `::after` pseudo-elements without distorting visual geometry.
- **iOS WebKit Auto-Zoom Guard:** Enforce `font-size: 16px !important` across all `<input>`, `<select>`, and `<textarea>` elements under `@media (pointer: coarse), (max-width: 900px)`.
- **Hover Media Gating:** Wrap desktop hover transformations in `@media (hover: hover)` to prevent sticky hover artifacts on touch screens.
- **Keyboard Focus & Tooltips (WCAG 2.4.7 / 2.4.11):** High-contrast `:focus-visible` outlines (`2px solid` with `outline-offset`) on all interactive controls, plus `:focus-visible` activation for `[data-tooltip]` badges.
- **Micro-Typography Floor:** Maintain `>= 11px` (`11.5px` on badges/pills) for readable mobile labels; `9px` is permitted strictly inside desktop `68px` header stat cubes (`.stat-cube-label`) to prevent horizontal overflow.
- **ARIA & Semantic HTML:** Explicit `aria-label` and `title` on icon-only buttons, `[hidden]:not([hidden="until-found"])` support, and zero interactive `<button>` elements nested inside `<summary>`.

### 4. Layout, BiDi & Responsive Standards
- **Directionality & Logical Properties:** Full RTL alignment (`dir="rtl"`), using CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline`, `padding-inline-end: 28px/32px` on RTL `<select>` elements).
- **BiDi Text Isolation:** Explicit `direction: ltr !important; unicode-bidi: isolate !important;` on salary ranges (`.salary-badge`, `.job-salary-chip`), phone numbers, and numeric intervals.
- **Zero Viewport Overflow & Safe Areas:** Use `100% / max-inline-size: 100%` (never `100vw`) on `dialog.dashboard-modal-backdrop`. Unify mobile breakpoint at `900px` (matching `.mobile-bottom-nav`) and offset floating buttons/toasts by `calc(56px + 16px + env(safe-area-inset-bottom, 0px))`.
- **Container Queries & Sticky Offsets:** Use `@container studio-main` for split-pane responsiveness (`55fr / 45fr` vs. Focus Mode `100%`) and offset `.studio-sticky-preview-col` by `calc(var(--sticky-bar-h, 56px) + 16px)`.

### 5. Dual-Template Synchronization
- Any change to `frontend/` source files must be compiled via `python3 src/ui_builder.py` and pass `python3 tests/test_template_docs_sync.py`, `python3 scripts/validate_zero_emoji.py`, and `python3 scripts/project_hygiene.py --check-secrets --validate`.

## Output Format
1. **Score:** Pass / Needs Improvement / Fail
2. **Key Findings:** Grouped by category with exact file and line references.
3. **Actionable Recommendations:** Concrete CSS/HTML/JS code adjustments.
