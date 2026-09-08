---
name: project-health-audit
description: Performs a comprehensive, read-only health audit across all Antigravity projects and their folders — git state, dependencies, build, tests, lint/types, secrets, configuration, and the agent layer (skills, rules, MCP, hooks, scheduled tasks, permissions) — and reports every finding with severity and evidence. Use when asked to check whether projects are healthy, find defects or failures, verify nothing is broken, run a portfolio-wide review, or produce a status report across multiple repos.
---

# Project Health Audit

Audit every project, report what is actually broken, and prove each verdict
with evidence. Fix nothing unless explicitly asked.

## Truth rule (read first)

An audit produces **evidence**, not a guarantee. Never write "everything is
fine" or "no defects". Write what was checked, what passed, what failed, and
**what could not be verified**. A check that was skipped, timed out, or was
not applicable is `UNVERIFIED` — never `PASS`. Absence of a finding is not
proof of absence of a defect, and the report must say so.

Never infer a verdict from file names, README claims, CI badges, or previous
audit results. A `PASS` requires a command that ran and an observed result.

## Safety rules (non-negotiable)

- **Read-only by default.** No edits, no fixes, no formatting, no dependency
  upgrades, no `git add/commit/push/checkout/merge/rebase/reset`, no branch
  or worktree deletion, no `rm`, no `prune`, no `clean`.
- Installs and builds are allowed **only** in the project's own directory and
  only when needed to run a check. Prefer offline/frozen-lockfile installs.
- Never run anything that touches production, sends mail, calls paid APIs,
  deploys, or applies migrations to a non-local database. If a test suite
  requires such access, mark `UNVERIFIED — requires external resources`.
- **Redact secrets.** Report the file, line number, and the kind of secret.
  Never print the value, not even partially, in the report or in chat.
- If a fix is warranted, list it under `Recommended fixes` with exact file,
  line, and proposed change. Apply only after explicit approval, and then one
  project at a time.

## Phase 0 — Determine scope (do not guess)

Resolve the project list in this order and state which source was used:

1. An `audit-scope.json` / `audit-scope.yaml` manifest at a path the user
   provides (list of project names → folder paths).
2. Folders already attached to the currently open Antigravity project(s).
3. Ask the user once for the root paths, then persist them to
   `audit-scope.json` so later runs are deterministic.

Remember: an Antigravity project may span **several folders** (e.g. frontend
and backend repos). Audit each folder, and also audit the seams between them
(shared contracts, API clients, duplicated types, version drift).

Record for each folder: path, VCS or not, primary language/toolchain,
package manager, whether it is a git worktree or a main checkout.

## Phase 1 — Repository state

Per folder:

- Current branch, detached HEAD, ahead/behind upstream, missing upstream.
- Uncommitted changes and untracked files (`git status --porcelain`).
- Stale Antigravity worktrees left over from agent conversations
  (`git worktree list`) — report, never remove.
- Merge conflict markers left in tracked files (`<<<<<<<`, `>>>>>>>`).
- Large or binary files committed by accident; files that should be ignored.
- Last commit date — flag folders untouched for a long time as `Stale`, not
  as broken.

## Phase 2 — Dependencies and configuration

- Lockfile present and in sync with the manifest.
- Clean, frozen install succeeds (`--frozen-lockfile` / `npm ci` / `pip
  install -r` in a temp venv / equivalent).
- Known vulnerabilities via the ecosystem's own audit command.
- Runtime version pin (`.nvmrc`, `.python-version`, `engines`) vs what is
  actually installed.
- Config completeness: every variable read in code exists in
  `.env.example` / config schema. Missing ones are a real defect.
- `.gitignore` covers `.env`, credentials, build output, local state.
- **Secret scan** across tracked files and git history if feasible: API keys,
  tokens, private keys, connection strings. Redact per the safety rules.

## Phase 3 — Build, types, lint

- Build/compile from a clean state. Capture failures in full.
- Type check (`tsc --noEmit`, `mypy`, etc.).
- Linter and formatter check mode (never write mode).
- Distinguish **errors** (defects) from **warnings** (findings) and record
  counts for both.

## Phase 4 — Tests

- Run the full suite. Record: passed, failed, skipped, todo, duration.
- Treat as findings, with severity: failing tests (Blocker), skipped or
  `.only` / `xit` / `@pytest.mark.skip` left in code (High), suites that
  cannot run at all (High, `UNVERIFIED` for the code they cover).
- Coverage if the project already collects it. Do not add tooling.
- Flakiness: if a suite fails then passes on re-run, report it as flaky —
  that is a defect, not a pass.
- Zero tests is a finding (`No test coverage — correctness UNVERIFIED`).

## Phase 5 — Agent layer (Antigravity-specific)

This is where cross-project rot usually hides. Check per project and globally
(`~/.gemini/config/skills/`, workspace `.agents/skills/`, legacy
`.agent/skills/`):

- **Skills**: every folder has a `SKILL.md`; frontmatter parses; `description`
  present, specific, third person; `name` matches the folder; no duplicate
  names across workspace and global scope (workspace wins — report the
  shadowing); referenced `scripts/`, `examples/`, `resources/` actually exist
  and are executable where needed.
- **Rules / AGENTS.md**: present, current, not contradicting a skill or
  another rules file. Contradictory instructions are a real defect.
- **MCP config**: servers referenced exist and are reachable; no credentials
  stored in plaintext in the config; unused servers listed as cleanup.
- **Hooks (`hooks.json`)**: valid JSON; scripts exist; scripts are executable;
  a failing hook that can block the agent loop is a Blocker.
- **Plugins (`plugin.json`)**: manifest valid; declared skills/agents/rules
  directories exist.
- **Subagent definitions**: referenced models/tools exist; no infinite
  delegation loops.
- **Scheduled tasks**: for each one — does it still point at a valid project
  and folder, does it have an early-exit and a failure path, is its last run
  successful, and would a silent failure be visible to anyone? A scheduled
  task that fails quietly is a Blocker.
- **Permissions and security preset** per project: flag `Full Machine` /
  `Unrestricted` presets, disabled strict mode, disabled sandbox, and overly
  broad persisted permission grants. Report as a risk finding with the
  project name; do not change settings.

## Phase 6 — Cross-project seams

- Shared library/API versions that disagree between folders.
- Duplicated code or types that have already diverged.
- Contracts (OpenAPI, protobuf, schema files) out of sync with consumers.
- The same secret or credential reused across projects.

## Severity model

| Severity | Meaning |
| --- | --- |
| `BLOCKER` | Broken now: build fails, tests fail, secret committed, automation silently failing |
| `HIGH` | Will break or already causes wrong behaviour: missing config, skipped tests, unsafe permissions, conflicting rules |
| `MEDIUM` | Real defect, contained impact: outdated deps with known CVEs, lint errors, stale worktrees |
| `LOW` | Hygiene: warnings, TODO/FIXME, dead files, formatting |
| `UNVERIFIED` | Could not be checked — say exactly why |

## Execution order and token discipline

Audit **one project at a time**, and prefer one subagent per project so that
the noisy output stays out of the main context. Each subagent returns only:
findings table, evidence lines, and the counts — never raw logs.

Clamp every command (`--quiet`, `| tail -50`, `--reporter=dot`,
`git --no-pager`). Keep full output only for failures. If a token-efficiency
skill is available, follow it — but its efficiency rules never authorize
skipping a check. A check not run is `UNVERIFIED`, and that must appear in
the report.

Hard timeout per command; on timeout record `UNVERIFIED — timed out after Ns`
and move on rather than retrying indefinitely.

## Output

Write, do not just print:

```
audit/
├── index.md                 # rollup: per-project status + top findings
├── summary.json             # machine-readable, for diffing runs
└── <project>/report.md      # per-project detail with evidence
```

`index.md` opens with counts by severity, then a table of
`project | blockers | high | medium | low | unverified | last audited`.

Each finding, in every report, has: **ID, severity, project, folder, file:line,
what is wrong, evidence (the command and its result), impact, suggested fix.**
No finding without evidence. No evidence without a command that actually ran.

`summary.json` enables incremental re-runs: on the next audit, compare against
the previous run and mark each finding `NEW`, `PERSISTS`, `FIXED`, or
`REGRESSED`. Report regressions first — they matter more than new findings.

## Finish with

1. One-paragraph verdict per project in plain language.
2. The blocker list, ordered by what to fix first.
3. An explicit list of everything left `UNVERIFIED` and what it would take to
   verify it.
4. Nothing was modified — or, if fixes were approved, exactly what changed.
