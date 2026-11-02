"""URL validation and conservative job identity without changing stored URLs."""
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode


def safe_http_url(value):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value):
        return ""
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
            return ""
        parsed.port
        return value.strip()
    except ValueError:
        return ""


def canonical_job_url(value):
    value = safe_http_url(value)
    if not value:
        return ""
    p = urlsplit(value)
    host = p.hostname.lower()
    if host in {"linkedin.com", "www.linkedin.com", "il.linkedin.com"}:
        match = re.search(r"/jobs/view/(?:[^/]*-)?(\d+)/?$", p.path)
        if match:
            return "https://www.linkedin.com/jobs/view/" + match.group(1)
    query = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in {"trk", "trackingid", "refid", "fbclid", "gclid"}]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/") or "/", urlencode(sorted(query)), ""))


def job_identity(job):
    source, source_id = job.get("source"), job.get("source_id")
    if source and source_id:
        return (str(source).casefold(), str(job.get("company", "")).casefold(), str(source_id))
    return (canonical_job_url(job.get("link")),)


def stable_job_id(job_or_link):
    """Produces a deterministic, unique identifier for a job across scraper variations."""
    if isinstance(job_or_link, str):
        link = job_or_link
        job = {}
    elif isinstance(job_or_link, dict):
        link = job_or_link.get("link", "")
        job = job_or_link
    else:
        return ""

    canon = canonical_job_url(link) if link else ""
    raw = canon or str(link).strip()

    # Check for known ATS / Job Board ID patterns
    m_li = re.search(r"/jobs/view/(?:[^/]*-)?(\d+)", raw)
    if m_li:
        return f"li_{m_li.group(1)}"

    m_comeet = re.search(r"comeet\.com/jobs/(?:[^/]+/)+([^/?#]+)", raw, re.IGNORECASE)
    if m_comeet:
        return f"comeet_{m_comeet.group(1)}"

    m_drushim = re.search(r"/job/(\d+)", raw)
    if m_drushim:
        return f"drushim_{m_drushim.group(1)}"

    # Content-based hash fallback if company and title exist
    company = " ".join((job.get("company") or "").casefold().split())
    title = " ".join((job.get("title") or "").casefold().split())
    if company and title:
        import hashlib
        h = hashlib.sha256(f"{company}|{title}".encode("utf-8")).hexdigest()[:12]
        return f"ch_{h}"

    return canon or str(link).strip()


def content_identity(job):
    """Exact cross-source copies only; titles alone are never sufficient."""
    normalize = lambda value: " ".join(str(value or "").casefold().split())
    values = tuple(normalize(job.get(key)) for key in ("company", "title", "location"))
    description = normalize(job.get("description") or job.get("snippet"))
    if not all(values) or len(description) < 200 or values[0] in {"חברה", "חברה מובילה (דיסקרטי)"}:
        return None
    return (*values, description)
