#!/usr/bin/env python3
"""
Update job fit_gaps and condensed reasoning across datasets.
- Uses word-boundary token matching (preventing 'subscription' -> 'bsc' false positives).
- Preserves original reasoning in 'full_reasoning' so condensing is non-destructive.
- Uses public-safe professional gap descriptions without personal/military PII in published JSON.
- Anchors all paths to ROOT_DIR and writes via save_state_atomic with backup.
"""

import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.state_manager import save_state_atomic

_BSC_RE = re.compile(
    r"(?<![a-z0-9])b\.?sc(?:\.)?(?![a-z0-9])|תואר ראשון בהנדסת מכונות|תואר ראשון בהנדסת חשמל|תואר ראשון בהנדסה",
    re.IGNORECASE,
)
_PRACTICAL_ENG_RE = re.compile(
    r"הנדסאי(?:/ת)?|practical\s+engineer|או\s+הנדסאי",
    re.IGNORECASE,
)
_CIVIL_LRT_RE = re.compile(
    r"הנדסה אזרחית|הנדסאי בניין|מהנדס בניין|עבודות מול נת[\"״]ע|רכבת קלה|תשתיות מסילה|(?<![a-z0-9])lrt(?![a-z0-9])",
    re.IGNORECASE,
)
_AVIATION_AP_RE = re.compile(
    r"aircraft\s+mechanic|מבנאי[./]?ת מטוסים|רישיון רת[\"״]א|(?<![a-z0-9])a\s*&\s*p(?![a-z0-9])|רישיון תעופתי",
    re.IGNORECASE,
)
_SW_EMBEDDED_RE = re.compile(
    r"(?<![a-z0-9])c\+\+(?![a-z0-9])|(?<![a-z0-9])c#(?![a-z0-9])|\bembedded\b|תכנות בקרים מתקדם|פיתוח אלגוריתמים",
    re.IGNORECASE,
)
_SENIOR_MGMT_TITLE_RE = re.compile(
    r"\bsite\s+operations\s+manager\b|\bteam\s+lead\b|\bopex\s+leader\b|מנהל(?:/ת)?\s+פרויקטים",
    re.IGNORECASE,
)


def clean_sentence(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"[,;:\-]\s*$", "", s).strip()
    if s and not s.endswith("."):
        s += "."
    return s


def condense_reasoning(text: str, title: str = "", company: str = "") -> str:
    text = (text or "").strip()
    if not text:
        return "התאמה טכנית גבוהה לתחומי הנדסת מכונות, בקרה, מערכות אנרגיה ותפעול שטח."

    s = re.sub(r"^(המשרה הינה|המשרה דורשת|התפקיד כולל|התפקיד עוסק ב|מדובר ב)\s+", "", text)
    sentences = [part.strip() for part in re.split(r"[.!?]\s+", s) if part.strip()]
    if not sentences:
        return clean_sentence(text)

    res = sentences[0]
    if len(res) < 70 and len(sentences) > 1:
        res = f"{res}. {sentences[1]}"

    return clean_sentence(res.strip())


def analyze_fit_gaps(job: Dict[str, Any]) -> str:
    """
    Compute objective, public-safe requirement gaps for a job posting.
    Never embeds private personal/military/academic-timeline details into public datasets.
    """
    title = (job.get("title") or "").lower()
    reqs = (job.get("company_requirements") or "").lower()
    summary = (job.get("job_summary") or "").lower()
    snippet = (job.get("snippet") or "").lower()
    combined = f"{title} {reqs} {summary} {snippet}"

    gaps: List[str] = []

    # 1. Electrician License Requirement
    if any(k in combined for k in ["חשמלאי מוסמך", "רישיון חשמלאי", "רישיון חשמל", "חשמלאי/ת מוסמך"]):
        gaps.append("נדרש רישיון חשמלאי מוסמך בתוקף")
    elif "מתח גבוה" in combined:
        gaps.append("נדרש רישיון מתח גבוה ייעודי")

    # 2. B.Sc. / Academic Degree requirement (word-boundary checked)
    if _BSC_RE.search(combined) and not _PRACTICAL_ENG_RE.search(combined):
        gaps.append("דרישת סף לתואר B.Sc בהנדסה (ללא חלופת הנדסאי מכונות במודעה)")

    # 3. Civil / Railway / Infrastructure specific
    if _CIVIL_LRT_RE.search(combined):
        gaps.append("דרישת רקע ייעודי בהנדסה אזרחית ותשתיות מסילתיות")

    # 4. Aviation / A&P License
    if _AVIATION_AP_RE.search(combined):
        gaps.append("דרישת רישיון טכנאי תעופה מוסמך / מבנאי מורשה")

    # 5. Deep Software / Embedded / Senior PLC programming
    if _SW_EMBEDDED_RE.search(combined):
        gaps.append("דרישה לפיתוח תוכנה או תכנות בקרים מעמיק")

    # 6. Senior / Multi-year Management
    if _SENIOR_MGMT_TITLE_RE.search(title):
        gaps.append("דרישת שנות ניסיון רבות בניהול בכיר בתעשייה")

    if not gaps:
        return "אין פערי סף מהותיים מול דרישות התפקיד."
    if len(gaps) == 1:
        return gaps[0] + "."
    return "; ".join(gaps) + "."


def update_job_record_in_place(job: Dict[str, Any]) -> None:
    """Update fit_gaps and reasoning on a job dict while preserving full_reasoning."""
    if not isinstance(job, dict):
        return
    raw_reasoning = (job.get("full_reasoning") or job.get("reasoning") or "").strip()
    if raw_reasoning and not job.get("full_reasoning"):
        job["full_reasoning"] = raw_reasoning
    job["fit_gaps"] = analyze_fit_gaps(job)
    job["reasoning"] = condense_reasoning(
        raw_reasoning,
        job.get("title", ""),
        job.get("company", ""),
    )


def _backup_to_recovery(file_path: Path) -> None:
    """Save a pre-update backup inside .recovery/ (never inside data/ or docs/)."""
    if not file_path.exists():
        return
    recovery_dir = ROOT_DIR / ".recovery" / "backups"
    recovery_dir.mkdir(parents=True, exist_ok=True)
    rel_slug = str(file_path.relative_to(ROOT_DIR)).replace(os.sep, "__")
    shutil.copy2(file_path, recovery_dir / f"{rel_slug}.bak")


def main(base_dir: Path = ROOT_DIR) -> int:
    paths = [
        base_dir / "docs" / "data" / "jobs.json",
        base_dir / "data" / "weekly_archive.json",
    ]
    cat_paths = [
        base_dir / "data" / "historical_catalog.json",
        base_dir / "docs" / "data" / "historical_catalog.json",
    ]

    updated_files = 0

    for p in paths:
        if not p.exists():
            continue
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_dict_envelope = isinstance(data, dict) and "jobs" in data
        jobs_list = data["jobs"] if is_dict_envelope else data

        print(f"Updating {len(jobs_list)} jobs in {p}...")
        for j in jobs_list:
            update_job_record_in_place(j)

        _backup_to_recovery(p)
        save_state_atomic(str(p), data)
        updated_files += 1

    for cp in cat_paths:
        if not cp.exists():
            continue
        with open(cp, "r", encoding="utf-8") as f:
            cat = json.load(f)
        print(f"Updating {len(cat)} catalog jobs in {cp}...")
        for j in cat.values():
            update_job_record_in_place(j)

        _backup_to_recovery(cp)
        save_state_atomic(str(cp), cat)
        updated_files += 1

    if updated_files == 0:
        raise FileNotFoundError(f"No target job dataset files found under {base_dir}")

    print(f"Updated {updated_files} dataset files successfully.")
    return updated_files


if __name__ == "__main__":
    main()
