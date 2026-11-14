#!/usr/bin/env bash
# Pre-commit hook for job_search_automation
# Enforces Zero-Emoji policy, Secret Scan, and Python/JSON Schema integrity before commit.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

PYTHON_BIN="python3"
if [ -x "$REPO_ROOT/venv/bin/python" ]; then
    PYTHON_BIN="$REPO_ROOT/venv/bin/python"
fi

echo "[PRE-COMMIT] Running Zero-Emoji Compliance Validator..."
"$PYTHON_BIN" scripts/validate_zero_emoji.py

echo "[PRE-COMMIT] Running Secret Scan and Schema Integrity Validation..."
"$PYTHON_BIN" scripts/project_hygiene.py --check-secrets --validate

echo "[PRE-COMMIT] All checks passed."
