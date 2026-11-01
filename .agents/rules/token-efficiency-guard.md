# Token Efficiency & Scoped Execution Guard

## 1. Architectural Grounding & Zero-Scan Navigation
- Before performing broad searches or directory listings, consult `./PROJECT_CONTEXT.md` for pre-mapped entry points, module layouts, and code conventions.
- Never run wide directory scans (`find .`, `ls -R`, or unconstrained grep) across the repository. Always navigate directly to the relevant files.

## 2. Absolute Ban on Bulk Data Loading
- Never read entire raw dataset files in `data/*.json` (`jobs.json`, `sync_state.json`, `historical_catalog.json`, `evaluation_state.json`) using `read_file`.
- For inspecting job counts, categories, schema keys, or sync parity, exclusively execute the CLI tool:
  `python3 scripts/inspect_state.py [options]`
- If a specific record must be debugged, use targeted Python one-liners or `python3 scripts/inspect_state.py --job <id>` to extract only the single object (under 30 lines) into context.

## 3. Frontend & CSS Task Scoping
- In all UI, styling, layout, responsive, and accessibility tasks:
  - Absolute data lockout: Do not touch or inspect any files in `data/`. Rely strictly on HTML markup and CSS classes.
  - Scoped reading: Do not load full 4,000+ line HTML files. Always pass `StartLine` and `EndLine` to `read_file` to inspect only the target component.
  - Dual-template symmetry: Keep `frontend/templates/index.html` and `docs/index.html` in 1:1 synchronization.
  - Targeted verification: Run only `tests/test_mobile_css.py` and `tests/test_template_docs_sync.py`.

## 4. Scoped Backend & Logic Tasks
- When modifying scrapers or AI scoring logic, inspect only the specific module under `src/` and its matching test file under `tests/`.
- Mock external network calls and large datasets in tests; do not invoke live scraping runs during routine debugging.

## 5. Output Minimization
- Suppress verbose command outputs. Do not dump megabytes of test traces or stdout logs into the conversation context.
- Keep responses concise, direct, and focused on the requested outcome.
