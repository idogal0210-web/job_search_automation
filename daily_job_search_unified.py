import os
import sys
import json
import smtplib
import time
import requests
import random
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from src.ats_scraper import scrape_all_comeet_jobs
from src.interactive_app_builder import build_and_save_docs_app

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

    def print_summary(self):
        print("\n[HEALTH] === Run Health Summary ===")
        print(f"[HEALTH] LinkedIn: {self.linkedin_jobs_found} jobs found | {self.linkedin_successes}/{self.linkedin_requests} successful reqs ({self.linkedin_failures} failed)")
        print(f"[HEALTH] Comeet: {self.comeet_jobs_found} jobs found | {self.comeet_companies_successful}/{self.comeet_companies_attempted} successful companies ({self.comeet_companies_failed} failed)")
        print(f"[HEALTH] Gemini: {self.gemini_successes}/{self.gemini_attempts} evaluations succeeded ({self.gemini_failures} failed)")
        print(f"[HEALTH] Funnel: {self.candidates_found} unique candidates -> {self.jobs_evaluated} evaluated -> {self.jobs_passed} passed thresholds")
        print(f"[HEALTH] Email: Attempts={self.email_attempts}, Success={self.email_success}")
        print(f"[HEALTH] Final Status: {self.final_status}")
        print("[HEALTH] ==============================\n")


DATA_DIR = os.path.join(BASE_DIR, "data")
SEEN_JOBS_FILE = os.path.join(DATA_DIR, "seen_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "seen_jobs.json")
SEEN_DRONES_FILE = os.path.join(DATA_DIR, "seen_drones.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "seen_drones.json")
WEEKLY_ARCHIVE_FILE = os.path.join(DATA_DIR, "weekly_archive.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "weekly_archive.json")
REJECTED_JOBS_FILE = os.path.join(DATA_DIR, "rejected_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "rejected_jobs.json")
RETENTION_DAYS = 14

def check_already_ran_today():
    if "--force" in sys.argv or not os.environ.get("GITHUB_ACTIONS"):
        return False
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        return False

    token = os.environ.get("GITHUB_TOKEN")
    repo = "idogal0210-web/job_search_automation"
    workflow_id = "daily_job_search.yml"
    
    if not token:
        return False
        
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_id}/runs?status=success&per_page=10"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            runs = res.json().get("workflow_runs", [])
            today_utc = datetime.utcnow().date()
            for run in runs:
                if run.get("event") == "schedule":
                    run_time_str = run.get("created_at")
                    if run_time_str:
                        run_date = datetime.strptime(run_time_str, "%Y-%m-%dT%H:%M:%SZ").date()
                        if run_date == today_utc:
                            print(f"[INIT] Workflow already succeeded today on schedule ({run_date}). Skipping duplicate email dispatch.")
                            return True
    except Exception as e:
        print(f"[ERROR] Idempotency check warning: {e}")
    return False

def load_seen_dict(file_path):
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        fresh = {}
        for link, ts_str in data.items():
            try:
                if datetime.fromisoformat(ts_str) > cutoff:
                    fresh[link] = ts_str
            except Exception:
                pass
        return fresh
    except Exception:
        return {}

def load_rejected_job_links():
    rejected_set = set()
    if os.path.exists(REJECTED_JOBS_FILE):
        try:
            with open(REJECTED_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                rejected_set = set(data if isinstance(data, list) else data.keys())
        except Exception:
            rejected_set = set()

    try:
        fb_url = "https://job-finder-auto-default-rtdb.firebaseio.com/triage.json"
        res = requests.get(fb_url, timeout=5)
        if res.status_code == 200:
            cloud_data = res.json()
            if cloud_data and isinstance(cloud_data, dict):
                cloud_rejected = cloud_data.get("rejected", [])
                if isinstance(cloud_rejected, list):
                    for l in cloud_rejected:
                        if l:
                            rejected_set.add(l)
                    with open(REJECTED_JOBS_FILE, "w", encoding="utf-8") as f:
                        json.dump(sorted(list(rejected_set)), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Cloud sync warning (load_rejected_job_links): {e}")

    return rejected_set

def save_seen_dict(file_path, seen_dict, new_links):
    now_iso = datetime.now().isoformat()
    for link in new_links:
        seen_dict[link] = now_iso
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(seen_dict, f, ensure_ascii=False, indent=2)

def update_weekly_archive(new_jobs):
    archive = []
    if os.path.exists(WEEKLY_ARCHIVE_FILE):
        try:
            with open(WEEKLY_ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception:
            archive = []
            
    cutoff_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    archive = [j for j in archive if j.get("date", "") >= cutoff_date]
    
    rejected_set = load_rejected_job_links()
    archive = [j for j in archive if j.get("link") not in rejected_set]

    seen_links = {j.get("link") for j in archive}
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    if new_jobs:
        for job in new_jobs:
            link = job.get("link")
            if link and link not in seen_links and link not in rejected_set:
                seen_links.add(link)
                job_copy = dict(job)
                job_copy["date"] = today_str
                archive.append(job_copy)
            
    with open(WEEKLY_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    return archive

CV_CONTEXT = """
Name: Ido Gal (עידו גל)
Title: Gas Controller - Operations & Product (בקר גז - תפעול ומוצר) & Energy Systems | Practical Mechanical Engineer | Real-Time Control & Supply Continuity
Education: Practical Mechanical Engineer, Natural Gas & Green Energy (הנדסאי מכונות, התמחות בגז טבעי ובאנרגיה ירוקה), Ruppin Academic Center (2024). Certified Electrician Studies (2026 - לקראת סיום הלימודים, חודשיים). NOT a B.Sc. Engineer!
Skills: Real-time 24/7 SCADA & gas control, pressure/flow monitoring, nomination allocations, Excel, SAP, Python, Gemini/Copilot AI automation, Nahal Reconnaissance demolitions/combat engineering (סיירת נח"ל).
"""

NON_TECHNICAL_TITLES = [
    "שיווק", "מנהל מותג", "מנהלת מותג", "משאבי אנוש", "רכזת גיוס", "רכז גיוס", "גיוס עובדים",
    "הנהלת חשבונות", "מנהל חשבונות", "מנהלת חשבונות", "רואה חשבון", "רואת חשבון", "חשב שכר", "חשבת שכר",
    "יועץ משפטי", "יועצת משפטית", "עורך דין", "עורכת דין", "משפטי", "סיעוד", "אח מוסמך", "אחות מוסמכת",
    "רופא", "רופאה", "רוקח", "רוקחת", "מכירות טלפוניות", "טלמרקטינג", "נציג שירות", "נציגת שירות",
    "נציג מכירות", "נציגת מכירות", "מוקד", "קופאי", "קופאית", "מלצר", "מלצרית", "מזכיר", "מזכירה",
    "מנהל משרד", "מנהלת משרד", "קוסמטיקה", "טיפוח", "ביוטי", "רכש", "קניין", "קניינית",
    "ניקיון", "עובד ניקיון", "עובדת ניקיון", "בוחן חיובים", "בוחנת חיובים", "מנתח מערכות data",
    "brand manager", "marketing", "digital marketing", "social media", "seo", "human resources",
    "talent acquisition", "recruiter", "sourcer", "accountant", "bookkeeper", "payroll",
    "finance manager", "cfo", "legal counsel", "attorney", "lawyer", "compliance officer",
    "nurse", "nursing", "physician", "pharmacist", "sales representative", "telemarketing",
    "customer service", "customer support", "cashier", "receptionist", "office manager", "cosmetics", "beauty",
    "user acquisition", "procurement", "buyer", "cleaner", "tax preparer", "service desk",
    "bi analyst", "data analyst", "full stack", "web developer", "frontend", "backend", "software developer",
    "copywriter", "content writer", "salesperson", "sales manager", "product designer", "country club", "crm dynamics",
    "collections", "salesforce", "account manager", "brand marketing", "vp of sales", "sales"
]

def evaluate_and_enrich_job_with_gemini(client, title, company, snippet, is_drone, health_metrics):
    title_lower = title.lower()
    company_lower = company.lower()
    
    # Deterministic Pre-Filters
    for bl in ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון"]:
        if bl in company_lower:
            print(f"[FILTER] Disqualifying Blacklist: {company} - {title}")
            return None

    for non_tech in NON_TECHNICAL_TITLES:
        if non_tech in title_lower:
            print(f"[FILTER] Disqualifying non-technical role: {company} - {title} ('{non_tech}')")
            return None

    prompt = f"""
    You are an expert AI Technical Career Coach evaluating a job opportunity for Ido Gal.

    Candidate Profile (Source of Truth):
    {CV_CONTEXT}

    Target Job Details:
    - Title: {title}
    - Company: {company}
    - Snippet/Description: {snippet}
    - Is Drone/Defense domain: {is_drone}

    Evaluation & Screening Rules:
    1. B.Sc. REQUIREMENT & FLEXIBILITY:
       - Ido is a certified Practical Mechanical Engineer (הנדסאי מכונות), NOT a B.Sc. engineer.
       - ONLY allow B.Sc.-titled jobs if you identify genuine flexibility, practical openness, or if the company is known to accept experienced practical engineers (הנדסאים).
    2. DOMAIN PREFERENCES:
       - Energy: Give a strong preference / bonus to Solar PV, Energy Storage (BESS), Energy Tech and Natural Gas opportunities.
    3. MATCH SCORING (0-100):
       - Score objectively based on Ido's genuine background.

    Return STRICT JSON with keys:
    1. "match_score": integer (0 to 100).
    2. "concrete_matches_count": integer (0 to 10).
    3. "reasoning": 1-2 sentence Hebrew justification.
    4. "sector_key": one of ["energy", "drones", "cuas", "avionics", "other"].
    5. "sector": Hebrew sector title e.g. "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA" or "🚁 רחפנים וכטב״ם אוטונומי".
    6. "location": Hebrew location in 2-4 words.
    7. "company_domain_product": 10-15 words Hebrew concise summary strictly describing the company's core domain and product.
    8. "job_summary": 2-3 sentence Hebrew concise summary of core job duties and responsibilities.
    9. "experience_strengths": 1-2 sentence Hebrew tailored strengths mapping.
    10. "key_highlights": 1-2 sentence Hebrew highlights.
    11. "company_size": string.
    12. "junior_openness": string.
    13. "work_model": string.
    """
    
    time.sleep(1.5)
    
    health_metrics.gemini_attempts += 1
    
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash"
    ]
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)
            
            # Validation
            req_keys = ["match_score", "concrete_matches_count", "reasoning", "sector_key"]
            if not all(k in data for k in req_keys):
                print(f"[VALIDATION] Missing keys in Gemini response from {model_name}")
                continue
                
            if not isinstance(data.get("match_score"), int) or not isinstance(data.get("concrete_matches_count"), int):
                print(f"[VALIDATION] Type error in Gemini response from {model_name}")
                continue
                
            health_metrics.gemini_successes += 1
            
            # Post-Gemini Python Deterministic Enforcement
            if data["concrete_matches_count"] < 3:
                print(f"[VALIDATION] Job disqualified (concrete matches < 3): {company} - {title}")
                return None
                
            return data
            
        except Exception as e:
            print(f"[GEMINI] Failure with {model_name}: {e}")
            continue

    print(f"[ERROR] All Gemini models failed for {company} - {title}.")
    health_metrics.gemini_failures += 1
    return None

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

def build_unified_html_email(jobs, top_3, dashboard_url):
    now_str = datetime.now().strftime("%d.%m.%Y")
    
    if not jobs:
        return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<body style="font-family: Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 20px; direction: rtl; text-align: center;">
    <h1 style="color: #38bdf8;">🎯 דוח משרות יומי - {now_str}</h1>
    <p>הסריקה עברה בהצלחה, אך לא נמצאו משרות רלוונטיות היום שעוברות את רף הציון הנדרש.</p>
    <p>נמשיך לסרוק מחר!</p>
</body>
</html>
"""

    sectors = {
        "energy": {"title": "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA", "jobs": []},
        "drones": {"title": '🚁 רחפנים, כטב"ם אוטונומי ורובוטיקה', "jobs": []},
        "cuas": {"title": "🛡️ מערכות הגנת C-UAS וביטחון", "jobs": []},
        "avionics": {"title": '📡 מטע"דים, אלקטרו-אופטיקה ואוויוניקה', "jobs": []}
    }

    for j in jobs:
        sec_key = j.get("sector_key", "energy")
        if sec_key not in sectors:
            sec_key = "energy"
        sectors[sec_key]["jobs"].append(j)

    top_3_html = ""
    if top_3:
        top_items = ""
        for idx, pick in enumerate(top_3, 1):
            comp_domain = pick.get('company_domain_product', pick.get('sector', ''))
            top_items += f"""
            <div style="background-color: #1e293b; padding: 14px 18px; margin-bottom: 10px; border-radius: 10px; border-right: 4px solid #f59e0b; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 800; color: #f8fafc; font-size: 15.5px;">{idx}. {pick.get('company')} – {pick.get('title')}</div>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
                        <span style="color: #34d399; font-weight: bold;">{pick.get('match_score')}% התאמה</span> • {comp_domain}
                    </div>
                </div>
                <div>
                    <a href="{pick.get('link')}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; padding: 6px 14px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: bold; display: inline-block;">הגש מועמדות ↗</a>
                </div>
            </div>
            """
        top_3_html = f"""
        <div style="background-color: #0f172a; border: 1px solid #f59e0b; border-radius: 14px; padding: 18px; margin-bottom: 26px; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.15);">
            <div style="font-size: 16px; font-weight: 800; color: #fbbf24; margin-bottom: 14px;">⭐ משרות הזהב המובילות (Top 3 Picks):</div>
            {top_items}
        </div>
        """

    sector_blocks_html = ""
    for sec_key, sec_data in sectors.items():
        sec_jobs = sec_data["jobs"]
        if not sec_jobs:
            continue
        
        cards_html = ""
        for idx, j in enumerate(sec_jobs, 1):
            comp_name = j.get('company', 'חברה')
            comp_domain = j.get('company_domain_product', j.get('company_summary', j.get('sector', '')))
            loc = j.get('location', 'ישראל')
            score = j.get('match_score', 0)
            
            card_title = f"{comp_name} - {j.get('title', '')}"
            job_sum = j.get('job_summary', j.get('company_summary', ''))
            strengths = j.get('experience_strengths', j.get('reasoning', ''))
            highlights = j.get('key_highlights', '')
            
            if sec_key in ['drones', 'cuas', 'avionics']:
                badge_html = '<span style="background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">🚁 רחפנים וכטב"ם אוטונומי</span>'
            else:
                badge_html = '<span style="background-color: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">⚡ תשתיות אנרגיה וגז טבעי</span>'

            boxes_html = ""
            if comp_domain and comp_domain.strip():
                boxes_html += f'<div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #38bdf8; font-weight: bold;">🏢 תחום ומוצר החברה:</span> {comp_domain}</div>'
            if job_sum and job_sum.strip():
                boxes_html += f'<div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #38bdf8; font-weight: bold;">📋 תקציר המשרה:</span> {job_sum}</div>'
            if strengths and strengths.strip():
                boxes_html += f'<div style="background-color: rgba(6, 78, 59, 0.2); border: 1px solid rgba(5, 150, 105, 0.35); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #e2e8f0;"><span style="color: #4ade80; font-weight: bold;">💪 נקודות חוזק מהניסיון שלך:</span> {strengths}</div>'
            if highlights and highlights.strip():
                boxes_html += f'<div style="background-color: rgba(120, 53, 15, 0.2); border: 1px solid rgba(217, 119, 6, 0.35); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #fbbf24; font-weight: bold;">🔍 דגשים / דרישות נוספות:</span> {highlights}</div>'

            cards_html += f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 20px; margin-bottom: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.35);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid #334155; padding-bottom: 12px; margin-bottom: 14px;">
                    <div>
                        {badge_html}
                        <h2 style="font-size: 17px; font-weight: bold; color: #ffffff; margin: 0; line-height: 1.4;">
                            {idx}. {card_title} <span style="font-size: 12.5px; font-weight: normal; color: #94a3b8; margin-right: 6px;">• {loc}</span>
                        </h2>
                    </div>
                    <div style="background-color: rgba(16, 185, 129, 0.15); color: #34d399; font-size: 12.5px; font-weight: 800; padding: 4px 12px; border-radius: 9999px; border: 1px solid rgba(16, 185, 129, 0.35); white-space: nowrap; margin-right: 12px;">
                        {score}% התאמה
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    {boxes_html}
                </div>
                <div style="border-top: 1px solid rgba(51, 65, 85, 0.6); padding-top: 14px; margin-top: 14px; text-align: left;">
                    <a href="{j.get('link')}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; padding: 9px 22px; text-decoration: none; border-radius: 8px; font-size: 12.5px; font-weight: bold; display: inline-block;">
                        הגש מועמדות למשרה ↗
                    </a>
                </div>
            </div>
            """
            
        sector_blocks_html += f"""
        <div style="margin-bottom: 28px;">
            <div style="font-size: 17.5px; font-weight: 800; color: #f8fafc; margin-bottom: 14px; border-bottom: 2px solid #0284c7; padding-bottom: 6px;">
                {sec_data['title']} ({len(sec_jobs)} משרות)
            </div>
            {cards_html}
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; background-color: #020617; color: #f8fafc; margin: 0; padding: 20px; direction: rtl;">
    <div style="max-width: 680px; margin: 0 auto; background-color: #0b1329; border-radius: 16px; padding: 24px; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; border-radius: 14px; padding: 24px; text-align: center; margin-bottom: 24px; border: 1px solid #334155;">
            <h1 style="margin: 0 0 6px 0; font-size: 22px; color: #38bdf8; font-weight: 800;">🎯 דוח משרות יומי מאוחד | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך סריקה: {now_str} | סה"כ משרות נבחרות: {len(jobs)}</div>
        </div>

        <div style="text-align: center; margin-bottom: 26px;">
            <a href="{dashboard_url}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; font-size: 14.5px; font-weight: bold; text-decoration: none; padding: 13px 28px; border-radius: 12px; display: inline-block;">
                🚀 פתח דוח אינטראקטיבי וניהול משרות (✔️ / ✖️) ↗
            </a>
        </div>

        {top_3_html}
        {sector_blocks_html}

        <div style="border-top: 1px solid #1e293b; padding-top: 16px; text-align: center; font-size: 12px; color: #64748b;">
            דוח זה הופק באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל.
        </div>
    </div>
</body>
</html>
"""
    return html

def run_unified_daily_search():
    print("[INIT] Starting Unified Daily Job Search Pipeline...")
    health = RunHealth()
    
    if check_already_ran_today():
        print("[INIT] Already ran successfully today. Exiting idempotently.")
        sys.exit(0)

    api_key = os.environ.get("GEMINI_API_KEY")
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_pwd = os.environ.get("SENDER_APP_PASSWORD")

    if not api_key:
        print("[ERROR] GEMINI_API_KEY missing. Fail fast.")
        sys.exit(1)
    if not sender_email or not sender_pwd:
        print("[ERROR] SENDER_EMAIL or SENDER_APP_PASSWORD missing. Fail fast.")
        sys.exit(1)

    genai_client = genai.Client(api_key=api_key, http_options={'timeout': 15000})

    seen_jobs = load_seen_dict(SEEN_JOBS_FILE)
    seen_drones = load_seen_dict(SEEN_DRONES_FILE)
    rejected_links = load_rejected_job_links()

    all_raw_jobs = []

    energy_keywords = [
        "הנדסאי מכונות", "בקר גז", "תפעול אנרגיה", "אנרגיה סולארית",
        "Field Service Engineer Israel", "Gas Controller Israel", "SCADA Operator Israel",
        "Control Room Operator Israel", "טכנאי חדר בקרה", "מפעיל תחנת כוח", "אגירת אנרגיה BESS",
        "Enlight Renewable Energy", "Energix Renewable Energies", "SolarEdge Israel",
        "Doral Energy", "Nofar Energy", "Shikun & Binui Energy", "EDF Renewables Israel",
        "Prime Energy Israel", "Brenmiller Energy", "Augwind Energy",
        "OPC Energy", "Dalia Energy", "Dorad Energy", "Edeltech", "Supergas Energy",
        "Ormat Technologies", "Paz Ashdod Refinery", "Bazan Energy", "Afcon Control", "Electra Power",
        "H2Pro", "Prisma Photonics", "Doral Energy-Tech Ventures", "GenCell Energy",
        "ZOOZ Power", "Chakratec", "Raycatch", "Phinergy", "mPrest"
    ]
    energy_jobs = fetch_linkedin_jobs(energy_keywords, health)
    for j in energy_jobs:
        j["is_drone"] = False
    all_raw_jobs.extend(energy_jobs)

    drone_keywords = [
        "XTEND Drones", "Spear UAV", "Rafael Drone", "Airobotics",
        "Percepto Drones", "Robotican", "Steadicopter", "Third Eye Systems",
        "Elbit Systems Drones", "IAI Drones", "High Lander Drones",
        "Smart Shooter", "HevenDrones", "רחפנים", 'כטב"ם', 'אינטגרטור כטב"ם',
        'ניסויי טיסה כטב"ם', "Drone Assembly Technician", "Counter-UAS Israel",
        "אינטגרטור מערכות", "Integration Technician Israel"
    ]
    drone_jobs = fetch_linkedin_jobs(drone_keywords, health)
    for j in drone_jobs:
        j["is_drone"] = True
    all_raw_jobs.extend(drone_jobs)

    # Comeet Scraper
    comeet_res = scrape_all_comeet_jobs()
    health.comeet_companies_attempted = comeet_res["attempted"]
    health.comeet_companies_successful = comeet_res["successes"]
    health.comeet_companies_failed = comeet_res["failures"]
    health.comeet_jobs_found = len(comeet_res["jobs"])
    
    for j in comeet_res["jobs"]:
        j["is_drone"] = True
        j["snippet"] = j.get("title", "")
    all_raw_jobs.extend(comeet_res["jobs"])

    # Deduplicate
    unique_candidates = []
    seen_links_current = set()
    seen_titles = set()

    for job in all_raw_jobs:
        link = job.get("link", "")
        base_link = link.split('?')[0] if link else ""
        title_company = f"{job.get('title', '')}|{job.get('company', '')}".lower()

        if not base_link:
            continue
            
        if base_link in seen_links_current or title_company in seen_titles:
            continue
            
        if base_link in seen_jobs or base_link in seen_drones or base_link in rejected_links:
            continue
        if link in seen_jobs or link in seen_drones or link in rejected_links:
            continue
            
        seen_links_current.add(base_link)
        seen_titles.add(title_company)
        unique_candidates.append(job)

    health.candidates_found = len(unique_candidates)
    print(f"[INIT] Found {len(unique_candidates)} new candidate job listings to evaluate.")

    processed_jobs = []
    new_links_energy = []
    new_links_drones = []

    for job in unique_candidates:
        eval_res = evaluate_and_enrich_job_with_gemini(
            genai_client,
            job["title"],
            job["company"],
            job.get("snippet", ""),
            job.get("is_drone", False),
            health
        )
        health.jobs_evaluated += 1
        
        if not eval_res:
            continue
            
        score = eval_res.get("match_score", 0)
        threshold = 70 if job.get("is_drone") else 60
        
        if score >= threshold:
            enriched_job = {
                "title": job["title"],
                "company": job["company"],
                "link": job["link"],
                "match_score": score,
                "reasoning": eval_res.get("reasoning", ""),
                "sector_key": eval_res.get("sector_key", "energy"),
                "sector": eval_res.get("sector", "תשתיות אנרגיה"),
                "company_domain_product": eval_res.get("company_domain_product", ""),
                "location": eval_res.get("location", "ישראל"),
                "job_summary": eval_res.get("job_summary", ""),
                "experience_strengths": eval_res.get("experience_strengths", ""),
                "key_highlights": eval_res.get("key_highlights", ""),
                "company_size": eval_res.get("company_size", ""),
                "junior_openness": eval_res.get("junior_openness", ""),
                "work_model": eval_res.get("work_model", ""),
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            processed_jobs.append(enriched_job)
            
        if job.get("is_drone"):
            new_links_drones.append(job["link"])
        else:
            new_links_energy.append(job["link"])

    health.jobs_passed = len(processed_jobs)
    print(f"[INIT] {len(processed_jobs)} jobs passed the score threshold.")

    # ---------------------------------------------------------
    # NEW CURATION: KEEP ONLY THE ABSOLUTE TOP 5 QUALITY JOBS
    # ---------------------------------------------------------
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_5_jobs = processed_jobs[:5]
    top_3 = top_5_jobs[:3]

    # Build Dashboard HTML using ONLY the top 5 jobs
    temp_archive = update_weekly_archive(top_5_jobs)
    active_dashboard_jobs = temp_archive if temp_archive else top_5_jobs
    build_and_save_docs_app(active_dashboard_jobs, is_weekly=False)
    
    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    curated_email_jobs = top_5_jobs
    email_html = build_unified_html_email(curated_email_jobs, top_3, dashboard_url)

    # Dispatch Single Unified Email
    msg = MIMEMultipart()
    if not processed_jobs:
        msg['Subject'] = Header(f"ℹ️ דוח משרות יומי - אין משרות חדשות שעברו סף | עידו גל", 'utf-8')
    else:
        msg['Subject'] = Header(f"🎯 דוח משרות יומי מאוחד ({len(curated_email_jobs)} משרות נבחרות) | עידו גל", 'utf-8')
    
    msg['From'] = Header(f"Job Search Automation <{sender_email}>", 'utf-8')
    msg['To'] = Header("idogal0210@gmail.com", 'utf-8')
    msg.attach(MIMEText(email_html, 'html', 'utf-8'))

    for attempt in range(1, 4):
        health.email_attempts += 1
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(sender_email, sender_pwd)
            server.sendmail(sender_email, "idogal0210@gmail.com", msg.as_string())
            server.quit()
            print(f"[EMAIL] Unified daily email successfully dispatched (Attempt {attempt}).")
            health.email_success = True
            break
        except Exception as e:
            print(f"[ERROR] Email dispatch attempt {attempt} failed: {e}")
            time.sleep(attempt * 5)
            
    if not health.email_success:
        print("[ERROR] All email attempts failed! Exiting with code 1 so GitHub Actions sees the failure.")
        health.final_status = "FAILED"
        health.print_summary()
        sys.exit(1)

    # Idempotency safe guard - only save local JSONs AFTER email succeeds
    save_seen_dict(SEEN_JOBS_FILE, seen_jobs, new_links_energy)
    save_seen_dict(SEEN_DRONES_FILE, seen_drones, new_links_drones)

    if health.gemini_failures > 0 and health.gemini_successes == 0 and health.jobs_evaluated > 0:
        health.final_status = "FAILED_AI"
        health.print_summary()
        sys.exit(1)
        
    if health.linkedin_failures > 0 or health.comeet_companies_failed > 0:
        health.final_status = "DEGRADED"
    else:
        health.final_status = "SUCCESS"

    health.print_summary()

if __name__ == "__main__":
    run_unified_daily_search()
