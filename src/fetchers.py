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

# Energy & Infrastructure ATS Companies
ENERGY_COMEET_COMPANIES = [
    {"company": "SolarEdge", "uid": "solaredge", "sector": "אנרגיה סולארית וחשמל"},
    {"company": "Enlight Energy", "uid": "enlight", "sector": "אנרגיה מתחדשת"},
    {"company": "Augury", "uid": "augury", "sector": "ניטור מכונות ו-IIoT"},
]

# Dedicated Pure Drone, UAV, Robotics & Counter-UAS Companies
DRONE_COMEET_COMPANIES = [
    {"company": "XTEND", "uid": "xtend", "sector": "רחפנים אוטונומיים וביטחון"},
    {"company": "SpearUAV", "uid": "spearuav", "sector": "רחפנים משוטטים ורובוטיקה"},
    {"company": "Airobotics", "uid": "airobotics", "sector": "רחפנים אוטונומיים"},
    {"company": "HighLander", "uid": "highlander", "sector": "ניהול תנועת רחפנים ו-UAS"},
    {"company": "D-Fend Solutions", "uid": "d-fend", "sector": "הגנת C-UAS מפני רחפנים"},
    {"company": "NextVision", "uid": "nextvision", "sector": "אלקטרו-אופטיקה ומטע\"דים לרחפנים"},
]

ENERGY_KEYWORDS = [
    "gas", "energy", "mechanical", "control", "scada", "operator", "electrician", 
    "technician", "מכונות", "הנדסאי", "גז", "אנרגיה", "חשמל", "בקרה", "מפעיל", "טכנאי", "שירות שטח", "field", "operation"
]

# Strict Drone / UAV Anchor Keywords
DRONE_ANCHOR_KEYWORDS = [
    "drone", "uav", "uas", "flight", "pilot", "operator", "avionics", "fpv", "evtol", 
    "multirotor", "payload", "gcs", "integration", "field test", "technician", "assembly",
    "רחפן", "רחפנים", "כטבמ", "כטב\"ם", "מטיס", "מפעיל", "אינטגרציה", "הרכבה", "ניסויי טיסה", "מטע\"ד", "חיווט"
]

# Negative Keywords to reject non-drone/unrelated jobs
DRONE_NEGATIVE_KEYWORDS = [
    "naval", "submarine", "tank", "artillery", "weapon sight", "accounting", "hr manager", "legal"
]

def fetch_comeet_positions(company_uid, company_name, default_sector):
    """Fetch open positions from Comeet API."""
    url = f"https://www.comeet.com/jobs-api/v1/companies/{company_uid}/positions?token=undefined"
    jobs = []
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data, list):
            for pos in data:
                title = pos.get("name", "")
                location_obj = pos.get("location", {})
                city = location_obj.get("city", "ישראל") if isinstance(location_obj, dict) else "ישראל"
                link = pos.get("url_active_page", "") or pos.get("url_comeet_hosted_page", "")
                details = pos.get("details", "") or pos.get("experience_level", "") or ""
                
                if link and title:
                    jobs.append({
                        "title": title,
                        "company": company_name,
                        "location": city,
                        "link": link,
                        "snippet": f"{company_name} - {title}. {details}"[:400],
                        "sector": default_sector
                    })
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        print(f"[ERROR] Comeet scraper failed for {company_name}: {e}")
        return {"status": "failed", "jobs": [], "error": str(e)}

def scrape_comeet_companies():
    """Extract and filter energy and drone ATS jobs."""
    all_jobs = []
    failures = 0
    successes = 0
    
    # Energy
    for comp in ENERGY_COMEET_COMPANIES:
        res = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        if res["status"] == "success":
            successes += 1
            for p in res["jobs"]:
                text = f"{p['title']} {p['snippet']}".lower()
                if any(kw in text for kw in ENERGY_KEYWORDS):
                    all_jobs.append(p)
        else:
            failures += 1
            
    # Drones
    for comp in DRONE_COMEET_COMPANIES:
        res = fetch_comeet_positions(comp["uid"], comp["company"], comp["sector"])
        if res["status"] == "success":
            successes += 1
            for p in res["jobs"]:
                text = f"{p['title']} {p['snippet']}".lower()
                if any(kw in text for kw in DRONE_ANCHOR_KEYWORDS):
                    if not any(neg in text for neg in DRONE_NEGATIVE_KEYWORDS):
                        all_jobs.append(p)
        else:
            failures += 1
            
    return {
        "jobs": all_jobs,
        "successes": successes,
        "failures": failures,
        "attempted": len(ENERGY_COMEET_COMPANIES) + len(DRONE_COMEET_COMPANIES)
    }
