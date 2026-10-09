import re
import time
import requests
import random
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class RunHealth:
    linkedin_requests: int = 0
    linkedin_successes: int = 0
    linkedin_failures: int = 0
    linkedin_jobs_found: int = 0
    
    gemini_attempts: int = 0
    gemini_successes: int = 0
    gemini_failures: int = 0
    
    candidates_found: int = 0
    jobs_evaluated: int = 0
    jobs_passed: int = 0
    
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
    for kw in keywords:
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
                                
                                jobs.append({
                                    "title": title,
                                    "company": company,
                                    "link": link,
                                    "snippet": snippet,
                                    "query": kw
                                })
                        health_metrics.linkedin_successes += 1
                        break
                    elif res.status_code == 429:
                        print(f"[SOURCE] LinkedIn 429 Rate Limit on {kw}, page {page}. Backing off.")
                        time.sleep((2 ** attempt) + random.uniform(1, 3))
                    else:
                        print(f"[SOURCE] LinkedIn returned {res.status_code} for {kw}. Attempt {attempt+1}")
                        time.sleep(2)
                except Exception as e:
                    print(f"[ERROR] LinkedIn connection error: {e}. Attempt {attempt+1}")
                    time.sleep(2)
            else:
                health_metrics.linkedin_failures += 1
            time.sleep(1 + random.uniform(0.5, 1.5))
            
    health_metrics.linkedin_jobs_found += len(jobs)
    return jobs



def fetch_linkedin_full_job_description(link: str) -> str:
    """Attempt to extract full job description from LinkedIn guest API endpoint."""
    if not link or "linkedin.com/jobs/view" not in link:
        return ""
    try:
        # Extract numeric job ID from the end of the link
        match = re.search(r"-(\d+)(?:\?|$)", link)
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
        res = requests.get(api_url, headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            desc_div = soup.find("div", class_="show-more-less-html__markup") or soup.find("div", class_="description__text")
            if desc_div:
                clean_text = desc_div.get_text(separator="\n", strip=True)
                if len(clean_text) > 100:
                    return clean_text[:2000]
    except Exception as e:
        pass
    return ""



