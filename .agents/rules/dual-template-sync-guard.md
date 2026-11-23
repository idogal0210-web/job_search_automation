---
trigger: glob
globs: "frontend/**, docs/**, src/ui_builder.py"
description: "Enforces 1:1 dual-template synchronization between frontend/ sources and docs/ build. Forbids editing docs/ in isolation."
---

# Dual-Template Synchronization Guard (`frontend/` vs. `docs/`)

## 1. Core Architecture & Single Source of Truth
In `job_search_automation`, the web application follows a strict Dual-Template architecture:
- **Source of Truth:** Modular source files under `frontend/`:
  - `frontend/templates/index.html` (layout shell, metadata slots, Career Studio split-pane)
  - `frontend/css/dashboard.css` (modular styling and design tokens)
  - `frontend/js/dashboard.js` (client-side application logic, state adapters, Supabase sync)
  - `frontend/templates/email_report.html` (externalized daily email digest template)
- **Production Build Artifacts:** Compiled distribution files under `docs/`:
  - `docs/index.html`
  - `docs/dashboard.css`
  - `docs/dashboard.js`

## 2. Invariant Rules (Iron Guards)
1. **Never Edit `docs/` in Isolation:** Modifying any file inside `docs/` directly without updating the corresponding source in `frontend/` is strictly forbidden.
2. **Mandatory 1:1 Structural Parity:** Every UI change, new DOM element, CSS class, or JS handler added to `frontend/` must be synchronized 1:1 to `docs/` (either via `src/ui_builder.py` or synchronous dual edits).
3. **Mandatory Test Verification:** Any turn that modifies UI markup, styles, or client scripts MUST verify parity by running:
   ```bash
   python3 -m unittest tests/test_template_docs_sync.py
   ```
   If this test fails, the changes are broken and cannot be declared done or pushed to GitHub.
4. **Strict Zero Emojis:** Zero emojis across all HTML templates, CSS rules, JavaScript strings, and user alerts.
