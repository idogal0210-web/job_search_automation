import json
import re
import time
import requests
import random
from bs4 import BeautifulSoup
from dataclasses import dataclass
from urllib.parse import urlsplit
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

        match = re.search(r'COMPANY_POSITIONS_DATA\s*=\s*(\[.*?\]);\s*(?:COMPANY|POSITION|\n|</script>)', res.text, re.DOTALL)
        if not match:
            if health_metrics is not None:
                health_metrics.comeet_failures += 1
            print(f"[COMEET] Could not parse positions payload from {url}", flush=True)
            return []

        positions = json.loads(match.group(1))
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
                raw_val = d.get("value") or ""
                val = re.sub(r"<[^>]+>", " ", raw_val)
                val = re.sub(r"\s+", " ", val).strip()
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


def fetch_indeed_jobs(keywords, health_metrics, location="Israel", max_pages=1, session=None):
    """Fetch energy, SCADA, gas, solar, and industrial operations jobs from Indeed (il.indeed.com)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    jobs = []
    seen_links = set()

    for kw in dict.fromkeys(keywords):
        for page in range(max_pages):
            start = page * 10
            url = f"https://il.indeed.com/jobs?q={requests.utils.quote(kw)}&l={requests.utils.quote(location)}&start={start}"
            health_metrics.indeed_requests += 1

            for attempt in range(3):
                try:
                    if session is not None:
                        res = session.get(url, headers=headers, timeout=15)
                    elif cffi_requests is not None:
                        res = cffi_requests.get(url, headers=headers, impersonate="safari17_0", timeout=15)
                    else:
                        res = requests.get(url, headers=headers, timeout=15)

                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        parsed_jobs = []

                        # Extraction strategy 1: Structured JSON in mosaic provider script
                        target = 'window.mosaic.providerData["mosaic-provider-jobcards"]='
                        if target in res.text:
                            try:
                                s_idx = res.text.find(target) + len(target)
                                e_idx = res.text.find(";\n", s_idx)
                                if e_idx == -1:
                                    e_idx = res.text.find(";", s_idx)
                                json_data = json.loads(res.text[s_idx:e_idx].strip())
                                model = json_data.get("metaData", {}).get("mosaicProviderJobCardsModel", {})
                                for item in model.get("results", []):
                                    jk = item.get("jobkey")
                                    title = item.get("title")
                                    if not title or not jk:
                                        continue
                                    link = f"https://il.indeed.com/viewjob?jk={jk}"
                                    if link in seen_links:
                                        continue
                                    seen_links.add(link)

                                    company = item.get("company") or "חברה"
                                    loc = item.get("formattedLocation") or location
                                    raw_snippet = item.get("snippet") or ""
                                    snippet = BeautifulSoup(raw_snippet, "html.parser").get_text(separator=" ", strip=True) if raw_snippet else title

                                    parsed_jobs.append({
                                        "title": title,
                                        "company": company,
                                        "link": link,
                                        "snippet": snippet,
                                        "location": loc,
                                        "logo": "",
                                        "company_logo_url": None,
                                        "query": kw,
                                        "source": "Indeed",
                                    })
                            except Exception as json_err:
                                print(f"[SOURCE] Indeed JSON parse error: {json_err}", flush=True)

                        # Extraction strategy 2: HTML DOM fallback
                        if not parsed_jobs:
                            cards = soup.select(".job_seen_beacon") or soup.select("div[data-jk]")
                            for card in cards:
                                jk = card.get("data-jk")
                                title_el = card.select_one("h2.jobTitle span") or card.select_one("a[data-jk]") or card.select_one("h2.jobTitle")
                                title = title_el.get_text(strip=True) if title_el else ""
                                link_el = card.select_one("a[data-jk]") or card.select_one("h2.jobTitle a")
                                if not jk and link_el and link_el.get("data-jk"):
                                    jk = link_el.get("data-jk")
                                link = f"https://il.indeed.com/viewjob?jk={jk}" if jk else ""
                                if not link and link_el and link_el.get("href"):
                                    href = link_el.get("href")
                                    link = f"https://il.indeed.com{href}" if href.startswith("/") else href

                                if not title or not link or link in seen_links:
                                    continue
                                seen_links.add(link)

                                comp_el = card.select_one('[data-testid="company-name"]') or card.select_one(".companyName")
                                company = comp_el.get_text(strip=True) if comp_el else "חברה"
                                loc_el = card.select_one('[data-testid="text-location"]') or card.select_one(".companyLocation")
                                loc = loc_el.get_text(strip=True) if loc_el else location
                                snip_el = card.select_one(".job-snippet") or card.select_one('[data-testid="jobs-snippet"]')
                                snippet = snip_el.get_text(strip=True) if snip_el else title

                                parsed_jobs.append({
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "snippet": snippet,
                                    "location": loc,
                                    "logo": "",
                                    "company_logo_url": None,
                                    "query": kw,
                                    "source": "Indeed",
                                })

                        if not parsed_jobs and not soup.select(".jobsearch-NoResult"):
                            health_metrics.indeed_failures += 1
                            print("[SOURCE] Indeed no recognized job cards; extraction unverified", flush=True)
                            break

                        jobs.extend(parsed_jobs)
                        health_metrics.indeed_successes += 1
                        break
                    elif res.status_code == 429:
                        print(f"[SOURCE] Indeed 429 Rate Limit on {kw}, page {page}. Backing off.")
                        delay = _retry_delay(res, attempt)
                        if delay > 30:
                            health_metrics.indeed_failures += 1
                            break
                        if attempt < 2:
                            time.sleep(delay)
                    elif res.status_code in {401, 403}:
                        health_metrics.indeed_failures += 1
                        break
                    else:
                        print(f"[SOURCE] Indeed returned {res.status_code} for {kw}. Attempt {attempt+1}")
                        time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"[ERROR] Indeed connection error: {type(e).__name__}. Attempt {attempt+1}")
                    time.sleep(2 ** attempt)
            else:
                health_metrics.indeed_failures += 1
            time.sleep(1 + random.uniform(0.5, 1.5))

    health_metrics.indeed_jobs_found += len(jobs)
    return jobs


def fetch_glassdoor_jobs(keywords, health_metrics, location="Israel", max_pages=1, session=None):
    """Fetch energy, SCADA, solar, and industrial operations jobs from Glassdoor (glassdoor.com)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    jobs = []
    seen_links = set()

    for kw in dict.fromkeys(keywords):
        for page in range(max_pages):
            page_param = f"&p={page + 1}" if page > 0 else ""
            url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={requests.utils.quote(kw)}&locT=N&locId=119{page_param}"
            health_metrics.glassdoor_requests += 1

            for attempt in range(3):
                try:
                    if session is not None:
                        res = session.get(url, headers=headers, timeout=15)
                    else:
                        res = requests.get(url, headers=headers, timeout=15)

                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        cards = soup.select('li[data-test="jobListing"]')
                        parsed_jobs = []

                        for card in cards:
                            title_el = card.select_one('a[data-test="job-title"]') or card.find("a", href=lambda h: h and ("/job-listing/" in h or "/partner/jobListing" in h))
                            if not title_el:
                                continue
                            link = title_el.get("href", "")
                            if link.startswith("/"):
                                link = f"https://www.glassdoor.com{link}"
                            link = link.split("?")[0] if link else ""
                            if not link or link in seen_links:
                                continue
                            seen_links.add(link)

                            title = title_el.get_text(strip=True)
                            comp_el = (
                                card.select_one('span[class*="compactEmployerName"]')
                                or card.select_one('[data-test="employer-name"]')
                                or card.select_one('div[class*="employerNameContainer"]')
                            )
                            company = comp_el.get_text(strip=True) if comp_el else "חברה"
                            company = re.sub(r"\d\.\d$", "", company).strip() or company

                            loc_el = card.select_one('[data-test="emp-location"]')
                            loc = loc_el.get_text(strip=True) if loc_el else location

                            snip_el = card.select_one('[data-test="descSnippet"]')
                            snippet = snip_el.get_text(separator=" ", strip=True) if snip_el else title

                            img_el = card.find("img")
                            logo = img_el.get("src", "") if img_el else ""

                            parsed_jobs.append({
                                "title": title,
                                "company": company,
                                "link": link,
                                "snippet": snippet,
                                "location": loc,
                                "logo": logo,
                                "company_logo_url": logo or None,
                                "query": kw,
                                "source": "Glassdoor",
                            })

                        if not parsed_jobs and not soup.select(".no-results"):
                            health_metrics.glassdoor_failures += 1
                            print("[SOURCE] Glassdoor no recognized job cards; extraction unverified", flush=True)
                            break

                        jobs.extend(parsed_jobs)
                        health_metrics.glassdoor_successes += 1
                        break
                    elif res.status_code == 429:
                        print(f"[SOURCE] Glassdoor 429 Rate Limit on {kw}, page {page}. Backing off.")
                        delay = _retry_delay(res, attempt)
                        if delay > 30:
                            health_metrics.glassdoor_failures += 1
                            break
                        if attempt < 2:
                            time.sleep(delay)
                    elif res.status_code in {401, 403}:
                        health_metrics.glassdoor_failures += 1
                        break
                    else:
                        print(f"[SOURCE] Glassdoor returned {res.status_code} for {kw}. Attempt {attempt+1}")
                        time.sleep(2 ** attempt)
                except Exception as e:
                    print(f"[ERROR] Glassdoor connection error: {type(e).__name__}. Attempt {attempt+1}")
                    time.sleep(2 ** attempt)
            else:
                health_metrics.glassdoor_failures += 1
            time.sleep(1 + random.uniform(0.5, 1.5))

    health_metrics.glassdoor_jobs_found += len(jobs)
    return jobs


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
    "indeed": IndeedFetcher(),
    "glassdoor": GlassdoorFetcher(),
}

