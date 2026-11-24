# Google Antigravity Project Instructions — job_search_automation

## 1. Project Overview & Mission
`job_search_automation` is an autonomous, production-grade Israeli job discovery and career automation platform tailored for Ido Gal (Mechanical Practical Engineer, Energy/Gas/Solar/UAV Operations).

The platform continuously executes:
- Multi-source job ingestion (LinkedIn, Drushim, Comeet, Greenhouse, Lever ATS boards).
- Intelligent LLM evaluation with calibrated scoring and statutory threshold checks (Gemini Flash).
- Secure, non-destructive cloud synchronization with Supabase (`public.sync_state`).
- Live dual-template dashboard deployment to GitHub Pages (`frontend/` -> `docs/`).
- Career Studio v3.0 split-screen workbench (4-stage progressive flow: ATS Hard Gates & Gaps, Keywords & Live A4 Tailoring, LinkedIn & Outreach Kit, and STAR Interview Simulator).

---

## 2. Modular Rule Architecture (`.agents/rules/`)
Project behaviors and safety constraints are partitioned into modular, single-responsibility rule files under `.agents/rules/`. Each rule is tagged with standardized YAML frontmatter for optimal context budgeting (`always_on`, `model_decision`, or `glob`).

### 2.1 Always-On Invariants (`trigger: always_on`)
These rules are loaded into context unconditionally:

- [zero-emojis.md](.agents/rules/zero-emojis.md): Strict, absolute ban on all pictorial Unicode emojis and Dingbats across all code, comments, commit messages, PR descriptions, markdown artifacts, and conversational replies.
- [pre-push-verification-and-living-docs.md](.agents/rules/pre-push-verification-and-living-docs.md): Requires clean execution of validation scripts and full unit test suite before any commit. Mandates same-commit updates to `TASKS.md`, `PROJECT_CONTEXT.md`, and `README.md`.
- [single-source-and-replaceability-guard.md](.agents/rules/single-source-and-replaceability-guard.md): Enforces single source of truth, modular component replaceability across scrapers, database persistence, UI, and bulk data lockout on `data/*.json`.
- [critical-thinking-quality.md](.agents/rules/critical-thinking-quality.md): Uncompromising quality floor. Active evaluation of proposals, identification of failure modes, and empirical verification before declaring task completion.

### 2.2 Model Decision & Contextual Rules (`trigger: model_decision`)
Loaded dynamically when relevant tool calls or architectural questions are evaluated:

- [mcp-policy.md](.agents/rules/mcp-policy.md): Standard operating procedures, safety bounds, and credit conservation rules for allowed MCP servers (`tavily`, `firecrawl`, `chrome-devtools`, `github`, `supabase_mcp`, `gemini-api-docs`). Native ATS integrations (Comeet, Greenhouse, Lever) run directly via `src/ats_client.py`.
- [project-tree-display.md](.agents/rules/project-tree-display.md): Mandates rendering the interactive Generative UI tree widget (`scripts/render_tree_widget.py` + `<agent-embed>`) whenever the user requests to inspect or view the project tree or directory hierarchy.

### 2.3 Scoped Glob Rules (`trigger: glob`)
Activated automatically when working on matched file paths:

- [dual-template-sync-guard.md](.agents/rules/dual-template-sync-guard.md): Enforces strict 1:1 structural and byte parity between `frontend/` source templates/styles and `docs/` production distribution files. Forbids editing `docs/` in isolation (`frontend/**, docs/**, src/ui_builder.py`).
- [supabase-state-integrity-guard.md](.agents/rules/supabase-state-integrity-guard.md): Guarantees non-destructive, additive upsert contracts for user triage records (`starred`, `saved`, `rejected`, notes) on Supabase Cloud Database (`supabase/**, frontend/js/**, docs/dashboard.js, scripts/*cloud*`).
- [DESIGN.md](DESIGN.md): Read `DESIGN.md` before changing any UI — single source of truth for colors, typography, spacing, component states, layout rules, and open design consolidation questions.
- [ui-invariants-symmetry-guard.md](.agents/rules/ui-invariants-symmetry-guard.md): UI invariants, desktop symmetry, dark-mode tokens, and zero synthetic logo rules for HTML/CSS/JS assets (`*.html, *.css, *.js, frontend/**, docs/**, src/ui_builder.py`).
- [realism-grounding.md](.agents/rules/realism-grounding.md): Enforces 100% candidate realism, locked original job titles, and zero credential fabrication across all tailored CV and cover letter workflows (`.agents/skills/cv-tailor/**, tools/cv_tailor/**, docs/career/cv/**, frontend/data/cv/**, output/**`).
- [cover-letter-policy.md](.agents/rules/cover-letter-policy.md): Mandates explicit user confirmation before authoring cover letters.
- [language-generation-policy.md](.agents/rules/language-generation-policy.md): Defaults tailored CV outputs to Hebrew; requires explicit user instruction for English versions.
- [file-naming-and-save-policy.md](.agents/rules/file-naming-and-save-policy.md): Enforces clear, short, standardized file naming conventions and user save confirmations.

---

## 3. Essential Verification Commands
Before concluding turns or pushing changes, verify integrity with these deterministic checks:

- Template Parity Verification:
  `python3 tests/test_template_docs_sync.py`
- Zero-Emoji Audit:
  `python3 scripts/validate_zero_emoji.py`
- Secret Detection and Schema Integrity:
  `python3 scripts/project_hygiene.py --check-secrets --validate`
- Comprehensive Unit Test Suite:
  `python3 -m unittest discover -s tests -p "test_*.py"`
- Client-Side JavaScript Syntax:
  `node -c frontend/js/dashboard.js docs/dashboard.js`
- Interactive Tree Widget Generation (Generative UI):
  `python3 scripts/render_tree_widget.py --output docs/tree_widget.html`
