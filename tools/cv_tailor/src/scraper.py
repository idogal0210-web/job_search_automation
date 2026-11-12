import re
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
try:
    from tools.cv_tailor.src.utils import print_info, print_warning, print_success
    from src.ats_client import fetch_ats_job_detail
except ModuleNotFoundError:
    from src.utils import print_info, print_warning, print_success
    fetch_ats_job_detail = None

@dataclass
class JobPosting:
    url: Optional[str]
    title: str
    company: str
    location: str
    raw_text: str
    description: str
    requirements: str
    source: str = "direct"

def scrape_with_firecrawl(url: str, api_key: str) -> Optional[dict]:
    """Scrape web page using Firecrawl REST API."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "formats": ["markdown", "html"]
        }
        res = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=25)
        if res.status_code == 200:
            data = res.json()
            if data.get("success") and "data" in data:
                return data["data"]
        return None
    except Exception as e:
        print_warning(f"Firecrawl scrape failed: {e}")
        return None

def scrape_with_bs4(url: str) -> str:
    """Scrape web page using standard requests + BeautifulSoup fallback."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    
    # Remove script, style, nav, footer, header tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()
    
    lines = (line.strip() for line in soup.get_text().splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    clean_text = "\n".join(chunk for chunk in chunks if chunk)
    return clean_text

def scrape_job(url: str, firecrawl_key: str = None, company_hint: str = "", title_hint: str = "") -> JobPosting:
    """Scrape a job posting using API-first ATS extraction, then Firecrawl or BeautifulSoup."""
    print_info(f"סורק משרה מהכתובת: {url}")

    if fetch_ats_job_detail is not None:
        ats_res = fetch_ats_job_detail(url)
        if ats_res and ats_res.get("ok") and ats_res.get("job"):
            ats_job = ats_res["job"]
            desc = (ats_job.get("description") or "").strip()
            if desc:
                print_success(f"שליפת API ישירה הושלמה ({ats_res.get('provider')}) ללא צורך ב-Firecrawl.")
                return JobPosting(
                    url=ats_job.get("url") or url,
                    title=title_hint.strip() or ats_job.get("title") or "משרה ללא כותרת",
                    company=company_hint.strip() or ats_job.get("company") or "חברה לא צוינה",
                    location=ats_job.get("location") or "",
                    raw_text=desc,
                    description=desc,
                    requirements=desc,
                    source=ats_job.get("source") or "ats_direct",
                )

    raw_content = ""
    source = "bs4_fallback"
    
    if firecrawl_key:
        print_info("משתמש ב-Firecrawl API לגריפה מדויקת...")
        fc_data = scrape_with_firecrawl(url, firecrawl_key)
        if fc_data and "markdown" in fc_data:
            raw_content = fc_data["markdown"]
            source = "firecrawl"
            print_success("גריפה באמצעות Firecrawl הושלמה בהצלחה.")
            
    if not raw_content:
        if firecrawl_key:
            print_warning("מעבר לגריפה באמצעות fallback ישיר (BeautifulSoup)...")
        else:
            print_info("גורף ישירות באמצעות BeautifulSoup...")
        raw_content = scrape_with_bs4(url)
        print_success("גריפה ישירה הושלמה.")
        
    return parse_job_text(raw_content, url=url, company_hint=company_hint, title_hint=title_hint, source=source)

def parse_job_text(text: str, url: str = None, company_hint: str = "", title_hint: str = "", source: str = "direct") -> JobPosting:
    """Parse raw job text into structured JobPosting object."""
    clean_text = text.strip()
    title = title_hint.strip()
    company = company_hint.strip()
    location = ""

    # Basic heuristic extraction if not provided
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
    if not title and lines:
        title = lines[0][:80]
    if not company and len(lines) > 1:
        # Check if 2nd line contains company name
        company = lines[1][:50]

    return JobPosting(
        url=url,
        title=title or "משרה ללא כותרת",
        company=company or "חברה לא צוינה",
        location=location,
        raw_text=clean_text,
        description=clean_text,
        requirements=clean_text,
        source=source
    )
