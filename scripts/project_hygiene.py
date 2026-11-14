#!/usr/bin/env python3
"""
project_hygiene.py
Automated project hygiene, candidate classification, safe cleanup, secret scanning,
and integrity validation for job_search_automation.
Driven by .save-and-sync.yml policy and enforces the deterministic 4-Tier
classification model and zero-emoji policy.
"""

import ast
import fnmatch
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_PROTECTED_PREFIXES = (
    "src",
    "data",
    "docs",
    ".agents",
    ".github",
    "tests",
    "tools",
    "frontend",
    "scripts",
    ".git",
    "venv",
    ".venv",
)

DEFAULT_PROTECTED_EXACT_FILES = {
    "main.py",
    ".env",
    ".gitignore",
    ".python-version",
    "requirements.txt",
    "requirements-lock.txt",
    "PROJECT_CONTEXT.md",
    "TASKS.md",
    "README.md",
    ".save-and-sync.yml",
}

DEFAULT_DISPOSABLE_PATTERNS = [
    "*.bak",
    "*.tmp",
    "*.temp",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
    "*-intake*.md",
    "*review-snapshot*.md",
]

EXCLUDED_WALK_DIRS = {
    ".git",
    "venv",
    ".venv",
    ".recovery",
    "node_modules",
    "dist",
    "__pycache__",
}

SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9_]{36,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google Gemini / Cloud API Key"),
    (r"hf_[a-zA-Z0-9]{34,}", "Hugging Face Access Token"),
    (r"tvly-[a-zA-Z0-9\-_]{30,}", "Tavily API Key"),
    (r"fc-[a-f0-9]{32}", "Firecrawl API Key"),
    (r"sb_secret_[A-Za-z0-9_\-]{16,}", "Supabase Secret Key"),
    (r"sbp_[a-f0-9]{32,}", "Supabase Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"sk-ant-(?:api\d{2}-)?[A-Za-z0-9_\-]{20,}", "Anthropic API Key"),
    (r"-----BEGIN (?:RSA|OPENSSH|PRIVATE) KEY-----", "Private Key Header"),
]


def load_policy_config(repo_root: Path = REPO_ROOT) -> Dict[str, Any]:
    """
    Load policy configuration from .save-and-sync.yml.
    Supports both PyYAML (when installed) and deterministic line-based YAML parsing.
    """
    policy_path = Path(repo_root) / ".save-and-sync.yml"
    config: Dict[str, Any] = {
        "protected_prefixes": set(DEFAULT_PROTECTED_PREFIXES),
        "protected_exact_files": set(DEFAULT_PROTECTED_EXACT_FILES),
        "disposable_patterns": list(DEFAULT_DISPOSABLE_PATTERNS),
        "log_max_age_days": 7,
        "log_max_lines": 500,
    }
    if not policy_path.exists():
        return config

    raw_text = policy_path.read_text(encoding="utf-8", errors="ignore")
    parsed: Dict[str, Any] = {}
    try:
        import yaml  # type: ignore
        loaded = yaml.safe_load(raw_text)
        if isinstance(loaded, dict):
            parsed = loaded
    except Exception:
        current_section = None
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line.startswith((" ", "\t")) and stripped.endswith(":"):
                current_section = stripped[:-1].strip()
                parsed.setdefault(current_section, [])
            elif stripped.startswith("- ") and current_section in ("protected_paths", "disposable_patterns"):
                val = stripped[2:].strip().strip('"').strip("'")
                if isinstance(parsed.get(current_section), list):
                    parsed[current_section].append(val)
            elif ":" in stripped and current_section == "log_retention":
                if not isinstance(parsed.get("log_retention"), dict):
                    parsed["log_retention"] = {}
                k, v = stripped.split(":", 1)
                v_clean = v.strip().strip('"').strip("'")
                if v_clean.isdigit():
                    parsed["log_retention"][k.strip()] = int(v_clean)

    for entry in parsed.get("protected_paths", []) or []:
        s = str(entry).strip()
        if not s:
            continue
        if s.endswith("/**"):
            config["protected_prefixes"].add(s[:-3].strip("/"))
        elif "*" not in s:
            config["protected_exact_files"].add(s)
        else:
            config["protected_exact_files"].add(s)

    disp = parsed.get("disposable_patterns")
    if isinstance(disp, list) and disp:
        normalized_disp = []
        for pat in disp:
            p_str = str(pat).strip()
            if p_str.startswith("**/"):
                p_str = p_str[3:]
            if p_str and p_str != "__pycache__":
                normalized_disp.append(p_str)
        if normalized_disp:
            config["disposable_patterns"] = normalized_disp

    log_ret = parsed.get("log_retention")
    if isinstance(log_ret, dict):
        if isinstance(log_ret.get("max_age_days"), int):
            config["log_max_age_days"] = log_ret["max_age_days"]
        if isinstance(log_ret.get("max_lines"), int):
            config["log_max_lines"] = log_ret["max_lines"]

    return config


POLICY = load_policy_config(REPO_ROOT)
PROTECTED_PREFIXES = tuple(sorted(POLICY["protected_prefixes"]))
PROTECTED_EXACT_FILES = set(POLICY["protected_exact_files"])
DISPOSABLE_PATTERNS = list(POLICY["disposable_patterns"])


def format_size(bytes_size: int) -> str:
    if bytes_size < 1024:
        return f"{bytes_size} B"
    if bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    return f"{bytes_size / (1024 * 1024):.2f} MB"


def get_dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp) and os.path.exists(fp):
                total += os.path.getsize(fp)
    return total


def is_protected(rel_path: str, repo_root: Path = REPO_ROOT) -> bool:
    """
    Return True when `rel_path` falls under Tier 1 protected paths or exact files.
    Bytecode cache files (.pyc, .pyo, __pycache__) and OS metadata (.DS_Store, Thumbs.db)
    are never protected; all other files under protected prefixes are strictly protected.
    """
    norm_rel = os.path.normpath(rel_path).lstrip(os.sep)
    if not norm_rel or norm_rel == ".":
        return True
    base_name = os.path.basename(norm_rel)
    if base_name in {".DS_Store", "Thumbs.db"} or base_name.endswith((".pyc", ".pyo")):
        return False

    parts = norm_rel.split(os.sep)
    if parts[0] == "__pycache__" or "__pycache__" in parts:
        return False

    policy = load_policy_config(repo_root) if repo_root != REPO_ROOT else POLICY
    exact_set = policy["protected_exact_files"]
    prefix_set = policy["protected_prefixes"]

    if norm_rel in exact_set or parts[0] in exact_set:
        return True
    for pat in exact_set:
        if "*" in pat and (fnmatch.fnmatch(norm_rel, pat) or fnmatch.fnmatch(base_name, pat)):
            return True
    if parts[0] in prefix_set:
        return True
    return False


def _prune_excluded_dirs(dirs: List[str], keep_pycache: bool = False) -> None:
    excluded = EXCLUDED_WALK_DIRS - ({"__pycache__"} if keep_pycache else set())
    dirs[:] = [d for d in dirs if d not in excluded]


def scan_project(repo_root: Path = REPO_ROOT) -> Dict[str, List[Dict[str, Any]]]:
    repo_root = Path(repo_root)
    policy = load_policy_config(repo_root)
    disposable_patterns = policy["disposable_patterns"]
    max_log_age_days = policy["log_max_age_days"]

    tier2_disposable: List[Dict[str, Any]] = []
    tier3_logs: List[Dict[str, Any]] = []
    pycache_dirs: List[Dict[str, Any]] = []

    for root, dirs, files in os.walk(repo_root):
        _prune_excluded_dirs(dirs, keep_pycache=True)

        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            size = get_dir_size(pycache_path)
            pycache_dirs.append({
                "path": os.path.relpath(pycache_path, repo_root),
                "full_path": pycache_path,
                "type": "directory",
                "size": size,
                "reason": "Python bytecode cache directory",
            })
            dirs.remove("__pycache__")

        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_root)

            # Enforce Tier 1 protection before classifying any file as disposable
            if is_protected(rel_path, repo_root=repo_root):
                continue

            matched_disposable = False
            for pat in disposable_patterns:
                if fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(rel_path, pat):
                    size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
                    tier2_disposable.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "type": "file",
                        "size": size,
                        "reason": f"Matches disposable pattern '{pat}'",
                    })
                    matched_disposable = True
                    break

            if matched_disposable:
                continue

            if f.endswith(".log") and "logs" in rel_path.split(os.sep):
                stat = os.stat(full_path)
                mtime = datetime.fromtimestamp(stat.st_mtime)
                age_days = (datetime.now() - mtime).days
                size = stat.st_size
                if age_days > max_log_age_days or size > 1024 * 1024:
                    tier3_logs.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "type": "log",
                        "size": size,
                        "age_days": age_days,
                        "reason": f"Log file exceeds retention threshold ({age_days} days old, {format_size(size)})",
                    })

    return {
        "tier2_disposable": tier2_disposable,
        "pycache_dirs": pycache_dirs,
        "tier3_logs": tier3_logs,
    }


def run_clean(dry_run: bool = True, repo_root: Path = REPO_ROOT) -> Tuple[int, int]:
    repo_root = Path(repo_root)
    policy = load_policy_config(repo_root)
    max_log_lines = policy["log_max_lines"]

    scan_results = scan_project(repo_root)
    all_disposable = scan_results["pycache_dirs"] + scan_results["tier2_disposable"] + scan_results["tier3_logs"]

    total_size = sum(item["size"] for item in all_disposable)

    print(f"\n{'[DRY-RUN AUDIT]' if dry_run else '[EXECUTING CLEANUP]'} Project Hygiene Report")
    print(f"Repository Root: {repo_root}")
    print("-" * 75)

    if not all_disposable:
        print("[OK] No disposable, cache, or expired files found. Working tree is lean and clean.")
        return 0, 0

    print(f"Found {len(all_disposable)} disposable candidate(s) occupying ~{format_size(total_size)}:")
    for item in all_disposable:
        print(f"  - [{item['type'].upper()}] {item['path']} ({format_size(item['size'])}) -> {item['reason']}")

    if dry_run:
        print("-" * 75)
        print("[INFO] Dry-run mode: 0 files modified. Run with --clean to execute safe removal.")
        return len(all_disposable), total_size

    print("\n[ACTION] Executing removal...")
    cleaned_count = 0
    freed_bytes = 0

    for item in scan_results["pycache_dirs"]:
        p = item["full_path"]
        if os.path.exists(p):
            shutil.rmtree(p, ignore_errors=True)
            cleaned_count += 1
            freed_bytes += item["size"]
            print(f"  [REMOVED DIR] {item['path']}")

    for item in scan_results["tier2_disposable"]:
        rel_path = item["path"]
        if is_protected(rel_path, repo_root=repo_root):
            print(f"  [SKIPPED PROTECTED] {rel_path}")
            continue
        p = item["full_path"]
        if os.path.exists(p):
            os.remove(p)
            cleaned_count += 1
            freed_bytes += item["size"]
            print(f"  [REMOVED FILE] {rel_path}")

    for item in scan_results["tier3_logs"]:
        rel_path = item["path"]
        if is_protected(rel_path, repo_root=repo_root):
            continue
        p = item["full_path"]
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                if len(lines) > max_log_lines:
                    with open(p, "w", encoding="utf-8") as f:
                        f.writelines(lines[-max_log_lines:])
                    print(f"  [TRUNCATED LOG] {rel_path}")
                else:
                    os.remove(p)
                    print(f"  [REMOVED LOG] {rel_path}")
                cleaned_count += 1
                freed_bytes += item["size"]
            except Exception as e:
                print(f"  [WARNING] Error handling log {rel_path}: {e}")

    print("-" * 75)
    print(f"[OK] Cleanup finished successfully. Cleaned {cleaned_count} items, freed {format_size(freed_bytes)}.")
    return cleaned_count, freed_bytes


def scan_secrets(repo_root: Path = REPO_ROOT) -> int:
    repo_root = Path(repo_root)
    print("\n[SCAN] Scanning for potential exposed secrets...")
    findings = []

    for root, dirs, files in os.walk(repo_root):
        _prune_excluded_dirs(dirs, keep_pycache=False)

        for f in files:
            if f in {".env", ".env.local"}:
                continue
            if f.endswith((".png", ".jpg", ".jpeg", ".ico", ".pdf", ".pyc", ".db", ".sqlite", ".woff", ".woff2")):
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_root)

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as file_obj:
                    for line_num, line in enumerate(file_obj, start=1):
                        for pattern, secret_type in SECRET_PATTERNS:
                            matches = re.findall(pattern, line)
                            for m in matches:
                                redacted = m[:6] + "..." + m[-4:] if len(m) > 12 else m[:4] + "..."
                                findings.append({
                                    "file": rel_path,
                                    "line": line_num,
                                    "type": secret_type,
                                    "preview": redacted,
                                })
            except Exception:
                pass

    if findings:
        print(f"[SECURITY ALERT] Found {len(findings)} potential unredacted secret(s):")
        for finding in findings:
            print(f"  [WARN] {finding['file']}:{finding['line']} -> [{finding['type']}] ({finding['preview']})")
        return len(findings)

    print("[OK] Secret scan passed: No unredacted API keys or secrets detected in working tree.")
    return 0


def _parse_requirement_packages(text: str) -> Set[str]:
    """Extract normalized exact package names from a requirements file."""
    pkgs: Set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith(("-", "--")):
            continue
        name = re.split(r"[=<>!~\[\s;]", line, maxsplit=1)[0].strip().lower()
        if name:
            pkgs.add(name.replace("_", "-"))
    return pkgs


def validate_dataset_schemas(repo_root: Path = REPO_ROOT) -> List[str]:
    """Validate structural schemas of core JSON state and dashboard files."""
    repo_root = Path(repo_root)
    errors: List[str] = []

    schema_checks = [
        ("data/jobs_state.json", list, None),
        ("data/sync_state.json", dict, ("saved", "starred", "rejected")),
        ("data/historical_catalog.json", dict, None),
        ("data/inactive_jobs.json", dict, ("scanned_at", "total_scanned", "inactive_jobs")),
        ("data/evaluation_state.json", dict, ("jobs",)),
        ("docs/data/jobs.json", (list, dict), None),
        ("docs/data/latest_run.json", dict, ("run_id", "final_status", "stages")),
    ]

    for rel_path, expected_type, required_keys in schema_checks:
        fp = repo_root / rel_path
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"Schema check failed to parse {rel_path}: {exc}")
            continue
        if not isinstance(data, expected_type):
            errors.append(
                f"Schema mismatch in {rel_path}: expected {expected_type}, got {type(data).__name__}"
            )
            continue
        if required_keys and isinstance(data, dict):
            for key in required_keys:
                if key not in data:
                    errors.append(f"Schema mismatch in {rel_path}: missing required key '{key}'")
        if rel_path == "data/jobs_state.json" and isinstance(data, list):
            non_str = [x for x in data[:20] if not isinstance(x, str)]
            if non_str:
                errors.append("Schema mismatch in data/jobs_state.json: items must be URL strings")
        if rel_path == "docs/data/jobs.json":
            jobs_list = data.get("jobs", []) if isinstance(data, dict) else data
            if not isinstance(jobs_list, list):
                errors.append("Schema mismatch in docs/data/jobs.json: 'jobs' must be a list")

    return errors


def validate_integrity(repo_root: Path = REPO_ROOT) -> int:
    repo_root = Path(repo_root)
    print("\n[VALIDATE] Validating project code and data integrity...")
    errors: List[str] = []

    py_files: List[str] = []
    for root, dirs, files in os.walk(repo_root):
        _prune_excluded_dirs(dirs, keep_pycache=False)
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    # Validate Python syntax in-memory using ast.parse (never writes __pycache__)
    for pf in py_files:
        try:
            source = Path(pf).read_text(encoding="utf-8")
            ast.parse(source, filename=pf)
        except SyntaxError as e:
            rel = os.path.relpath(pf, repo_root)
            errors.append(f"Python syntax error in {rel}:{e.lineno}: {e.msg}")
        except Exception as e:
            rel = os.path.relpath(pf, repo_root)
            errors.append(f"Python parse error in {rel}: {e}")

    for root, dirs, files in os.walk(repo_root):
        _prune_excluded_dirs(dirs, keep_pycache=False)
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8") as jf:
                        json.load(jf)
                except Exception as e:
                    rel = os.path.relpath(full_path, repo_root)
                    errors.append(f"JSON syntax error in {rel}: {e}")

    errors.extend(validate_dataset_schemas(repo_root))

    # Check Living Documentation and Dependency Parity
    doc_files = ["PROJECT_CONTEXT.md", "TASKS.md", "README.md", "requirements.txt", "requirements-lock.txt"]
    for df in doc_files:
        df_path = repo_root / df
        if not df_path.exists():
            errors.append(f"Missing required living documentation file: {df}")
        elif df_path.stat().st_size == 0:
            errors.append(f"Living documentation file is empty: {df}")

    req_file = repo_root / "requirements.txt"
    lock_file = repo_root / "requirements-lock.txt"
    if req_file.exists() and lock_file.exists():
        try:
            req_pkgs = _parse_requirement_packages(req_file.read_text(encoding="utf-8"))
            lock_pkgs = _parse_requirement_packages(lock_file.read_text(encoding="utf-8"))
            for pkg in sorted(req_pkgs):
                if pkg not in lock_pkgs:
                    errors.append(f"Dependency '{pkg}' listed in requirements.txt is missing from requirements-lock.txt")
        except Exception as e:
            errors.append(f"Error checking dependency parity: {e}")

    if errors:
        print(f"[ERROR] Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return len(errors)

    print(f"[OK] Integrity validated successfully: {len(py_files)} Python files, all JSON datasets, and living documentation passed check.")
    return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Deterministic Project Hygiene for job_search_automation")
    parser.add_argument("--audit", "--dry-run", action="store_true", help="Perform read-only hygiene audit")
    parser.add_argument("--clean", action="store_true", help="Execute safe cleanup of disposable/expired candidates")
    parser.add_argument("--check-secrets", action="store_true", help="Scan for exposed API tokens and private keys")
    parser.add_argument("--validate", action="store_true", help="Validate Python & JSON syntax")
    parser.add_argument("--all", action="store_true", help="Run audit, validation, and secret scan")

    args = parser.parse_args()

    if not (args.clean or args.check_secrets or args.validate or args.all):
        args.audit = True

    exit_code = 0

    if args.audit or args.all:
        run_clean(dry_run=True)

    if args.clean:
        run_clean(dry_run=False)

    if args.check_secrets or args.all:
        sec_errs = scan_secrets()
        if sec_errs > 0:
            exit_code = 1

    if args.validate or args.all:
        val_errs = validate_integrity()
        if val_errs > 0:
            exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
