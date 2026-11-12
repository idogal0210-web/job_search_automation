import json
import re
import time
import requests
import random
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urlsplit
from src.ats_client import format_lever_description, html_to_clean_text, parse_comeet_positions
from src.url_utils import safe_http_url, canonical_job_url

try:
    from curl_cffi import requests as cffi_requests
except ImportError:
    cffi_requests = None

def _get_with_retries(client, url, **kwargs):
    """Retry transient read failures only, with bounded exponential delay."""
    for attempt in range(3):
        try:
            response = client.get(url, **kwargs)
            if response.status_code not in {429, 500, 502, 503, 504} or attempt == 2:
                return response
            delay = _retry_delay(response, attempt)
            if delay > 30:
                return response  # Defer instead of retrying before the server permits it.
        except (requests.RequestException, TimeoutError):
            if attempt == 2:
                raise
            delay = 2 ** attempt
        time.sleep(delay)


def _retry_delay(response, attempt):
    try:
        retry_after = float(response.headers.get("Retry-After", 0))
    except (TypeError, ValueError):
        retry_after = 0
    return max(2 ** attempt, retry_after)


def _source_url(link, domain):
    if not safe_http_url(link):
        return False
    host = urlsplit(link).hostname
    return host == domain or host.endswith("." + domain)


@dataclass
class RunHealth:
    linkedin_requests: int = 0
    linkedin_successes: int = 0
    linkedin_failures: int = 0
    linkedin_jobs_found: int = 0
    
    drushim_requests: int = 0
    drushim_successes: int = 0
    drushim_failures: int = 0
    drushim_jobs_found: int = 0
    
    comeet_requests: int = 0
    comeet_successes: int = 0
    comeet_failures: int = 0
    comeet_jobs_found: int = 0

    greenhouse_requests: int = 0
    greenhouse_successes: int = 0
    greenhouse_failures: int = 0
    greenhouse_jobs_found: int = 0

    lever_requests: int = 0
    lever_successes: int = 0
    lever_failures: int = 0
    lever_jobs_found: int = 0

    indeed_requests: int = 0
    indeed_successes: int = 0
    indeed_failures: int = 0
    indeed_jobs_found: int = 0

    glassdoor_requests: int = 0
    glassdoor_successes: int = 0
    glassdoor_failures: int = 0
    glassdoor_jobs_found: int = 0
    
    gemini_attempts: int = 0
    gemini_successes: int = 0
    gemini_failures: int = 0
    
    candidates_found: int = 0
    jobs_evaluated: int = 0
    jobs_passed: int = 0
    jobs_rejected: int = 0
    pending_evaluations: int = 0
    fallback_evaluations: int = 0
    cached_evaluations: int = 0
    
    email_attempts: int = 0
    email_success: bool = False
    
    final_status: str = "UNKNOWN"

def fetch_linkedin_jobs(keywords, health_metrics, location="Israel", max_pages=1):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin"
    }
    jobs = []
    for kw in dict.fromkeys(keywords):
        for page in range(max_pages):
            start = page * 25
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location={requests.utils.quote(location)}&start={start}"
            
            health_metrics.linkedin_requests += 1
            
            for attempt in range(3):
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        cards = soup.find_all("li")
                        if not soup.select("a.base-card__full-link"):
                            if res.text.strip() and not soup.select(".jobs-search-no-results-banner"):
                                health_metrics.linkedin_failures += 1
                                print("[SOURCE] LinkedIn unexpected extraction structure", flush=True)
                            else:
                                health_metrics.linkedin_successes += 1
                            break
                        for card in cards:
                            link_tag = card.find("a", class_="base-card__full-link")
                            title_tag = card.find("h3", class_="base-search-card__title")
                            comp_tag = card.find("h4", class_="base-search-card__subtitle")
                            snippet_tag = card.find("p", class_="base-search-card__snippet")
                            
                            if link_tag and title_tag:
                                link = link_tag.get("href", "").split("?")[0]
                                title = title_tag.get_text(strip=True)
                                company = comp_tag.get_text(strip=True) if comp_tag else "חברה"
                                snippet = snippet_tag.get_text(strip=True) if snippet_tag else title

                                img_tag = card.find("img")
                                logo = ""
                                if img_tag:
                                    delayed = img_tag.get("data-delayed-url") or ""
                                    src = img_tag.get("src") or ""
                                    ghost = img_tag.get("data-ghost-url") or ""
                                    if delayed and delayed != ghost and not delayed.startswith("data:"):
                                        logo = delayed
                                    elif src and src != ghost and not src.startswith("data:"):
                                        logo = src

                                jobs.append({
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "snippet": snippet,
                                    "logo": logo,
                                    "company_logo_url": logo or None,
                                    "query": kw,
                                    "source": "LinkedIn"
                                })
                        health_metrics.linkedin_successes += 1
                        break
                    elif res.status_code == 429:
                        print(f"[SOURCE] LinkedIn 429 Rate Limit on {kw}, page {page}. Backing off.")
                        delay = _retry_delay(res, attempt)
                        if delay > 30:
                            health_metrics.linkedin_failures += 1
                            break
                        if attempt < 2:
                            time.sleep(delay)
                    elif res.status_code in {401, 403}:
                        health_metrics.linkedin_failures += 1
                        break
                    else:
                        print(f"[SOURCE] LinkedIn returned {res.status_code} for {kw}. Attempt {attempt+1}")
                        time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"[ERROR] LinkedIn connection error: {type(e).__name__}. Attempt {attempt+1}")
                    time.sleep(2 ** attempt)
            else:
                health_metrics.linkedin_failures += 1
            time.sleep(1 + random.uniform(0.5, 1.5))
            
    health_metrics.linkedin_jobs_found += len(jobs)
    return jobs



def fetch_linkedin_full_job_description(link: str) -> str:
    """Attempt to extract full job description from LinkedIn guest API endpoint."""
    if not _source_url(link, "linkedin.com"):
        return ""
    try:
        # Extract numeric job ID from the end of the link
        match = re.search(r"/(\d+)$", urlsplit(canonical_job_url(link)).path)
        if not match:
            match = re.search(r"/(\d+)(?:\?|$)", link)
        if not match:
            return ""
        job_id = match.group(1)
        api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        res = _get_with_retries(requests, api_url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            desc_div = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="description__text")
            if desc_div:
                clean_text = desc_div.get_text(separator="\n", strip=True)
                if len(clean_text) > 100:
                    return clean_text
    except Exception as e:
        print(f"[DESCRIPTION] LinkedIn unavailable: {type(e).__name__}", flush=True)
    return ""


def fetch_drushim_jobs(keywords, health_metrics, max_pages=1):
    """Fetch broad engineering, energy, and operations job postings from Drushim (drushim.co.il)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    jobs = []
    seen_links = set()

    for kw in dict.fromkeys(keywords):
        for page in range(max_pages):
            if page == 0:
                url = f"https://www.drushim.co.il/jobs/search/{requests.utils.quote(kw)}/"
            else:
                url = f"https://www.drushim.co.il/jobs/search/{requests.utils.quote(kw)}/?page={page + 1}"

            health_metrics.drushim_requests += 1

            for attempt in range(3):
                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        articles = soup.find_all("article", attrs={"data-nagish": "job-card-item"})
                        if not articles:
                            health_metrics.drushim_failures += 1
                            print("[SOURCE] Drushim no recognized job cards; extraction unverified", flush=True)
                            break
                        for art in articles:
                            link_tag = art.find("a", href=lambda h: h and "/job/" in h)
                            if not link_tag:
                                continue
                            href = link_tag.get("href", "")
                            link = f"https://www.drushim.co.il{href}" if href.startswith("/") else href
                            if link in seen_links:
                                continue
                            seen_links.add(link)

                            # Title extraction
                            title = ""
                            save_btn = art.find("button", attrs={"data-nagish": "job-card-save-button"})
                            if save_btn and save_btn.get("aria-label"):
                                aria = save_btn.get("aria-label")
                                aria = re.sub(r"^שמור משרה\s*", "", aria)
                                aria = re.sub(r"\s*למועדפים$", "", aria).strip()
                                title = aria
                            if not title:
                                heading = art.find(["h2", "h3", "p"], class_=lambda c: c and ("title" in c.lower() or "name" in c.lower()))
                                if heading:
                                    title = heading.get_text(strip=True)
                            if not title:
                                title = link_tag.get_text(strip=True) or kw

                            # Company extraction
                            comp_tag = art.find(class_=lambda c: c and "company" in c.lower())
                            company = comp_tag.get_text(strip=True) if comp_tag else "חברה"
                            if not company or company == "- חסוי -":
                                company = "חברה מובילה (דיסקרטי)"

                            # Logo extraction
                            logo_tag = art.find("img", attrs={"data-nagish": "job-card-company-logo-image"}) or art.find("img")
                            logo = ""
                            if logo_tag:
                                l_src = logo_tag.get("src") or logo_tag.get("data-src") or ""
                                if l_src and not l_src.startswith("data:"):
                                    logo = l_src

                            # Snippet / Description: extract full context without UI buttons
                            clean_parts = [p for p in art.stripped_strings if p not in ["שיתוף", "פרטי המשרה", "שלח/י באתר החברה", "שלח קורות חיים", "הגש מועמדות"]]
                            snippet = " | ".join(clean_parts)[:1000]

                            jobs.append({
                                "title": title,
                                "company": company,
                                "link": link,
                                "snippet": snippet,
                                "logo": logo,
                                "company_logo_url": logo or None,
                                "query": kw,
                                "source": "Drushim"
                            })
                        health_metrics.drushim_successes += 1
                        break
                    elif res.status_code == 429:
                        print(f"[SOURCE] Drushim 429 Rate Limit on {kw}. Backing off.")
                        delay = _retry_delay(res, attempt)
                        if delay > 30:
                            health_metrics.drushim_failures += 1
                            break
                        if attempt < 2:
                            time.sleep(delay)
                    elif res.status_code in {401, 403}:
                        health_metrics.drushim_failures += 1
                        break
                    else:
                        print(f"[SOURCE] Drushim returned {res.status_code} for {kw}. Attempt {attempt+1}")
                        time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"[ERROR] Drushim connection error: {type(e).__name__}. Attempt {attempt+1}")
                    time.sleep(2 ** attempt)
            else:
                health_metrics.drushim_failures += 1
            time.sleep(1 + random.uniform(0.5, 1.5))

    health_metrics.drushim_jobs_found += len(jobs)
    return jobs


def fetch_drushim_full_job_description(link: str) -> str:
    """Attempt to extract full job description from Drushim job page."""
    if not _source_url(link, "drushim.co.il"):
        return ""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        res = _get_with_retries(requests, link, headers=headers, timeout=8, allow_redirects=False)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            main_desc = soup.find(class_=lambda c: c and ("job-details" in c.lower() or "job-description" in c.lower())) or soup.find("main") or soup.find("article")
            if main_desc:
                clean_text = main_desc.get_text(separator="\n", strip=True)
                if len(clean_text) > 100:
                    return clean_text
    except Exception as e:
        print(f"[DESCRIPTION] Drushim unavailable: {type(e).__name__}", flush=True)
    return ""


def fetch_comeet_jobs(company_slug="enlightenergy", company_uid="99.006", company_display_name="Enlight Renewable Energy", health_metrics=None, timeout=10, session=None):
    """
    Direct ATS connector for Comeet career portals (e.g. Enlight Renewable Energy).
    Extracts structured position metadata directly from official career portal payload.
    """
    import json
    if health_metrics is not None:
        health_metrics.comeet_requests += 1

    url = f"https://www.comeet.com/jobs/{company_slug}/{company_uid}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    client = session or requests
    try:
        res = _get_with_retries(client, url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            if health_metrics is not None:
                health_metrics.comeet_failures += 1
            print(f"[COMEET] Failed to fetch {url}: HTTP {res.status_code}", flush=True)
            return []

        positions = parse_comeet_positions(res.text)
        if positions is None:
            if health_metrics is not None:
                health_metrics.comeet_failures += 1
            print(f"[COMEET] Could not parse positions payload from {url}", flush=True)
            return []
        jobs = []
        for pos in positions:
            title = (pos.get("name") or "").strip()
            link = pos.get("url_active_page") or pos.get("url_comeet_hosted_page") or ""
            if not title or not safe_http_url(link):
                continue

            loc_obj = pos.get("location") or {}
            loc_parts = [loc_obj.get("city"), loc_obj.get("name") or loc_obj.get("country")]
            loc_str = ", ".join(p for p in loc_parts if p)

            # Combine details
            details_list = (pos.get("custom_fields") or {}).get("details", [])
            desc_parts = []
            for d in details_list:
                val = html_to_clean_text(d.get("value") or "")
                if val:
                    desc_parts.append(f"{d.get('name', 'Details')}: {val}")
            snippet = " | ".join(desc_parts) if desc_parts else title

            comeet_logo = "assets/logos/enlight.png" if "enlight" in company_slug.lower() else None
            jobs.append({
                "title": title,
                "company": company_display_name,
                "link": link,
                "location": loc_str,
                "snippet": snippet,
                "logo": comeet_logo,
                "company_logo_url": comeet_logo,
                "source": "Comeet",
                "source_id": pos.get("uid", ""),
                "description": snippet if desc_parts else "",
                "description_complete": bool(desc_parts),
                "is_direct_ats": True
            })

        if positions and not jobs:
            if health_metrics is not None:
                health_metrics.comeet_failures += 1
            print("[COMEET] Nonempty payload contained no valid positions", flush=True)
            return []
        if health_metrics is not None:
            health_metrics.comeet_successes += 1
            health_metrics.comeet_jobs_found += len(jobs)

        print(f"[COMEET] Successfully collected {len(jobs)} positions from {company_display_name}", flush=True)
        return jobs

    except Exception as e:
        if health_metrics is not None:
            health_metrics.comeet_failures += 1
        print(f"[COMEET_ERROR] Error fetching from {url}: {type(e).__name__}", flush=True)
        return []


class CircuitBreaker:
    """Per-source circuit breaker opening after consecutive failures."""

    def __init__(self, threshold: int = 3):
        self.threshold = max(1, int(threshold))
        self._failures: dict = {}
        self._opened: set = set()

    def is_open(self, source: str) -> bool:
        return source in self._opened

    def record_success(self, source: str) -> None:
        self._failures[source] = 0
        self._opened.discard(source)

    def record_failure(self, source: str) -> bool:
        count = self._failures.get(source, 0) + 1
        self._failures[source] = count
        if count >= self.threshold and source not in self._opened:
            self._opened.add(source)
            print(f"[CIRCUIT OPEN] {source}", flush=True)
            return True
        return False


def fetch_greenhouse_jobs(
    company_slug: str,
    company_display_name: str = "",
    health_metrics: RunHealth = None,
    timeout: int = 10,
    session=None,
) -> list:
    """Direct ATS connector for Greenhouse boards API."""
    if health_metrics is not None:
        health_metrics.greenhouse_requests += 1

    display_name = (company_display_name or company_slug).strip()
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    client = session or requests
    try:
        res = _get_with_retries(client, url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            if health_metrics is not None:
                health_metrics.greenhouse_failures += 1
            print(f"[GREENHOUSE] Failed to fetch {url}: HTTP {res.status_code}", flush=True)
            return []

        payload = res.json()
        raw_jobs = payload.get("jobs") if isinstance(payload, dict) else None
        if not isinstance(raw_jobs, list):
            if health_metrics is not None:
                health_metrics.greenhouse_failures += 1
            print(f"[GREENHOUSE] Unexpected payload structure from {url}", flush=True)
            return []

        jobs = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            title = (item.get("title") or "").strip()
            link = (item.get("absolute_url") or "").strip()
            if not title or not safe_http_url(link):
                continue

            loc_name = ((item.get("location") or {}).get("name") or "").strip()
            desc_text = html_to_clean_text(item.get("content") or "")
            updated_at = str(item.get("updated_at") or "")[:10]

            jobs.append({
                "title": title,
                "company": (item.get("company_name") or display_name).strip(),
                "link": link,
                "location": loc_name,
                "date": updated_at,
                "snippet": desc_text or title,
                "logo": None,
                "company_logo_url": None,
                "source": "Greenhouse",
                "source_id": str(item.get("id") or ""),
                "description": desc_text,
                "description_complete": bool(desc_text),
                "is_direct_ats": True,
            })

        if health_metrics is not None:
            health_metrics.greenhouse_successes += 1
            health_metrics.greenhouse_jobs_found += len(jobs)
        print(f"[GREENHOUSE] Successfully collected {len(jobs)} positions from {display_name}", flush=True)
        return jobs

    except Exception as e:
        if health_metrics is not None:
            health_metrics.greenhouse_failures += 1
        print(f"[GREENHOUSE_ERROR] Error fetching from {url}: {type(e).__name__}", flush=True)
        return []


def fetch_lever_jobs(
    company_slug: str,
    company_display_name: str = "",
    health_metrics: RunHealth = None,
    timeout: int = 10,
    session=None,
) -> list:
    """Direct ATS connector for Lever postings API."""
    if health_metrics is not None:
        health_metrics.lever_requests += 1

    display_name = (company_display_name or company_slug).strip()
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    client = session or requests
    try:
        res = _get_with_retries(client, url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            if health_metrics is not None:
                health_metrics.lever_failures += 1
            print(f"[LEVER] Failed to fetch {url}: HTTP {res.status_code}", flush=True)
            return []

        raw_jobs = res.json()
        if not isinstance(raw_jobs, list):
            if health_metrics is not None:
                health_metrics.lever_failures += 1
            print(f"[LEVER] Unexpected payload structure from {url}", flush=True)
            return []

        jobs = []
        for item in raw_jobs:
            if not isinstance(item, dict):
                continue
            title = (item.get("text") or "").strip()
            link = (item.get("hostedUrl") or "").strip()
            if not title or not safe_http_url(link):
                continue

            cats = item.get("categories") or {}
            loc_name = (cats.get("location") or "").strip()
            desc_text = format_lever_description(item)

            jobs.append({
                "title": title,
                "company": display_name,
                "link": link,
                "location": loc_name,
                "snippet": desc_text or title,
                "logo": None,
                "company_logo_url": None,
                "source": "Lever",
                "source_id": str(item.get("id") or ""),
                "description": desc_text,
                "description_complete": bool(desc_text),
                "is_direct_ats": True,
            })

        if health_metrics is not None:
            health_metrics.lever_successes += 1
            health_metrics.lever_jobs_found += len(jobs)
        print(f"[LEVER] Successfully collected {len(jobs)} positions from {display_name}", flush=True)
        return jobs

    except Exception as e:
        if health_metrics is not None:
            health_metrics.lever_failures += 1
        print(f"[LEVER_ERROR] Error fetching from {url}: {type(e).__name__}", flush=True)
        return []


def fetch_indeed_jobs(keywords, health_metrics, location="Israel", max_pages=1, session=None):
    """Decommissioned: Indeed scraper removed due to persistent anti-bot gating."""
    return []


def fetch_glassdoor_jobs(keywords, health_metrics, location="Israel", max_pages=1, session=None):
    """Decommissioned: Glassdoor scraper removed due to persistent anti-bot gating."""
    return []


class JobFetcher:
    """Base interface for all scrapers and ATS connectors."""
    source_name: str = "generic"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        raise NotImplementedError


class LinkedInFetcher(JobFetcher):
    source_name = "LinkedIn"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        location = kwargs.get("location", "Israel")
        max_pages = kwargs.get("max_pages", 1)
        return fetch_linkedin_jobs(keywords, health_metrics, location=location, max_pages=max_pages)


class DrushimFetcher(JobFetcher):
    source_name = "Drushim"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        max_pages = kwargs.get("max_pages", 1)
        return fetch_drushim_jobs(keywords, health_metrics, max_pages=max_pages)


class ComeetFetcher(JobFetcher):
    source_name = "Comeet"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        company_name = kwargs.get("company_name", "enlightenergy")
        company_uid = kwargs.get("company_uid", "99.006")
        display_name = kwargs.get("company_display_name", "Enlight Renewable Energy")
        return fetch_comeet_jobs(company_name, company_uid, display_name, health_metrics)


class GreenhouseFetcher(JobFetcher):
    source_name = "Greenhouse"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        company_slug = kwargs.get("company_slug") or kwargs.get("company_name", "")
        display_name = kwargs.get("company_display_name", company_slug)
        return fetch_greenhouse_jobs(company_slug, display_name, health_metrics=health_metrics)


class LeverFetcher(JobFetcher):
    source_name = "Lever"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        company_slug = kwargs.get("company_slug") or kwargs.get("company_name", "")
        display_name = kwargs.get("company_display_name", company_slug)
        return fetch_lever_jobs(company_slug, display_name, health_metrics=health_metrics)


class IndeedFetcher(JobFetcher):
    source_name = "Indeed"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        location = kwargs.get("location", "Israel")
        max_pages = kwargs.get("max_pages", 1)
        session = kwargs.get("session")
        return fetch_indeed_jobs(keywords, health_metrics, location=location, max_pages=max_pages, session=session)


class GlassdoorFetcher(JobFetcher):
    source_name = "Glassdoor"

    def fetch(self, keywords, health_metrics: RunHealth, **kwargs) -> list:
        location = kwargs.get("location", "Israel")
        max_pages = kwargs.get("max_pages", 1)
        session = kwargs.get("session")
        return fetch_glassdoor_jobs(keywords, health_metrics, location=location, max_pages=max_pages, session=session)


FETCHERS = {
    "linkedin": LinkedInFetcher(),
    "drushim": DrushimFetcher(),
    "comeet": ComeetFetcher(),
    "greenhouse": GreenhouseFetcher(),
    "lever": LeverFetcher(),
}

