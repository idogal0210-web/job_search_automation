---
name: ui-review
description: Review UI code for design system compliance, accessibility, coherence, and best practices in Google Antigravity projects.
---

# UI Design & Coherence Review (Antigravity Standard)

## When to Use
Use this skill to review UI code (HTML, CSS, JavaScript) for design token compliance, accessibility, visual coherence, and front-end best practices.

## Core Review Principles

### 1. Coherence & Visual Craft Laws ("One Choice Per Axis")
The primary reason a UI appears disjointed or artificial is mixed visual languages. Verify that each axis adheres to one unified system:
- **One Radius Personality:** Choose sharp (0-4px), soft (8-12px), or rounded. Avoid mixing contrasting personalities across adjacent panels and controls.
- **Nested-Radius Law:** Any element inside a rounded container must satisfy:
  `inner_radius = outer_radius - padding`
  Never use the same large radius on an inner child element as its parent, to prevent visual bulging.
- **One Accent Color:** A single primary accent color for interactive emphasis and focus states. Semantic status colors (green, red, amber) are reserved strictly for status severity.
- **Zero Emojis as UI Icons:** Absolutely no pictorial Unicode emojis or Dingbats used as list, navigation, action, or status icons. Use a single, coherent vector icon set (e.g., Phosphor Icons in `currentColor` or inline SVG).
- **Status Color = Severity, Not Decoration:** Standard/neutral states must use neutral zinc/slate tones. Bright colors are reserved strictly for states requiring user attention.
- **One Shadow Language:** Consistent light source direction, blur radius scale, and color tinting across all elevated layers.
- **Consistent Control Heights:** Buttons, inputs, and selects must share standardized height tiers (e.g., 32px compact, 38px default, 44px touch-ready).
- **Icon Family Consistency:** One icon family, fill mode, and stroke weight across the entire interface.

### 2. Design Token Compliance
- Use semantic CSS variables (`var(--bg-canvas)`, `var(--bg-surface)`, `var(--text-primary)`, `var(--accent-primary)`).
- Avoid scattered, unmanaged arbitrary hex color codes.
- Adhere to CSS Cascade Layers (`@layer base, dashboard, studio;`) to prevent specificity conflicts.

### 3. Accessibility (a11y) & WCAG AA
- Touch targets: Design goal of 44x44px for primary mobile interactive controls (WCAG 2.2 AA SC 2.5.8 minimum is 24x24px).
- Visible `focus-visible` styling with accessible contrast and glow rings on all interactive elements.
- Meaningful `aria-*` attributes, explicit `aria-label` / `title` on icon-only buttons.
- Color contrast meets WCAG AA standards (>= 4.5:1 for normal text, >= 3:1 for large text / graphical objects).
- Respect `prefers-reduced-motion`.
- All images have appropriate `alt` attributes or empty `alt=""` for purely decorative elements.
- Form inputs have associated `<label>` elements or explicit `aria-label`.

### 4. Layout, BiDi & Responsive Standards
- Directionality: Full RTL alignment for Hebrew interfaces, using CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline`).
- BiDi Text Isolation: Explicit `direction: ltr; unicode-bidi: isolate;` on numeric ranges, phone numbers, and salaries.
- No horizontal viewport overflow on mobile or desktop viewports.
- Responsive breakpoints and Container Queries (`@container`) used for decoupled split-pane workspaces.

### 5. Dual-Template Synchronization (For Dual-Template Projects)
- Any review of `frontend/` source templates must check 1:1 structural and behavioral parity with `docs/` distribution files.
- Automated parity check passes: `python3 tests/test_template_docs_sync.py`.

## Output Format
1. **Score:** Pass / Needs Improvement / Fail
2. **Key Findings:** Grouped by category with exact file and line references.
3. **Actionable Recommendations:** Concrete CSS/HTML code adjustments.
