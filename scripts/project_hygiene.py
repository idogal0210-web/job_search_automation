#!/usr/bin/env python3
"""
project_hygiene.py
Automated project hygiene, candidate classification, safe cleanup, secret scanning,
and integrity validation for job_search_automation.
Follows the deterministic 4-Tier classification model and zero-emoji policy.
"""

import os
import sys
import re
import json
import shutil
import time
import fnmatch
from pathlib import Path
from datetime import datetime, timedelta

REPO_ROOT = Path(__file__).resolve().parent.parent

PROTECTED_PREFIXES = (
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

PROTECTED_EXACT_FILES = {
    "main.py",
    ".env",
    ".gitignore",
    ".python-version",
    "requirements.txt",
    "requirements-lock.txt",
    "PROJECT_CONTEXT.md",
    "README.md",
    ".save-and-sync.yml",
}

DISPOSABLE_PATTERNS = [
    "*.bak",
    "*.tmp",
    "*.temp",
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
]

SECRET_PATTERNS = [
    (r"ghp_[A-Za-z0-9_]{36,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z\-_]{35}", "Google Gemini / Cloud API Key"),
    (r"hf_[a-zA-Z0-9]{34,}", "Hugging Face Access Token"),
    (r"tvly-[a-zA-Z0-9\-_]{30,}", "Tavily API Key"),
    (r"fc-[a-f0-9]{32}", "Firecrawl API Key"),
    (r"-----BEGIN (?:RSA|OPENSSH|PRIVATE) KEY-----", "Private Key Header"),
]

def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size / (1024 * 1024):.2f} MB"

def get_dir_size(path):
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp) and os.path.exists(fp):
                total += os.path.getsize(fp)
    return total

def is_protected(rel_path):
    parts = rel_path.split(os.sep)
    if parts[0] in PROTECTED_EXACT_FILES:
        return True
    if parts[0] in PROTECTED_PREFIXES:
        return True
    return False

def scan_project(repo_root=REPO_ROOT):
    tier2_disposable = []
    tier3_logs = []
    pycache_dirs = []
    
    for root, dirs, files in os.walk(repo_root):
        if ".git" in dirs:
            dirs.remove(".git")
        if "venv" in dirs:
            dirs.remove("venv")
        if ".venv" in dirs:
            dirs.remove(".venv")
        if ".recovery" in dirs:
            dirs.remove(".recovery")
            
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            size = get_dir_size(pycache_path)
            pycache_dirs.append({
                "path": os.path.relpath(pycache_path, repo_root),
                "full_path": pycache_path,
                "type": "directory",
                "size": size,
                "reason": "Python bytecode cache directory"
            })
            dirs.remove("__pycache__")
            
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, repo_root)
            
            matched_disposable = False
            for pat in DISPOSABLE_PATTERNS:
                if fnmatch.fnmatch(f, pat) or fnmatch.fnmatch(rel_path, pat):
                    size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
                    tier2_disposable.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "type": "file",
                        "size": size,
                        "reason": f"Matches disposable pattern '{pat}'"
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
                if age_days > 7 or size > 1024 * 1024:
                    tier3_logs.append({
                        "path": rel_path,
                        "full_path": full_path,
                        "type": "log",
                        "size": size,
                        "age_days": age_days,
                        "reason": f"Log file exceeds retention threshold ({age_days} days old, {format_size(size)})"
                    })

    return {
        "tier2_disposable": tier2_disposable,
        "pycache_dirs": pycache_dirs,
        "tier3_logs": tier3_logs
    }

def run_clean(dry_run=True, repo_root=REPO_ROOT):
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
        p = item["full_path"]
        if os.path.exists(p):
            os.remove(p)
            cleaned_count += 1
            freed_bytes += item["size"]
            print(f"  [REMOVED FILE] {item['path']}")
            
    for item in scan_results["tier3_logs"]:
        p = item["full_path"]
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                if len(lines) > 200:
                    with open(p, "w", encoding="utf-8") as f:
                        f.writelines(lines[-200:])
                    print(f"  [TRUNCATED LOG] {item['path']}")
                else:
                    os.remove(p)
                    print(f"  [REMOVED LOG] {item['path']}")
                cleaned_count += 1
                freed_bytes += item["size"]
            except Exception as e:
                print(f"  [WARNING] Error handling log {item['path']}: {e}")
                
    print("-" * 75)
    print(f"[OK] Cleanup finished successfully. Cleaned {cleaned_count} items, freed {format_size(freed_bytes)}.")
    return cleaned_count, freed_bytes

def scan_secrets(repo_root=REPO_ROOT):
    print("\n[SCAN] Scanning for potential exposed secrets...")
    findings = []
    
    for root, dirs, files in os.walk(repo_root):
        if ".git" in dirs: dirs.remove(".git")
        if "venv" in dirs: dirs.remove("venv")
        if ".venv" in dirs: dirs.remove(".venv")
        if ".recovery" in dirs: dirs.remove(".recovery")
        
        for f in files:
            if f in {".env", ".env.local"}:
                continue
            if f.endswith((".png", ".jpg", ".jpeg", ".ico", ".pdf", ".pyc", ".db", ".sqlite")):
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
                                    "preview": redacted
                                })
            except Exception:
                pass
                
    if findings:
        print(f"[SECURITY ALERT] Found {len(findings)} potential unredacted secret(s):")
        for finding in findings:
            print(f"  [WARN] {finding['file']}:{finding['line']} -> [{finding['type']}] ({finding['preview']})")
        return len(findings)
    else:
        print("[OK] Secret scan passed: No unredacted API keys or secrets detected in working tree.")
        return 0

def validate_integrity(repo_root=REPO_ROOT):
    import py_compile
    print("\n[VALIDATE] Validating project code and data integrity...")
    errors = []
    
    py_files = []
    for root, dirs, files in os.walk(repo_root):
        if ".git" in dirs: dirs.remove(".git")
        if "venv" in dirs: dirs.remove("venv")
        if ".venv" in dirs: dirs.remove(".venv")
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
                
    for pf in py_files:
        try:
            py_compile.compile(pf, doraise=True)
        except py_compile.PyCompileError as e:
            rel = os.path.relpath(pf, repo_root)
            errors.append(f"Python syntax error in {rel}: {e}")
            
    for root, dirs, files in os.walk(repo_root):
        if ".git" in dirs: dirs.remove(".git")
        if "venv" in dirs: dirs.remove("venv")
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8") as jf:
                        json.load(jf)
                except Exception as e:
                    rel = os.path.relpath(full_path, repo_root)
                    errors.append(f"JSON syntax error in {rel}: {e}")
                    
    if errors:
        print(f"[ERROR] Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return len(errors)
        
    print(f"[OK] Integrity validated successfully: {len(py_files)} Python files and all JSON datasets passed check.")
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
    
    if args.audit:
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
