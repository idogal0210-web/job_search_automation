"""Centralized configuration loader for job search automation.

Loads policies, search keywords, company targets, and aliases from search-preferences.json
or local private override, providing resilient defaults.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent

DEFAULT_PREFERENCES_PATH = (
    ROOT_DIR / ".agents" / "skills" / "job-search-automation-state" / "references" / "search-preferences.json"
)
LOCAL_OVERRIDE_PATH = ROOT_DIR / "data" / "search_preferences.local.json"

_CACHED_CONFIG: Dict[str, Any] = {}


def load_raw_config() -> Dict[str, Any]:
    """Load configuration dictionary from local override or workspace references."""
    global _CACHED_CONFIG
    if _CACHED_CONFIG:
        return _CACHED_CONFIG

    data = {}
    if LOCAL_OVERRIDE_PATH.exists():
        try:
            with open(LOCAL_OVERRIDE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    if not data and DEFAULT_PREFERENCES_PATH.exists():
        try:
            with open(DEFAULT_PREFERENCES_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load search-preferences.json: {e}")
            data = {}

    _CACHED_CONFIG = data
    return _CACHED_CONFIG


def get_search_keywords() -> Dict[str, List[str]]:
    """Return search keyword lists by source channel."""
    cfg = load_raw_config()
    keywords = cfg.get("search_keywords", {})
    return {
        "energy": list(keywords.get("energy", [])),
        "drones": list(keywords.get("drones", [])),
        "drushim": list(keywords.get("drushim", [])),
        "indeed": list(keywords.get("indeed", [])),
        "glassdoor": list(keywords.get("glassdoor", [])),
    }


def get_hebrew_company_aliases() -> Dict[str, str]:
    """Return dictionary mapping Hebrew names to canonical English company identifiers."""
    cfg = load_raw_config()
    return dict(cfg.get("hebrew_company_aliases", {}))


def get_target_companies() -> Tuple[List[str], Dict[str, List[str]]]:
    """Return (flat_target_companies_list, categorized_target_companies_dict)."""
    cfg = load_raw_config()
    targets = cfg.get("target_companies", [])
    categories = cfg.get("target_companies_by_category", {})
    return list(targets), dict(categories)


def get_excluded_employers() -> List[str]:
    """Return list of excluded employers from environment or configuration."""
    env_blacklist = os.environ.get("EXCLUDED_EMPLOYERS", "")
    if env_blacklist:
        return [e.strip().lower() for e in env_blacklist.split(",") if e.strip()]

    cfg = load_raw_config()
    excluded = cfg.get("excluded_employers", [])
    if excluded:
        return [e.strip().lower() for e in excluded if e.strip()]

    return ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון"]


def get_salary_policy() -> Dict[str, int]:
    """Return salary thresholds in ILS."""
    cfg = load_raw_config()
    policy = cfg.get("salary_policy", {})
    return {
        "absolute_floor": policy.get("absolute_floor_ils", 15000),
        "high_threshold": policy.get("high_salary_threshold_ils", 18000),
        "shifts_24_7_floor": policy.get("shifts_24_7_floor_ils", 20000),
    }
