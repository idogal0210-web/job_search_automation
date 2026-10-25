#!/usr/bin/env python3
"""
scripts/validate_zero_emoji.py

Comprehensive Zero-Emoji Compliance Validator.
Scans source code, templates, stylesheets, scripts, markdown, and tests
for any banned Unicode emojis, pictographs, dingbats, and encoded entities.

Strictly preserves Hebrew text, Nikud, numbers, punctuation, and currency symbols
(₪ Shekel U+20AA, $ Dollar U+0024, € Euro U+20AC, £ Pound U+00A3) with zero false positives.

Target directories scanned by default:
  - frontend/
  - docs/
  - tests/
  - scripts/

Exit Codes:
  0 - Clean (0 emojis found)
  1 - Violation (1 or more emojis found)
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple

# Unicode emoji categories per specifications:
EMOJI_CATEGORIES = [
    ("Emoticons", 0x1F600, 0x1F64F),
    ("Miscellaneous Symbols and Pictographs", 0x1F300, 0x1F5FF),
    ("Transport and Map Symbols", 0x1F680, 0x1F6FF),
    ("Alchemical Symbols", 0x1F700, 0x1F77F),
    ("Geometric Shapes Extended", 0x1F780, 0x1F7FF),
    ("Supplemental Arrows-C", 0x1F800, 0x1F8FF),
    ("Supplemental Symbols and Pictographs", 0x1F900, 0x1F9FF),
    ("Chess / Symbols Extended-A", 0x1FA00, 0x1FA6F),
    ("Symbols and Pictographs Extended-B", 0x1FA70, 0x1FAFF),
    ("Miscellaneous Symbols", 0x2600, 0x26FF),
    ("Dingbats", 0x2700, 0x27BF),
    ("Enclosed Alphanumeric and Flags", 0x1F100, 0x1F1FF),
    ("Miscellaneous Technical", 0x2300, 0x23FF),
    ("Variation Selectors (VS-16)", 0xFE0F, 0xFE0F),
    ("Combining Enclosing Keycap", 0x20E3, 0x20E3),
]

# Combined regex pattern for direct character matching
EMOJI_REGEX_STR = "[" + "".join(
    f"\\U{start:08X}-\\U{end:08X}" if start > 0xFFFF else f"\\u{start:04X}-\\u{end:04X}"
    for _, start, end in EMOJI_CATEGORIES
) + "]"

EMOJI_PATTERN = re.compile(EMOJI_REGEX_STR, re.UNICODE)
EMOJI_REGEX = EMOJI_PATTERN

# Pattern for encoded HTML entities: &#<decimal>; or &#x<hex>;
HTML_ENTITY_PATTERN = re.compile(r"&#(?:([0-9]+)|[xX]([0-9a-fA-F]+));")

# Default targets scanned for Career Studio compliance
DEFAULT_TARGET_DIRS = ["frontend", "docs", "tests", "scripts"]
DEFAULT_EXTENSIONS = {".html", ".js", ".css", ".py", ".md", ".json"}
DEFAULT_EXCLUDE_DIRS = {".git", "venv", "__pycache__", ".agents", "node_modules", "data"}

TARGET_FILES = [
    "frontend/templates/index.html",
    "frontend/css/dashboard.css",
    "frontend/js/dashboard.js",
    "docs/index.html",
    "docs/dashboard.css",
    "docs/dashboard.js"
]


class EmojiViolation(NamedTuple):
    file_path: str
    line_number: int
    char_code: str
    category: str
    char_repr: str
    snippet: str


def get_category_for_codepoint(cp: int) -> Optional[str]:
    """Identify category name if codepoint is within banned emoji ranges."""
    for cat_name, start, end in EMOJI_CATEGORIES:
        if start <= cp <= end:
            return cat_name
    return None


def is_emoji_codepoint(cp: int) -> bool:
    """Check if codepoint falls within any of the emoji categories."""
    return get_category_for_codepoint(cp) is not None


def check_text(text: str, file_path: str = "<memory>") -> List[EmojiViolation]:
    """
    Scan string content for emojis and return list of violations.
    Checks direct Unicode characters and HTML-encoded decimal/hex entities.
    """
    violations = []
    lines = text.splitlines()

    for line_idx, line in enumerate(lines, 1):
        # 1. Direct character scan
        for match in EMOJI_PATTERN.finditer(line):
            char = match.group()
            cp = ord(char)
            cat = get_category_for_codepoint(cp) or "Unknown Emoji"
            violations.append(
                EmojiViolation(
                    file_path=file_path,
                    line_number=line_idx,
                    char_code=f"U+{cp:04X}",
                    category=cat,
                    char_repr=char,
                    snippet=line.strip()[:100],
                )
            )

        # 2. Encoded HTML entity scan (e.g. amp-hash-digits)
        for match in HTML_ENTITY_PATTERN.finditer(line):
            dec_val, hex_val = match.groups()
            try:
                cp = int(hex_val, 16) if hex_val is not None else int(dec_val, 10)
            except (ValueError, TypeError):
                continue
            cat = get_category_for_codepoint(cp)
            if cat:
                violations.append(
                    EmojiViolation(
                        file_path=file_path,
                        line_number=line_idx,
                        char_code=f"U+{cp:04X} (HTML Entity: {match.group()})",
                        category=f"Encoded {cat}",
                        char_repr=match.group(),
                        snippet=line.strip()[:100],
                    )
                )

    return violations


def scan_file(file_path: Path) -> List[EmojiViolation]:
    """Scan a single file for emoji violations."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return check_text(content, str(file_path))
    except Exception as exc:
        print(f"[WARN] Could not read file {file_path}: {exc}", file=sys.stderr)
        return []


def scan_directory(
    root_path: Path,
    extensions: Optional[set] = None,
    exclude_dirs: Optional[set] = None,
) -> List[EmojiViolation]:
    """
    Recursively scan directory for emoji violations in matching files.
    """
    if extensions is None:
        extensions = DEFAULT_EXTENSIONS
    if exclude_dirs is None:
        exclude_dirs = DEFAULT_EXCLUDE_DIRS

    all_violations: List[EmojiViolation] = []

    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file_name in files:
            p = Path(root) / file_name
            if p.suffix.lower() in extensions:
                violations = scan_file(p)
                if violations:
                    all_violations.extend(violations)

    return all_violations


def scan_files(root_dir=".") -> bool:
    """
    Scans target files and returns True if 0 violations, False otherwise.
    Maintains compatibility with milestone runners.
    """
    project_root = Path(root_dir).resolve()
    status_code, violations = run_zero_emoji_audit(project_root)
    return status_code == 0


def run_zero_emoji_audit(
    base_dir: Path,
    targets: Optional[Sequence[str]] = None,
    extensions: Optional[set] = None,
) -> Tuple[int, List[EmojiViolation]]:
    """
    Execute standard zero-emoji audit.
    Returns (status_code, violations).
    """
    if targets is None:
        targets = DEFAULT_TARGET_DIRS

    violations: List[EmojiViolation] = []

    for target in targets:
        target_path = base_dir / target if not os.path.isabs(target) else Path(target)
        if not target_path.exists():
            continue
        if target_path.is_file():
            v = scan_file(target_path)
            violations.extend(v)
        else:
            v = scan_directory(target_path, extensions=extensions)
            violations.extend(v)

    status_code = 1 if violations else 0
    return status_code, violations


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify Zero-Emoji Compliance across Career Studio frontend, docs, and test files."
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=None,
        help="Target file or directory to scan (default: frontend, docs, tests, scripts in project root).",
    )
    parser.add_argument(
        "--targets",
        "-t",
        nargs="+",
        default=None,
        help="Specific subdirectories to scan relative to project root.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent

    if args.path:
        target_path = Path(args.path).resolve()
        if target_path.is_file():
            violations = scan_file(target_path)
        else:
            violations = scan_directory(target_path)
    else:
        targets = args.targets if args.targets else DEFAULT_TARGET_DIRS
        _, violations = run_zero_emoji_audit(project_root, targets=targets)

    if violations:
        print(
            f"\n[ZERO-EMOJI VIOLATION] Found {len(violations)} banned emoji occurrences:\n",
            file=sys.stderr,
        )
        for v in violations:
            print(
                f"  --> {v.file_path}:{v.line_number} [{v.char_code}] ({v.category})\n"
                f"      Snippet: {v.snippet}",
                file=sys.stderr,
            )
        print(
            f"\nAudit FAILED: Strict zero-emoji policy violated. Please replace emojis with Phosphor vector icons.",
            file=sys.stderr,
        )
        return 1

    print(
        f"[ZERO-EMOJI AUDIT PASSED] 0 emojis found across Career Studio files ({', '.join(args.targets or DEFAULT_TARGET_DIRS)})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
