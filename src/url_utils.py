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


def normalize_text_for_hash(text: str) -> str:
    """Normalize company or title string to prevent slight variations from resurrecting jobs."""
    if not text:
        return ""
    # Strip invisible formatting characters (ZWJ, LTR, RTL, non-breaking space)
    cleaned = re.sub(r"[\u200b-\u200f\u00a0\ufeff]", " ", str(text))
    cleaned = cleaned.casefold()
    # Normalize gendered Hebrew slashes e.g. 'טכנאי/ת', 'מהנדס/ת', 'מנהל/ת', 'בקר/ית'
    cleaned = re.sub(r"/ת\b|/ה\b|/ית\b", "", cleaned)
    # Remove noise qualifiers e.g. (m/f), (דרוש/ה), (דיסקרטי)
    cleaned = re.sub(r"\((?:m/f|d/m/w|גברים/נשים|מ/נ|דיסקרטי|דרושים|דרוש|דרושה)\)", " ", cleaned)
    # Remove common company corporate suffixes
    cleaned = re.sub(r"\b(?:בע\"מ|בעמ|בע״מ|ltd\.?|inc\.?|corp\.?|gmbh|llc)\b", " ", cleaned)
    # Replace punctuation with space
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    # Collapse whitespace
    return " ".join(cleaned.split())


def content_job_hash(job_or_dict):
    """Generates a stable 12-char content hash based on normalized company and title."""
    if not isinstance(job_or_dict, dict):
        return ""
    company = normalize_text_for_hash(job_or_dict.get("company", ""))
    title = normalize_text_for_hash(job_or_dict.get("title", ""))
    if company and title:
        import hashlib
        h = hashlib.sha256(f"{company}|{title}".encode("utf-8")).hexdigest()[:12]
        return f"ch_{h}"
    return ""


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

    m_gh = re.search(r"(?:job-boards|boards)(?:\.eu)?\.greenhouse\.io/[^/]+/jobs/(\d+)", raw, re.IGNORECASE)
    if m_gh:
        return f"gh_{m_gh.group(1)}"

    m_lever = re.search(r"jobs\.(?:eu\.)?lever\.co/[^/]+/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", raw, re.IGNORECASE)
    if m_lever:
        return f"lever_{m_lever.group(1).lower()}"

    m_ashby = re.search(r"jobs\.ashbyhq\.com/[^/]+/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", raw, re.IGNORECASE)
    if m_ashby:
        return f"ashby_{m_ashby.group(1).lower()}"

    # Content-based hash fallback if company and title exist
    ch = content_job_hash(job)
    if ch:
        return ch

    return canon or str(link).strip()


def content_identity(job):
    """Exact cross-source copies only; titles alone are never sufficient."""
    normalize = lambda value: " ".join(str(value or "").casefold().split())
    values = tuple(normalize(job.get(key)) for key in ("company", "title", "location"))
    description = normalize(job.get("description") or job.get("snippet"))
    if not all(values) or len(description) < 200 or values[0] in {"חברה", "חברה מובילה (דיסקרטי)"}:
        return None
    return (*values, description)
