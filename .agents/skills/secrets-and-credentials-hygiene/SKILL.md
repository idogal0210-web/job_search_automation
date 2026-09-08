---
name: secrets-and-credentials-hygiene
description: Prevents secret leakage and enforces strict credential management across all agent interactions, code generation, commits, and automation outputs. Covers redaction rules, pre-commit scanning, secure storage patterns, token lifecycle management, and config file hygiene. Use whenever handling API keys, tokens, passwords, or sensitive environment variables.
---

# Secrets & Credentials Hygiene

Treat every secret as **radioactive material**: it must be contained,
tracked, and never exposed — not even partially. A single leaked token
can compromise an entire account, trigger quota abuse, or enable
unauthorized access to production systems.

## Prime Directive

**Never print, echo, embed, quote, log, or include any secret value —
fully or partially — in any of these surfaces:**

1. Chat responses or conversational output.
2. Code files, scripts, or generated source code.
3. Artifacts (plans, walkthroughs, reports, markdown documents).
4. Git commits, diffs, or commit messages.
5. Terminal command arguments visible in shell history.
6. Error messages or debug logs.

When referencing a secret, use its **name** (e.g., `GEMINI_API_KEY`,
`GIT_TOKEN`), never its **value**.

---

## 1. Secure Storage (Where Secrets Must Live)

| Storage Location | When to Use |
| --- | --- |
| **GitHub Secrets** (`Settings > Secrets > Actions`) | For any value used in GitHub Actions workflows |
| **`.env` file** (local, git-ignored) | For local development and testing |
| **Environment variables** (runtime injection) | For production services and CI/CD pipelines |

### What Must NEVER Be Stored In:

- Source code files (`.py`, `.js`, `.ts`, `.sh`, etc.).
- Configuration files committed to Git (`config.json`, `settings.yaml`).
- README or documentation files.
- Antigravity permission grants, command history, or `config.json`.
- Markdown artifacts, plans, or walkthrough documents.
- Inline comments or docstrings.

---

## 2. `.gitignore` Enforcement

Every project repository MUST have a `.gitignore` that excludes:

```gitignore
# Secrets and credentials
.env
.env.*
*.pem
*.key
*secret*
*token*

# Build and runtime artifacts
__pycache__/
*.pyc
venv/
node_modules/
.DS_Store

# Agent internals
.agents/
```

Before any `git add`, verify that `.gitignore` is in place and covers
sensitive patterns. If it does not exist, **create it before staging files**.

---

## 3. Pre-Commit Secret Scanning

Before every commit, scan staged files for accidental secret inclusion:

### Patterns to Detect:

| Pattern | Type |
| --- | --- |
| `ghp_[A-Za-z0-9]{36,}` | GitHub Personal Access Token |
| `AIza[A-Za-z0-9_-]{35}` | Google API Key |
| `sk-[A-Za-z0-9]{32,}` | OpenAI / Stripe Secret Key |
| `AQ.Ab[A-Za-z0-9_-]{30,}` | Google Gemini API Key |
| Strings matching `password`, `secret`, `token` followed by `=` and a value | Generic credential pattern |
| Base64-encoded strings > 40 chars in config files | Potential encoded secrets |

### Scanning Procedure:

```bash
# Quick scan before committing
git diff --cached --name-only | xargs grep -nEi \
  '(ghp_|AIza|sk-|AQ\.Ab|password\s*=|secret\s*=|token\s*=)' \
  2>/dev/null
```

If any match is found: **STOP. Do not commit.** Remove or relocate the
secret to `.env` or GitHub Secrets, then re-stage.

---

## 4. Token Lifecycle Management

### Creation:
- Name tokens descriptively (e.g., `Antigravity-MCP`, `Daily-Report-Actions`).
- Grant **minimum required scopes** only. Avoid full-admin tokens when
  `repo` + `workflow` suffice.
- Set expiration dates when possible (90-day rotation recommended).

### Usage:
- One token per purpose/service. Never reuse the same token across unrelated
  systems.
- Track where each token is used (document in a private, non-committed note).

### Rotation:
- Rotate tokens immediately if: a token was accidentally exposed, an employee
  or collaborator lost access, or the token's age exceeds 90 days.
- After rotation: update all locations where the old token was used (GitHub
  Secrets, `.env`, `mcp_config.json`), then revoke the old token.

### Revocation:
- Revoke tokens that are no longer in use.
- After revoking: verify that no automation broke (run a health audit).

---

## 5. Agent-Specific Rules

### When the Agent Encounters a Secret:

```
Secret value visible in context?
├─ In a file being read?         → Note the file and line, NEVER quote the value
├─ In command output?            → Summarize without the value: "API key found at .env:3"
├─ User pastes it in chat?       → Acknowledge receipt, use it silently, never repeat it
├─ In git history?               → Report as BLOCKER finding, recommend rotation
└─ In a generated artifact?      → STOP. Remove it before saving the artifact.
```

### When the Agent Generates Code:

- Use `os.environ.get("KEY_NAME")` or `os.getenv("KEY_NAME")` — never
  hardcoded string literals for credentials.
- Template `.env.example` files with placeholder values:
  ```
  GEMINI_API_KEY=your_gemini_api_key_here
  GMAIL_APP_PASSWORD=your_app_password_here
  ```
- Never generate `curl` commands with inline tokens in arguments. Use
  environment variable references: `curl -H "Authorization: token $TOKEN"`.

### When the Agent Runs Commands:

- Prefer environment variable injection over command-line arguments for
  secrets (command-line args are visible in process listings and shell
  history).
- If a token must be in a command argument (e.g., `git remote set-url`),
  acknowledge that it will appear in `.git/config` and ensure that file
  is not committed or shared.

---

## 6. Config File Hygiene

### `mcp_config.json`:
- Tokens stored in `mcp_config.json` under `env` blocks are acceptable
  (this file is local and not committed to Git).
- Verify that `mcp_config.json` is excluded from version control.

### `config.json` (Antigravity global config):
- Permission grants may inadvertently contain tokens from previous
  commands. Periodically audit `globalPermissionGrants` in
  `~/.gemini/config/config.json` for exposed credentials.
- If found: note the finding, recommend removal of the specific grant
  entry, and recommend token rotation.

---

## 7. Incident Response (Secret Was Leaked)

If a secret is found in a commit, chat, artifact, or public surface:

1. **Rotate immediately.** Generate a new token/key and update all consumers.
2. **Revoke the old credential.** Do not wait — revoke it now.
3. **Audit usage.** Check the service's access logs for unauthorized use
   during the exposure window.
4. **Scrub if possible.** For Git history: `git filter-branch` or BFG Repo
   Cleaner. For chat/artifacts: delete the artifact.
5. **Post-mortem.** Document how the leak happened and add a rule or scan
   to prevent recurrence.

---

## Anti-Patterns

| Dangerous | Instead |
| --- | --- |
| Hardcoding API keys in source code | `os.environ.get("KEY_NAME")` |
| Committing `.env` to Git | Add `.env` to `.gitignore` before first commit |
| Printing token values in logs | Log the token name and status, never the value |
| Reusing one token everywhere | One token per purpose with minimum scopes |
| Never rotating tokens | 90-day rotation policy, immediate on exposure |
| `curl` with inline tokens | Environment variable: `$TOKEN` |
| Ignoring old tokens in config | Periodic audit of `config.json` permission grants |
| Assuming "private repo" = "safe" | Private repos can be forked, cloned, or leaked |
