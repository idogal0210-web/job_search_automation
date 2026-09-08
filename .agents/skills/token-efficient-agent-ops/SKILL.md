---
name: token-efficient-agent-ops
description: Minimizes token and context consumption during agent work without reducing task quality, scope, or correctness. Use for any coding, refactoring, research, scheduled task, subagent run, or automation where context is large, the conversation is long, runs are repeated, or credits/quota are limited.
---

# Token-Efficient Agent Operations (Antigravity Edition)

Reduce tokens spent per unit of *completed, verified* work. Efficiency is a
constraint on **how** work is done, never on **whether** it is done.

## Prime Directive

**Correctness > completeness > efficiency.** If saving tokens would risk a
wrong answer, a skipped verification, a partial edit, or a silent change of
scope — spend the tokens. Say so in one line and continue.

## Never Sacrifice (Hard Floor)

Do not skip, shorten, or "optimize away" any of the following:

- Reading the exact code being modified before modifying it (via targeted range read).
- Running builds, tests, linters, or type checks that the task requires.
- Verifying that an edit actually applied and the result is coherent.
- Requirements stated by the user, including ones that seem redundant.
- Error output, stack traces, and failing test details when diagnosing.
- Asking a blocking clarification when the task is genuinely ambiguous.

Guessing to avoid a file read is a false saving: a wrong edit costs one bad
diff plus the debugging, the re-read, and the fix.

## Intake: Pull the Minimum Sufficient Context

1. **Locate before loading.** Use `grep_search` and `find_by_name` to find exact
   files and line numbers. Never open a full file to discover whether it is relevant.
2. **Read ranges, not files.** Use `view_file` with `StartLine` and `EndLine`
   parameters to read only the function, class, or hunk plus a small margin (20-50 lines).
   Widen only when the read proves insufficient.
3. **Read once.** Never re-read a file already in the current context unless
   it changed. If it changed, read only the modified line range.
4. **Prefer structure over prose.** Directory listings (`list_dir`), signatures, and
   data schemas usually answer the question that reading a full file would.
5. **Stop when the question is answered.** Additional confirming context is
   the most common source of waste.

Exception: for a wide refactor across many call sites, one broad search that
returns all matches is cheaper than iterative discovery. Batch it.

## Tool Calls & Execution: Targeted & Sandbox-Friendly

- **Sandbox-Friendly Commands:** Prefer separate, discrete command invocations over
  complex chaining (`&&`, `||`, `;`) when approval matching or elevation may be involved,
  preserving auto-approval and granular sandbox validation.
- **Clamp noisy output at the source:** `--quiet`, `-q`, `--reporter=dot`,
  `2>&1 | tail -n 50`, `| head -n 100`, `--no-progress`, `git --no-pager`.
- **Green vs. Red Runs:** On green runs, keep only the summary line. On failures,
  keep the full failing block — truncation is strictly forbidden on error traces.
- `git diff --stat` before `git diff`. View full diff only for hunks under review.
- Never dump build artifacts, virtual environments (`venv`, `.env`), lockfiles,
  `node_modules`, minified bundles, or binary files into context.

## Output: Write the Delta, Not the Document

- **Targeted Edits:** Always use `replace_file_content` for surgical patches. Never
  re-print an entire file or write full replacements when modifying existing code.
- **Concise, High-Signal Communication:** Do not restate the plan, summarize what
  was just shown, or narrate progress step by step. Deliver one clear line per completed unit.
- **RTL & Language Consistency:** When communicating in Hebrew, maintain crisp, direct
  Right-to-Left (RTL) formatting while keeping code identifiers in concise backticks.
- **Artifacts:** Plans and walkthroughs should document decisions, deltas, and
  verification results — not the reasoning transcript.
- No conversational fluff, no repetitive disclaimers, no preambles.

## Delegation: Isolate Expensive Exploration

Use a subagent (`invoke_subagent`) when the work is:
(a) Wide search, file exploration, or documentation survey
(b) Noisy log triage or large dataset inspection
(c) Independent and parallelizable workflows
(d) Exploratory trials likely to fail several times before succeeding

Rules for delegation:
- Give the subagent a narrow objective, exact scope, and a required compact return shape.
- Require a compact answer back (e.g. "file paths + line numbers + 1-line reason"),
  never raw text dumps. Exploration cost stays inside the subagent context.
- Do not delegate an edit that depends on heavy nuance already held in the main context.

## Model Routing

Route by task type:

| Task | Model |
| --- | --- |
| Architecture, ambiguous debugging, risky refactors, security | Strongest / Inherit (`pro`) |
| Mechanical edits, renames, boilerplate, formatting, summarizing | Fast model (`flash`) |
| Wide search, triage, log reduction in subagents | Fast / Light (`flash`, `flash_lite`) |

Escalate immediately if a fast model produces an incorrect result twice. Two cheap failures cost more than one correct run.

## Automation and Scheduled Tasks

For recurring or unattended runs (e.g. daily cron jobs, scrapers):

- **Early exit:** Detect "nothing changed" first (git SHA, mtime, hash, cursor timestamp)
  and stop before loading context or invoking APIs.
- **Incremental scope:** Process only the delta since the last run; persist state in
  lightweight JSON/cache. Never re-scan the entire dataset by default.
- **Idempotency:** Re-running must not duplicate work or output.
- **Deterministic preprocessing:** Filtering, parsing, counting, and formatting belong
  in Python/script logic, not in LLM prompt tokens.
- **Quiet success, loud failure:** Emit minimal summary on success; emit full detail on failure.
- **Contract preservation:** Never weaken checks, outputs, or notifications to save tokens.

## Decision Tree

```
Need information?
├─ Already in context?              → use it, do not re-read
├─ Locatable by search?             → grep/find first, then read exact range
├─ Wide / noisy / parallel?         → invoke_subagent with compact return
└─ Required for a correct edit?     → read range fully, no shortcuts

About to produce output?
├─ Modifying a file?                → replace_file_content (patch only)
├─ Explaining / reporting?          → shortest unambiguous form (RTL if Hebrew)
└─ Repeats visible context?         → omit

Execution failed?
└─ Stop trimming. Full errors, full relevant code hunk, escalate model if needed.
```

## Anti-Patterns

| Wasteful | Instead |
| --- | --- |
| Reading a whole file for one function | Search, then read the range |
| Re-reading unchanged files | Reuse context |
| Full-file rewrite for a small edit | Targeted patch (`replace_file_content`) |
| Dumping full test/build logs | Summary on pass, full block on fail |
| Narrating each step | One line per completed unit |
| Exploring broadly in the main thread | Subagent with a compact return |
| Strong model for mechanical edits | Fast model, escalate on failure |
| Scheduled task re-scanning everything | Cursor + early exit |
| Skipping tests to save tokens | Forbidden — run them |

## Self-Check Before Finishing

- Every user requirement addressed, nothing dropped.
- Required verification actually executed and validated.
- Edits applied cleanly and verified.
