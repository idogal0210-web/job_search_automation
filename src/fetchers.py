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
    
    comeet_companies_attempted: int = 0
    comeet_companies_successful: int = 0
    comeet_companies_failed: int = 0
    comeet_jobs_found: int = 0

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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
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



def extract_comeet_credentials(company_name):
    """Attempt to find Comeet UID and Token from the company's careers page."""
    # This is a placeholder for future dynamic extraction. 
    # For now, we will rely on a known mapping or just return None.
    # In a full implementation, you could fetch 'https://company.com/careers' and regex for the token.
    known_tokens = {
        "percepto": {"uid": "44.000", "token": "440154015404400088019802640880"},
        # Add more known tokens here as they are discovered
    }
    return known_tokens.get(company_name.lower())

def scrape_comeet_companies(companies, health_metrics):
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    
    for company in companies:
        health_metrics.comeet_companies_attempted += 1
        creds = extract_comeet_credentials(company)
        
        if not creds:
            print(f"[SOURCE] Comeet credentials for {company} not in known list. Skipping.")
            health_metrics.comeet_companies_failed += 1
            continue
            
        uid = creds["uid"]
        token = creds["token"]
        url = f"https://www.comeet.co/careers-api/2.0/company/{uid}/positions?token={token}&details=true"
        
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                positions = res.json()
                for p in positions:
                    # Filter for relevant positions (e.g., mechanical, technician, energy, drone)
                    # We will grab all and let the AI evaluator filter them, or pre-filter here.
                    title = p.get("name", "")
                    # Pre-filter to avoid spamming the AI with irrelevant jobs (like HR, Finance)
                    lower_title = title.lower()
                    if any(kw in lower_title for kw in ["finance", "hr", "sales", "marketing", "legal", "account"]):
                        continue
                        
                    jobs.append({
                        "title": title,
                        "company": company.capitalize(),
                        "link": p.get("url_active_page", ""),
                        "snippet": p.get("description", "No description available")[:200], # truncated for token limit
                        "query": f"Comeet - {company}"
                    })
                health_metrics.comeet_companies_successful += 1
                print(f"[SOURCE] Fetched {len(positions)} jobs from Comeet ({company}).")
            else:
                print(f"[SOURCE] Comeet returned {res.status_code} for {company}.")
                health_metrics.comeet_companies_failed += 1
        except Exception as e:
            print(f"[ERROR] Comeet connection error for {company}: {e}")
            health_metrics.comeet_companies_failed += 1
            
        time.sleep(2)
        
    health_metrics.comeet_jobs_found += len(jobs)
    return jobs
