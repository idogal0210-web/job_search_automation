"""Few-Shot Feedback Loop: Supabase triage state to LLM calibration.

Safely fetches recent starred and rejected user triage decisions from
Supabase public.sync_state (with graceful offline/CI fallback), joins them
with local catalog metadata, and builds a concise, bounded few-shot prompt
block for GeminiPool evaluation without any PII.
"""
from __future__ import annotations

import json
import os
import re
import ssl
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request

from src.url_utils import canonical_job_url, stable_job_id

ROOT_DIR = Path(__file__).resolve().parent.parent

# Default Supabase endpoint (read-only triage mirror)
DEFAULT_SUPABASE_URL = "https://wvwdxpttwsrdbvvtiyoh.supabase.co"
DEFAULT_SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2d2R4cHR0d3NyZGJ2dnRpeW9oIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQyNjA0MTcsImV4cCI6MjEwOTgzNjQxN30."
    "YUun0ttLje3gwWvOU-ACimAtX-xgbUbXhJoELCsx0V4"
)


def _safe_ssl_context() -> ssl.SSLContext:
    """Create an SSL context supporting system or certifi bundles."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch_triage_feedback_keys(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    user_token: Optional[str] = None,
    timeout: int = 5,
    fallback_file: Optional[Path] = None,
) -> Dict[str, List[str]]:
    """
    Safely retrieve lists of starred and rejected job identifiers.
    
    Attempts live read from Supabase REST endpoint first. If credentials
    are absent, network fails, or execution is in CI without access, silently
    falls back to local data/sync_state.json snapshot.
    Returns: {"starred": [...], "rejected": [...]}
    """
    url = (supabase_url or os.getenv("SUPABASE_URL") or DEFAULT_SUPABASE_URL).rstrip("/")
    key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or DEFAULT_SUPABASE_ANON_KEY
    auth_token = user_token or os.getenv("SUPABASE_USER_TOKEN") or key

    # 1. Attempt remote fetch
    if url and key:
        rest_url = f"{url}/rest/v1/sync_state?select=payload,updated_at&order=updated_at.desc&limit=1"
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {auth_token}",
            "User-Agent": "JobSearchAutomation-FeedbackLoop/1.0",
            "Accept": "application/json",
        }
        try:
            req = urllib.request.Request(rest_url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout, context=_safe_ssl_context()) as resp:
                if resp.status == 200:
                    rows = json.loads(resp.read().decode("utf-8"))
                    if isinstance(rows, list) and rows:
                        payload = rows[0].get("payload") or {}
                        if isinstance(payload, dict):
                            starred = [str(k) for k in payload.get("starred", []) if str(k).strip()]
                            rejected = [str(k) for k in payload.get("rejected", []) if str(k).strip()]
                            if starred or rejected:
                                return {"starred": starred, "rejected": rejected}
        except Exception:
            # Graceful silent degradation on any network, SSL, or auth failure
            pass

    # 2. Local fallback
    local_path = fallback_file or (ROOT_DIR / "data" / "sync_state.json")
    if local_path.exists():
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            payload = data.get("payload", data) if isinstance(data, dict) else {}
            if isinstance(payload, dict):
                return {
                    "starred": [str(k) for k in payload.get("starred", []) if str(k).strip()],
                    "rejected": [str(k) for k in payload.get("rejected", []) if str(k).strip()],
                }
        except Exception:
            pass

    return {"starred": [], "rejected": []}


def _clean_summary_snippet(text: str, max_chars: int = 120) -> str:
    """Normalize and truncate summary snippet to bounded length, removing formatting noise."""
    if not text:
        return ""
    clean = re.sub(r"[\r\n\t]+", " ", str(text))
    clean = re.sub(r"\s+", " ", clean).strip()
    if len(clean) > max_chars:
        return clean[:max_chars].rstrip() + "..."
    return clean


def build_catalog_job_index(root_dir: Optional[Path] = None) -> Dict[str, Dict[str, str]]:
    """
    Build an index of known jobs from historical catalogs and weekly archives.
    Maps canonical URLs, raw links, and stable IDs to stripped job summaries without PII.
    """
    base = root_dir or ROOT_DIR
    index: Dict[str, Dict[str, str]] = {}

    paths = [
        base / "docs" / "data" / "historical_catalog.json",
        base / "data" / "historical_catalog.json",
        base / "data" / "weekly_archive.json",
        base / "docs" / "data" / "jobs.json",
    ]

    for p in paths:
        if not p.exists():
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                raw = json.load(f)
            items: List[Dict[str, Any]] = []
            if isinstance(raw, dict):
                # Dict keyed by link or object with 'jobs'
                if "jobs" in raw and isinstance(raw["jobs"], list):
                    items = raw["jobs"]
                else:
                    items = [v for v in raw.values() if isinstance(v, dict)]
            elif isinstance(raw, list):
                items = [v for v in raw if isinstance(v, dict)]

            for item in items:
                title = str(item.get("title") or "").strip()
                company = str(item.get("company") or "").strip()
                if not title or not company:
                    continue

                summary = (
                    item.get("job_summary")
                    or item.get("company_requirements")
                    or item.get("reasoning")
                    or item.get("snippet")
                    or ""
                )
                stripped_item = {
                    "company": company,
                    "title": title,
                    "summary": _clean_summary_snippet(summary),
                }

                link = str(item.get("link") or "").strip()
                if link:
                    index[link] = stripped_item
                    canon = canonical_job_url(link)
                    if canon:
                        index[canon] = stripped_item

                sid = stable_job_id(item)
                if sid:
                    index[sid] = stripped_item
        except Exception:
            continue

    return index


def get_few_shot_calibration_data(
    max_starred: int = 5,
    max_rejected: int = 5,
    catalog_index: Optional[Dict[str, Dict[str, str]]] = None,
    feedback_keys: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, List[Dict[str, str]]]:
    """
    Match recent starred and rejected keys against catalog data.
    Takes up to max_starred and max_rejected items.
    """
    keys_map = feedback_keys if feedback_keys is not None else fetch_triage_feedback_keys()
    index = catalog_index if catalog_index is not None else build_catalog_job_index()

    def resolve_items(key_list: List[str], limit: int) -> List[Dict[str, str]]:
        resolved: List[Dict[str, str]] = []
        seen_titles = set()
        # Iterate from most recent (end of list) backwards
        for k in reversed(key_list):
            item = index.get(k) or index.get(canonical_job_url(k)) or index.get(stable_job_id(k))
            if item:
                pair = (item["company"].casefold(), item["title"].casefold())
                if pair not in seen_titles:
                    seen_titles.add(pair)
                    resolved.append(dict(item))
                    if len(resolved) >= limit:
                        break
        return resolved

    return {
        "starred": resolve_items(keys_map.get("starred", []), max_starred),
        "rejected": resolve_items(keys_map.get("rejected", []), max_rejected),
    }


def format_few_shot_prompt_block(few_shot_data: Dict[str, List[Dict[str, str]]]) -> str:
    """
    Format calibrated few-shot examples into a bounded prompt block.
    Returns empty string if no examples are available.
    """
    starred = few_shot_data.get("starred") or []
    rejected = few_shot_data.get("rejected") or []

    if not starred and not rejected:
        return ""

    lines = ["Candidate triage calibration (Real feedback preferences):"]
    if starred:
        lines.append("- Highly desired roles (starred by candidate):")
        for item in starred[:5]:
            snippet = f" | Focus: {item['summary']}" if item.get("summary") else ""
            lines.append(f"  * {item['company']} - {item['title']}{snippet}")

    if rejected:
        lines.append("- Disqualified / unwanted roles (rejected by candidate):")
        for item in rejected[:5]:
            snippet = f" | Note: {item['summary']}" if item.get("summary") else ""
            lines.append(f"  * {item['company']} - {item['title']}{snippet}")

    lines.append("")
    # Bounded length: truncate block to max 1200 chars to avoid prompt bloat
    full_block = "\n".join(lines)
    return full_block[:1200]


_CACHED_FEW_SHOT_BLOCK: Optional[str] = None


def get_few_shot_block(force_refresh: bool = False) -> str:
    """Return cached few-shot prompt block, fetching and formatting once per session."""
    global _CACHED_FEW_SHOT_BLOCK
    if _CACHED_FEW_SHOT_BLOCK is not None and not force_refresh:
        return _CACHED_FEW_SHOT_BLOCK
    try:
        calib_data = get_few_shot_calibration_data()
        formatted = format_few_shot_prompt_block(calib_data)
        _CACHED_FEW_SHOT_BLOCK = f"{formatted}\n" if formatted else ""
    except Exception:
        _CACHED_FEW_SHOT_BLOCK = ""
    return _CACHED_FEW_SHOT_BLOCK

