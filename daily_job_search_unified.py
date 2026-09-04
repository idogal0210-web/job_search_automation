import os
import sys
import json
import smtplib
import time
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

try:
    from src.ats_scraper import scrape_all_comeet_jobs
    from src.interactive_app_builder import build_and_save_docs_app
except ImportError:
    from ats_scraper import scrape_all_comeet_jobs
    from interactive_app_builder import build_and_save_docs_app

DATA_DIR = os.path.join(BASE_DIR, "data")
SEEN_JOBS_FILE = os.path.join(DATA_DIR, "seen_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "seen_jobs.json")
SEEN_DRONES_FILE = os.path.join(DATA_DIR, "seen_drones.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "seen_drones.json")
WEEKLY_ARCHIVE_FILE = os.path.join(DATA_DIR, "weekly_archive.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "weekly_archive.json")
REJECTED_JOBS_FILE = os.path.join(DATA_DIR, "rejected_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "rejected_jobs.json")
SAVED_JOBS_FILE = os.path.join(DATA_DIR, "saved_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "saved_jobs.json")
RETENTION_DAYS = 14

def check_already_ran_today():
    # Never block manual local runs, explicit --force, or manual workflow_dispatch triggers
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
                            print(f"[!] Workflow already succeeded today on schedule ({run_date}). Skipping duplicate email dispatch.")
                            return True
    except Exception as e:
        print(f"[!] Idempotency check warning: {e}")
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
    if not os.path.exists(REJECTED_JOBS_FILE):
        return set()
    try:
        with open(REJECTED_JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data if isinstance(data, list) else data.keys())
    except Exception:
        return set()

def save_seen_dict(file_path, seen_dict, new_links):
    now_iso = datetime.now().isoformat()
    for link in new_links:
        seen_dict[link] = now_iso
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(seen_dict, f, ensure_ascii=False, indent=2)

def update_weekly_archive(new_jobs):
    if not new_jobs:
        return
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
    
    for job in new_jobs:
        link = job.get("link")
        if link and link not in seen_links and link not in rejected_set:
            seen_links.add(link)
            job_copy = dict(job)
            job_copy["date"] = today_str
            archive.append(job_copy)
            
    with open(WEEKLY_ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

CV_CONTEXT = """
Name: Ido Gal (עידו גל)
Title: Gas Controller - Operations & Product (בקר גז - תפעול ומוצר) & Energy Systems | Practical Mechanical Engineer | Real-Time Control & Supply Continuity
Education: Practical Mechanical Engineer, Natural Gas & Green Energy (הנדסאי מכונות, התמחות בגז טבעי ובאנרגיה ירוקה), Ruppin Academic Center (2024). Certified Electrician Studies (2026 - לקראת סיום הלימודים, חודשיים). NOT a B.Sc. Engineer!
Skills: Real-time 24/7 SCADA & gas control, pressure/flow monitoring, nomination allocations, Excel, SAP, Python, Gemini/Copilot AI automation, Nahal Reconnaissance demolitions/combat engineering (סיירת נח"ל).
"""

NON_TECHNICAL_TITLES = [
    # Hebrew
    "שיווק", "מנהל מותג", "מנהלת מותג", "משאבי אנוש", "רכזת גיוס", "רכז גיוס", "גיוס עובדים",
    "הנהלת חשבונות", "מנהל חשבונות", "מנהלת חשבונות", "רואה חשבון", "רואת חשבון", "חשב שכר", "חשבת שכר",
    "יועץ משפטי", "יועצת משפטית", "עורך דין", "עורכת דין", "משפטי", "סיעוד", "אח מוסמך", "אחות מוסמכת",
    "רופא", "רופאה", "רוקח", "רוקחת", "מכירות טלפוניות", "טלמרקטינג", "נציג שירות", "נציגת שירות",
    "נציג מכירות", "נציגת מכירות", "מוקד", "קופאי", "קופאית", "מלצר", "מלצרית", "מזכיר", "מזכירה",
    "מנהל משרד", "מנהלת משרד", "קוסמטיקה", "טיפוח", "ביוטי", "רכש", "קניין", "קניינית",
    "ניקיון", "עובד ניקיון", "עובדת ניקיון", "בוחן חיובים", "בוחנת חיובים", "מנתח מערכות data",
    # English
    "brand manager", "marketing", "digital marketing", "social media", "seo", "human resources",
    "talent acquisition", "recruiter", "sourcer", "accountant", "bookkeeper", "payroll",
    "finance manager", "cfo", "legal counsel", "attorney", "lawyer", "compliance officer",
    "nurse", "nursing", "physician", "pharmacist", "sales representative", "telemarketing",
    "customer service", "customer support", "cashier", "receptionist", "office manager", "cosmetics", "beauty",
    "user acquisition", "procurement", "buyer", "cleaner", "tax preparer", "service desk",
    "bi analyst", "data analyst", "full stack", "web developer", "frontend", "backend", "software developer",
    "copywriter", "content writer", "salesperson", "sales manager", "product designer", "country club", "crm dynamics"
]

def evaluate_and_enrich_job_with_gemini(client, title, company, snippet, is_drone=False):
    """
    Evaluates job relevance AND extracts detailed structured section data using Gemini.
    Enforces candidate rules, strict exclusions, B.Sc. flexibility, and fail-closed integrity.
    """
    # 1. Deterministic Non-Technical & Blacklist Pre-Filters
    title_lower = title.lower()
    company_lower = company.lower()
    
    for bl in ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון", "raycatch", "רייקאץ"]:
        if bl in company_lower:
            print(f"[BLACKLIST] Disqualifying {company} - {title} (Match score: 0)")
            return {
                "match_score": 0,
                "reasoning": f"חברה ברשימת החרגה קשיחה ({company}) - נפסל מיידית.",
                "sector_key": "other",
                "sector": "לא רלוונטי",
                "company_domain_product": "",
                "location": "ישראל",
                "job_summary": "",
                "experience_strengths": "",
                "key_highlights": "",
                "company_size": "",
                "junior_openness": "",
                "work_model": ""
            }

    for non_tech in NON_TECHNICAL_TITLES:
        if non_tech in title_lower:
            print(f"[PRE-FILTER] Disqualifying non-technical role: {company} - {title} (matched '{non_tech}')")
            return {
                "match_score": 0,
                "reasoning": f"תפקיד שאינו טכני/הנדסי ('{non_tech}') - נפסל אוטומטית במערכת.",
                "sector_key": "other",
                "sector": "לא רלוונטי",
                "company_domain_product": "",
                "location": "ישראל",
                "job_summary": "",
                "experience_strengths": "",
                "key_highlights": "",
                "company_size": "",
                "junior_openness": "",
                "work_model": ""
            }

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
    1. STRICT EXCLUSIONS: If the company is "Energean", "INGL" (נתג"ז), "Chevron", or "Raycatch", give match_score: 0 and disqualify immediately.
    2. RELEVANCE & NON-TECHNICAL REJECTION:
       - Ido is a Practical Mechanical Engineer in natural gas, SCADA control, technical energy systems, and combat engineering/drones.
       - Any job completely outside engineering, technical operations, energy, mechanics, electricity, or drones/defense (e.g. Brand Manager, Marketing, Cosmetics, Sales, HR, Legal, Finance, Healthcare) MUST receive match_score: 0 and be disqualified immediately!
    3. B.Sc. REQUIREMENT & FLEXIBILITY:
       - Ido is a certified Practical Mechanical Engineer (הנדסאי מכונות), NOT a B.Sc. engineer.
       - If the job strictly and inflexibly requires a B.Sc. in engineering with zero leeway, disqualify it (match_score < 55).
       - ONLY allow B.Sc.-titled jobs if you identify genuine flexibility, practical openness, or if the company is known to accept experienced practical engineers (הנדסאים).
    4. DOMAIN PREFERENCES & TARGET COMPANIES:
       - Energy: Give a slight preference / bonus to Solar PV and Natural Gas opportunities (Ido's primary thesis & operational domains), while maintaining full openness and positive evaluation for all other energy fields (grid storage, power stations, thermal systems, wind, industrial infrastructure).
       - Target Company Bonus: Give a scoring bonus to companies in rapid growth (funded scale-ups like XTEND, Percepto, Spear UAV, Doral, Enlight, Nofar) or financially robust market leaders known for strong pay & benefits (Elbit, IAI, Rafael, OPC Energy, Ormat, Dalia Energy).
    5. 3-REQUIREMENTS MINIMUM MATCH IRON RULE:
       - The job MUST possess AT LEAST 3 CONCRETE, DEMONSTRABLE MATCHES between the stated job requirements/responsibilities and Ido's proven profile (Practical Mechanical Engineer, 24/7 SCADA & gas control room, natural gas & PRMS infrastructure, solar PV & BESS systems, upcoming Certified Electrician, or Nahal Reconnaissance operational drones/demolitions).
       - If a job has fewer than 3 concrete requirement matches (e.g. only generic soft skills or only 1-2 tenuous overlaps), you MUST give match_score < 50 and disqualify it immediately!
    6. MATCH SCORING (0-100):
       - Energy passing threshold: 60+. Drone/Defense passing threshold: 70+.
       - Score objectively based on Ido's genuine background: 24/7 gas/SCADA control, practical mechanical engineering, upcoming certified electrician (2 months), and Nahal Reconnaissance operational drone/combat engineering experience.

    Return STRICT JSON with keys:
    1. "match_score": integer (0 to 100).
    2. "reasoning": 1-2 sentence Hebrew justification.
    3. "sector_key": one of ["energy", "drones", "cuas", "avionics"].
    4. "sector": Hebrew sector title e.g. "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA" or "🚁 רחפנים וכטב״ם אוטונומי".
    5. "location": Hebrew location in 2-4 words (e.g. "תל אביב (היברידי)", "מתקן שטח / מרכז").
    6. "company_domain_product": 10-15 words Hebrew concise summary strictly describing the company's core domain and product (DO NOT repeat the company name or location here).
    7. "job_summary": 2-3 sentence Hebrew concise summary of core job duties and responsibilities.
    8. "experience_strengths": 1-2 sentence Hebrew tailored strengths mapping:
       - For Energy: Highlight 24/7 control room, gas pressures/flows, SCADA, INGL/platform interfaces, and Ruppin Natural Gas diploma.
       - For Drones/Defense: Highlight Nahal Reconnaissance field & operational drone piloting, demolitions, and precise mechanical assemblies.
       - For Industry/Operations: Highlight Practical Mechanical Engineer, pressure systems, and near-completion Certified Electrician (2 months).
    9. "key_highlights": 1-2 sentence Hebrew highlights covering:
       - Flexibility on B.Sc. / Practical Engineer openness.
       - Realistic salary range estimate for the Israeli market ONLY if known or strongly grounded (e.g. "הערכת שכר: 17,000-22,000 ₪"). If speculative, omit.
       - Shifts (24/7) or field/company car requirements if mentioned.
    10. "company_size": Hebrew company size estimate.
    11. "junior_openness": Hebrew openness indicator.
    12. "work_model": Hebrew work model.
    """
    
    # Cascade: Primary gemini-3.8-flash -> Fallbacks gemini-3.7-flash, gemini-3.5-flash, gemini-3.6-flash, gemini-flash-latest
    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-3.6-flash",
        "gemini-flash-latest"
    ]
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.15
                )
            )
            data = json.loads(response.text)
            return data
        except Exception:
            continue

    # Fail CLOSED: Never return dummy positive scores or fabricated text on error
    print(f"[-] Gemini evaluation failed for {company} - {title}. Disqualifying by default (score 0).")
    return {
        "match_score": 0,
        "reasoning": "שגיאת ניתוח או חוסר נתונים - נפסל אוטומטית למניעת שגיאות.",
        "sector_key": "other",
        "sector": "לא רלוונטי",
        "company_domain_product": "",
        "location": "ישראל",
        "job_summary": "",
        "experience_strengths": "",
        "key_highlights": "",
        "company_size": "",
        "junior_openness": "",
        "work_model": ""
    }

def fetch_linkedin_jobs(keywords, location="Israel", max_pages=2):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    jobs = []
    for kw in keywords:
        for page in range(max_pages):
            start = page * 25
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location={requests.utils.quote(location)}&start={start}"
            try:
                res = requests.get(url, headers=headers, timeout=8)
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
            except Exception:
                pass
    return jobs

def build_unified_html_email(jobs, top_3, dashboard_url):
    """
    Builds a Dark Mode List Layout email (matching dashboard_preview.html) with:
    - Category Pill Badge (Drones vs Energy)
    - Card Title with location next to it: [Company] - [Title] • [Location]
    - 4 distinct styled boxes with tinted backgrounds & borders:
      1. 🏢 תחום ומוצר החברה (Dark Slate Box)
      2. 📋 תקציר המשרה (Dark Slate Box)
      3. 💪 נקודות חוזק מהניסיון שלך (Emerald Tinted Box)
      4. 🔍 דגשים / דרישות נוספות (Amber Tinted Box)
    - Action CTA button with sky/blue gradient
    """
    now_str = datetime.now().strftime("%d.%m.%Y")

    sectors = {
        "energy": {"title": "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA", "jobs": []},
        "drones": {"title": "🚁 רחפנים, כטב\"ם אוטונומי ורובוטיקה", "jobs": []},
        "cuas": {"title": "🛡️ מערכות הגנת C-UAS וביטחון", "jobs": []},
        "avionics": {"title": "📡 מטע\"דים, אלקטרו-אופטיקה ואוויוניקה", "jobs": []}
    }

    for j in jobs:
        sec_key = j.get("sector_key", "energy")
        if sec_key not in sectors:
            sec_key = "energy"
        sectors[sec_key]["jobs"].append(j)

    # Top 3 Gold Picks Box (Dark Theme)
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

    # Sector Cards List (Dark Theme List matching dashboard_preview.html)
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
            
            # Category Badge
            if sec_key in ['drones', 'cuas', 'avionics']:
                badge_html = '<span style="background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">🚁 רחפנים וכטב״ם אוטונומי</span>'
            else:
                badge_html = '<span style="background-color: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">⚡ תשתיות אנרגיה וגז טבעי</span>'

            cards_html += f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 20px; margin-bottom: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.35);">
                <!-- Header -->
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

                <!-- Structured 4 Distinct Styled Boxes -->
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <!-- Box 1: Company Domain & Product -->
                    <div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;">
                        <span style="color: #38bdf8; font-weight: bold;">🏢 תחום ומוצר החברה:</span> {comp_domain}
                    </div>

                    <!-- Box 2: Job Summary -->
                    <div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;">
                        <span style="color: #38bdf8; font-weight: bold;">📋 תקציר המשרה:</span> {job_sum}
                    </div>

                    <!-- Box 3: Experience Strengths -->
                    <div style="background-color: rgba(6, 78, 59, 0.2); border: 1px solid rgba(5, 150, 105, 0.35); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #e2e8f0;">
                        <span style="color: #4ade80; font-weight: bold;">💪 נקודות חוזק מהניסיון שלך:</span> {strengths}
                    </div>

                    <!-- Box 4: Highlights / Requirements -->
                    <div style="background-color: rgba(120, 53, 15, 0.2); border: 1px solid rgba(217, 119, 6, 0.35); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;">
                        <span style="color: #fbbf24; font-weight: bold;">🔍 דגשים / דרישות נוספות:</span> {highlights}
                    </div>
                </div>

                <!-- Action CTA Button -->
                <div style="border-top: 1px solid rgba(51, 65, 85, 0.6); padding-top: 14px; margin-top: 14px; text-align: left;">
                    <a href="{j.get('link')}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; padding: 9px 22px; text-decoration: none; border-radius: 8px; font-size: 12.5px; font-weight: bold; display: inline-block; box-shadow: 0 4px 10px rgba(2, 132, 199, 0.35);">
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
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; border-radius: 14px; padding: 24px; text-align: center; margin-bottom: 24px; border: 1px solid #334155; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
            <h1 style="margin: 0 0 6px 0; font-size: 22px; color: #38bdf8; font-weight: 800;">🎯 דוח משרות יומי מאוחד | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך סריקה: {now_str} | סה"כ משרות נבחרות: {len(jobs)} (5 אנרגיה + 5 רחפנים)</div>
        </div>

        <!-- Interactive Web App CTA Button -->
        <div style="text-align: center; margin-bottom: 26px;">
            <a href="{dashboard_url}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; font-size: 14.5px; font-weight: bold; text-decoration: none; padding: 13px 28px; border-radius: 12px; display: inline-block; box-shadow: 0 6px 18px rgba(2, 132, 199, 0.4);">
                🚀 פתח דוח אינטראקטיבי וניהול משרות (✔️ / ✖️) ↗
            </a>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 8px;">כולל תובנות AI מורחבות על החברה, כמות עובדים, מדד פתיחות וסרגל התקדמות</div>
        </div>

        {top_3_html}

        {sector_blocks_html}

        <!-- Footer -->
        <div style="border-top: 1px solid #1e293b; padding-top: 16px; text-align: center; font-size: 12px; color: #64748b;">
            דוח זה הופק באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל.
        </div>

    </div>
</body>
</html>
"""
    return html

def run_unified_daily_search():
    print("[+] Starting Unified Daily Job Search Pipeline...")
    
    if check_already_ran_today():
        print("[+] Already ran successfully today. Exiting idempotently.")
        return

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[-] GEMINI_API_KEY missing. Exiting.")
        return

    genai_client = genai.Client(api_key=api_key, http_options={'timeout': 15000})

    seen_jobs = load_seen_dict(SEEN_JOBS_FILE)
    seen_drones = load_seen_dict(SEEN_DRONES_FILE)
    rejected_links = load_rejected_job_links()

    all_raw_jobs = []

    # 1. Energy Queries (Solar & Natural Gas focus + Grid & Power Plants)
    energy_keywords = [
        "הנדסאי מכונות", "בקר גז", "תפעול אנרגיה", "אנרגיה סולארית",
        "Field Service Engineer Israel", "Gas Controller Israel", "SCADA Operator Israel",
        "SolarEdge Israel", "Enlight Energy", "Doral Energy", "Nofar Energy",
        "Ormat Technologies", "OPC Energy", "Dalia Energy", "Edeltech",
        "Shikun & Binui Energy", "Control Room Operator Israel", "טכנאי חדר בקרה",
        "מפעיל תחנת כוח", "אגירת אנרגיה", "מערכות סולאריות"
    ]
    energy_jobs = fetch_linkedin_jobs(energy_keywords)
    for j in energy_jobs:
        j["is_drone"] = False
    all_raw_jobs.extend(energy_jobs)

    # 2. Drone & Defense Queries (Leading defense & scale-ups)
    drone_keywords = [
        "XTEND Drones", "Spear UAV", "Rafael Drone", "Airobotics",
        "Percepto Drones", "Robotican", "Steadicopter", "Third Eye Systems",
        "Elbit Systems Drones", "IAI Drones", "High Lander Drones",
        "Smart Shooter", "HevenDrones", "רחפנים", "כטב\"ם", "אינטגרטור כטב\"ם",
        "ניסויי טיסה כטב\"ם", "Drone Assembly Technician", "Counter-UAS Israel",
        "אינטגרטור מערכות", "Integration Technician Israel"
    ]
    drone_jobs = fetch_linkedin_jobs(drone_keywords)
    for j in drone_jobs:
        j["is_drone"] = True
    all_raw_jobs.extend(drone_jobs)

    # 3. Comeet ATS Scraper
    comeet_jobs = scrape_all_comeet_jobs()
    for j in comeet_jobs:
        j["is_drone"] = True
        j["snippet"] = j.get("title", "")
    all_raw_jobs.extend(comeet_jobs)

    # Deduplicate & filter against history AND persistent rejection set
    unique_candidates = []
    seen_current = set()

    for job in all_raw_jobs:
        link = job.get("link", "")
        if not link or link in seen_current or link in seen_jobs or link in seen_drones or link in rejected_links:
            continue
        seen_current.add(link)
        unique_candidates.append(job)

    print(f"[+] Found {len(unique_candidates)} new candidate job listings to evaluate.")

    processed_jobs = []
    new_links_energy = []
    new_links_drones = []

    for job in unique_candidates:
        eval_res = evaluate_and_enrich_job_with_gemini(
            genai_client,
            job["title"],
            job["company"],
            job.get("snippet", ""),
            is_drone=job.get("is_drone", False)
        )
        
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
                "company_domain_product": eval_res.get("company_domain_product", eval_res.get("company_summary", "")),
                "location": eval_res.get("location", "ישראל"),
                "job_summary": eval_res.get("job_summary", eval_res.get("company_summary", "")),
                "experience_strengths": eval_res.get("experience_strengths", eval_res.get("reasoning", "")),
                "key_highlights": eval_res.get("key_highlights", ""),
                "company_summary": eval_res.get("company_summary", ""),
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

    print(f"[+] {len(processed_jobs)} jobs passed the score threshold.")

    # Save to history & archive
    save_seen_dict(SEEN_JOBS_FILE, seen_jobs, new_links_energy)
    save_seen_dict(SEEN_DRONES_FILE, seen_drones, new_links_drones)
    update_weekly_archive(processed_jobs)

    # Build GitHub Pages interactive app
    build_and_save_docs_app(processed_jobs, is_weekly=False)

    # GitHub Pages Live URL
    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    # Sort by match score
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_3 = processed_jobs[:3]

    # Select 5 Energy + 5 Drones = Total 10 Jobs for daily email
    energy_jobs_top5 = [j for j in processed_jobs if j.get("sector_key") == "energy"][:5]
    drone_jobs_top5 = [j for j in processed_jobs if j.get("sector_key") in ["drones", "cuas", "avionics"]][:5]

    curated_set = set(j.get("link") for j in energy_jobs_top5 + drone_jobs_top5)
    remaining_jobs = [j for j in processed_jobs if j.get("link") not in curated_set]

    while len(energy_jobs_top5) < 5 and remaining_jobs:
        energy_jobs_top5.append(remaining_jobs.pop(0))

    while len(drone_jobs_top5) < 5 and remaining_jobs:
        drone_jobs_top5.append(remaining_jobs.pop(0))

    curated_email_jobs = energy_jobs_top5 + drone_jobs_top5

    # Build HTML email
    email_html = build_unified_html_email(curated_email_jobs, top_3, dashboard_url)

    # Dispatch Single Unified Email
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_pwd = os.environ.get("SENDER_APP_PASSWORD")
    recipient = "idogal0210@gmail.com"

    if sender_email and sender_pwd:
        import time
        msg = MIMEMultipart()
        msg['Subject'] = Header(f"🎯 דוח משרות יומי מאוחד (10 משרות נבחרות: 5 אנרגיה + 5 רחפנים) | עידו גל", 'utf-8')
        msg['From'] = Header(f"Job Search Automation <{sender_email}>", 'utf-8')
        msg['To'] = Header(recipient, 'utf-8')
        msg.attach(MIMEText(email_html, 'html', 'utf-8'))

        for attempt in range(1, 4):
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
                server.starttls()
                server.login(sender_email, sender_pwd)
                server.sendmail(sender_email, recipient, msg.as_string())
                server.quit()
                print(f"[+] Unified daily email successfully dispatched to {recipient} (Attempt {attempt}).")
                break
            except Exception as e:
                print(f"[!] Email dispatch attempt {attempt} failed: {e}")
                time.sleep(attempt * 5)

if __name__ == "__main__":
    run_unified_daily_search()
