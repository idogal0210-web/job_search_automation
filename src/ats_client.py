"""Shared direct ATS API helpers for Greenhouse, Lever, Ashby, and Comeet.

Provides lightweight, zero-browser HTTP/JSON extraction for both:
- Single-URL job detail lookup (Career Studio ingestion, pipeline enrichment, inactive scanning)
- Clean HTML-to-text normalization shared across direct ATS fetchers
"""
from __future__ import annotations

import html
import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlsplit

import requests


_COMEET_POSITIONS_RE = re.compile(
    r"COMPANY_POSITIONS_DATA\s*=\s*(\[.*?\]);\s*(?:COMPANY|POSITION|\n|</script>)",
    re.DOTALL,
)


def html_to_clean_text(raw_html: str) -> str:
    """Convert ATS HTML or HTML-escaped markup into readable plain text."""
    if not raw_html:
        return ""
    unescaped = html.unescape(str(raw_html))
    with_breaks = re.sub(r"</(?:p|div|li|h[1-6]|tr|section)>|<br\s*/?>", "\n", unescaped, flags=re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", " ", with_breaks)
    lines = [" ".join(line.split()) for line in stripped.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def format_lever_description(item: Dict[str, Any]) -> str:
    """Build clean plain-text job description from a Lever posting JSON object."""
    parts: List[str] = []
    intro = (item.get("descriptionPlain") or html_to_clean_text(item.get("description") or "")).strip()
    if intro:
        parts.append(intro)
    for section in item.get("lists") or []:
        if not isinstance(section, dict):
            continue
        heading = (section.get("text") or "").strip()
        body = html_to_clean_text(section.get("content") or "")
        if heading and body:
            parts.append(f"{heading}:\n{body}")
        elif body:
            parts.append(body)
    additional = (item.get("additionalPlain") or html_to_clean_text(item.get("additional") or "")).strip()
    if additional:
        parts.append(additional)
    return "\n\n".join(parts).strip()


def parse_comeet_positions(html_text: str) -> Optional[List[Dict[str, Any]]]:
    """Extract COMPANY_POSITIONS_DATA JSON array from a Comeet career page."""
    match = _COMEET_POSITIONS_RE.search(html_text or "")
    if not match:
        return None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, list) else None


def parse_ats_url(url: str) -> Optional[Dict[str, str]]:
    """Identify supported public ATS job URLs and extract provider + identifiers."""
    if not isinstance(url, str):
        return None
    raw = url.strip()
    if not raw:
        return None
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return None

    host = parsed.hostname.lower()
    path = parsed.path.strip("/")
    segments = [seg for seg in path.split("/") if seg]

    # Greenhouse: boards.greenhouse.io/<slug>/jobs/<id> or job-boards(.eu).greenhouse.io/<slug>/jobs/<id>
    if host in {"boards.greenhouse.io", "job-boards.greenhouse.io", "job-boards.eu.greenhouse.io"}:
        if len(segments) >= 3 and segments[1].lower() == "jobs" and segments[2].isdigit():
            return {
                "provider": "greenhouse",
                "company_slug": segments[0],
                "job_id": segments[2],
            }

    # Lever: jobs.lever.co/<slug>/<uuid> or jobs.eu.lever.co/<slug>/<uuid>
    if host in {"jobs.lever.co", "jobs.eu.lever.co"} and len(segments) >= 2:
        uuid_match = re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            segments[1],
            re.IGNORECASE,
        )
        if uuid_match:
            return {
                "provider": "lever",
                "company_slug": segments[0],
                "job_id": segments[1].lower(),
                "is_eu": "1" if ".eu." in host else "",
            }

    # Ashby: jobs.ashbyhq.com/<slug>/<uuid>
    if host == "jobs.ashbyhq.com" and len(segments) >= 2:
        uuid_match = re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            segments[1],
            re.IGNORECASE,
        )
        if uuid_match:
            return {
                "provider": "ashby",
                "company_slug": segments[0],
                "job_id": segments[1].lower(),
            }

    # Comeet: www.comeet.com/jobs/<slug>/<uid>/<title-slug>/<pos_uid>
    if host in {"comeet.com", "www.comeet.com"} and len(segments) >= 5 and segments[0].lower() == "jobs":
        return {
            "provider": "comeet",
            "company_slug": segments[1],
            "company_uid": segments[2],
            "job_id": segments[4],
        }

    return None


def _default_headers() -> Dict[str, str]:
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }


def _fetch_greenhouse_detail(meta: Dict[str, str], client: Any, timeout: int) -> Dict[str, Any]:
    api_url = f"https://boards-api.greenhouse.io/v1/boards/{meta['company_slug']}/jobs/{meta['job_id']}"
    resp = client.get(api_url, headers=_default_headers(), timeout=timeout)
    if resp.status_code in (404, 410):
        return {"ok": False, "state": "inactive", "provider": "greenhouse", "reason": f"המשרה הוסרה מ-Greenhouse (HTTP {resp.status_code})", "status_code": resp.status_code, "job": None}
    if resp.status_code != 200:
        return {"ok": False, "state": "unknown", "provider": "greenhouse", "reason": f"Greenhouse HTTP {resp.status_code}", "status_code": resp.status_code, "job": None}

    data = resp.json()
    loc = (data.get("location") or {}).get("name") or ""
    description = html_to_clean_text(data.get("content") or "")
    title = (data.get("title") or "").strip()
    company = (data.get("company_name") or meta["company_slug"]).strip()
    return {
        "ok": True,
        "state": "active",
        "provider": "greenhouse",
        "reason": "משרה פעילה ומאומתת ב-Greenhouse API",
        "status_code": 200,
        "job": {
            "url": data.get("absolute_url") or "",
            "title": title,
            "company": company,
            "location": loc,
            "description": description,
            "source": "ats_greenhouse_api",
        },
    }


def _fetch_lever_detail(meta: Dict[str, str], client: Any, timeout: int) -> Dict[str, Any]:
    api_host = "api.eu.lever.co" if meta.get("is_eu") else "api.lever.co"
    api_url = f"https://{api_host}/v0/postings/{meta['company_slug']}/{meta['job_id']}"
    resp = client.get(api_url, headers=_default_headers(), timeout=timeout)
    if resp.status_code in (404, 410):
        return {"ok": False, "state": "inactive", "provider": "lever", "reason": f"המשרה הוסרה מ-Lever (HTTP {resp.status_code})", "status_code": resp.status_code, "job": None}
    if resp.status_code != 200:
        return {"ok": False, "state": "unknown", "provider": "lever", "reason": f"Lever HTTP {resp.status_code}", "status_code": resp.status_code, "job": None}

    data = resp.json()
    cats = data.get("categories") or {}
    loc = (cats.get("location") or "").strip()
    description = format_lever_description(data)
    title = (data.get("text") or "").strip()
    return {
        "ok": True,
        "state": "active",
        "provider": "lever",
        "reason": "משרה פעילה ומאומתת ב-Lever API",
        "status_code": 200,
        "job": {
            "url": data.get("hostedUrl") or "",
            "title": title,
            "company": meta["company_slug"],
            "location": loc,
            "description": description,
            "source": "ats_lever_api",
        },
    }


def _fetch_ashby_detail(meta: Dict[str, str], client: Any, timeout: int) -> Dict[str, Any]:
    api_url = f"https://api.ashbyhq.com/posting-api/job-board/{meta['company_slug']}"
    resp = client.get(api_url, headers=_default_headers(), timeout=timeout)
    if resp.status_code in (404, 410):
        return {"ok": False, "state": "inactive", "provider": "ashby", "reason": f"לוח Ashby לא נמצא (HTTP {resp.status_code})", "status_code": resp.status_code, "job": None}
    if resp.status_code != 200:
        return {"ok": False, "state": "unknown", "provider": "ashby", "reason": f"Ashby HTTP {resp.status_code}", "status_code": resp.status_code, "job": None}

    data = resp.json()
    jobs = data.get("jobs")
    if not isinstance(jobs, list):
        return {"ok": False, "state": "unknown", "provider": "ashby", "reason": "תגובת Ashby אינה תקינה", "status_code": 200, "job": None}

    target_id = meta["job_id"].lower()
    matched = next(
        (item for item in jobs if isinstance(item, dict) and str(item.get("id") or "").lower() == target_id),
        None,
    )
    if matched is None:
        return {"ok": False, "state": "inactive", "provider": "ashby", "reason": "המשרה אינה מופיעה עוד בלוח הפעיל של Ashby", "status_code": 200, "job": None}

    description = (matched.get("descriptionPlain") or html_to_clean_text(matched.get("descriptionHtml") or "")).strip()
    return {
        "ok": True,
        "state": "active",
        "provider": "ashby",
        "reason": "משרה פעילה ומאומתת ב-Ashby API",
        "status_code": 200,
        "job": {
            "url": matched.get("jobUrl") or "",
            "title": (matched.get("title") or "").strip(),
            "company": meta["company_slug"],
            "location": (matched.get("location") or "").strip(),
            "description": description,
            "source": "ats_ashby_api",
        },
    }


def _fetch_comeet_detail(meta: Dict[str, str], client: Any, timeout: int) -> Dict[str, Any]:
    board_url = f"https://www.comeet.com/jobs/{meta['company_slug']}/{meta['company_uid']}"
    resp = client.get(board_url, headers=_default_headers(), timeout=timeout)
    if resp.status_code in (404, 410):
        return {"ok": False, "state": "inactive", "provider": "comeet", "reason": f"דף המשרות הוסר מ-Comeet (HTTP {resp.status_code})", "status_code": resp.status_code, "job": None}
    if resp.status_code != 200:
        return {"ok": False, "state": "unknown", "provider": "comeet", "reason": f"Comeet HTTP {resp.status_code}", "status_code": resp.status_code, "job": None}

    positions = parse_comeet_positions(resp.text)
    if positions is None:
        return {"ok": False, "state": "unknown", "provider": "comeet", "reason": "לא נמצא payload משרות בדף Comeet", "status_code": 200, "job": None}

    target_uid = meta["job_id"].lower()
    matched = next(
        (pos for pos in positions if isinstance(pos, dict) and str(pos.get("uid") or "").lower() == target_uid),
        None,
    )
    if matched is None:
        return {"ok": False, "state": "inactive", "provider": "comeet", "reason": "המשרה אינה מופיעה עוד ברשימת המשרות הפעילות ב-Comeet", "status_code": 200, "job": None}

    loc_obj = matched.get("location") or {}
    loc_parts = [loc_obj.get("city"), loc_obj.get("name") or loc_obj.get("country")]
    loc_str = ", ".join(p for p in loc_parts if p)

    details = (matched.get("custom_fields") or {}).get("details", [])
    desc_parts = []
    for d in details:
        val = html_to_clean_text(d.get("value") or "")
        if val:
            desc_parts.append(f"{d.get('name', 'Details')}: {val}")
    description = "\n\n".join(desc_parts).strip()

    return {
        "ok": True,
        "state": "active",
        "provider": "comeet",
        "reason": "משרה פעילה ומאומתת ב-Comeet",
        "status_code": 200,
        "job": {
            "url": matched.get("url_active_page") or matched.get("url_comeet_hosted_page") or "",
            "title": (matched.get("name") or "").strip(),
            "company": meta["company_slug"],
            "location": loc_str,
            "description": description,
            "source": "ats_comeet_api",
        },
    }


def fetch_ats_job_detail(url: str, session: Any = None, timeout: int = 12) -> Optional[Dict[str, Any]]:
    """
    Fetch structured job metadata and state directly from a supported ATS API.
    Returns None when URL does not match a known ATS pattern.
    """
    meta = parse_ats_url(url)
    if not meta:
        return None

    client = session or requests
    provider = meta["provider"]
    dispatch = {
        "greenhouse": _fetch_greenhouse_detail,
        "lever": _fetch_lever_detail,
        "ashby": _fetch_ashby_detail,
        "comeet": _fetch_comeet_detail,
    }
    handler = dispatch.get(provider)
    if not handler:
        return None

    try:
        return handler(meta, client, timeout)
    except (requests.RequestException, TimeoutError, ValueError) as exc:
        return {
            "ok": False,
            "state": "unknown",
            "provider": provider,
            "reason": f"שגיאת תקשורת מול {provider}: {type(exc).__name__}",
            "status_code": 0,
            "job": None,
        }
