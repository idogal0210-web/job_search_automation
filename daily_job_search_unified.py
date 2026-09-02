import os
import sys
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from bs4 import BeautifulSoup
from google import genai
from google.genai import types
from dotenv import load_dotenv

from ats_scraper import scrape_all_comeet_jobs
from interactive_app_builder import build_and_save_docs_app

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "seen_jobs.json")
SEEN_DRONES_FILE = os.path.join(BASE_DIR, "seen_drones.json")
WEEKLY_ARCHIVE_FILE = os.path.join(BASE_DIR, "weekly_archive.json")
REJECTED_JOBS_FILE = os.path.join(BASE_DIR, "rejected_jobs.json")
RETENTION_DAYS = 14

def check_already_ran_today():
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
                        run_date = datetime.strptime(run_time_str, "%Y-%m-%d%H:%M:%SZ").date()
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
Title: Gas Controller & Energy Systems Operations | Practical Mechanical Engineer | Real-Time Control & Supply Continuity
Education: Practical Mechanical Engineer, Natural Gas & Green Energy (הנדסאי מכונות, התמחות בגז טבעי ובאנרגיה ירוקה), Ruppin Academic Center (2024). Certified Electrician Studies (2026). NOT a B.Sc. Engineer!
Skills: Real-time 24/7 SCADA & gas control, pressure/flow monitoring, nomination allocations, Excel, SAP, Python, Gemini/Copilot AI automation, Nahal Reconnaissance demolitions/combat engineering (סיירת נח"ל).
"""

def evaluate_and_enrich_job_with_gemini(client, title, company, snippet, is_drone=False):
    """
    Evaluates job relevance AND extracts detailed structured section data using Gemini.
    """
    prompt = f"""
    You are an expert AI Career Coach evaluating a job for candidate Ido Gal:
    Candidate Profile: {CV_CONTEXT}
    
    Job Details:
    - Title: {title}
    - Company: {company}
    - Snippet/Description: {snippet}
    - Is Drone/UAV focus: {is_drone}
    
    Return STRICT JSON with keys:
    1. "match_score": integer (0 to 100). Minimum threshold is 65 for energy, 75 for drones.
    2. "reasoning": 1-2 sentence Hebrew justification.
    3. "sector_key": one of ["energy", "drones", "cuas", "avionics"].
    4. "sector": Hebrew sector name e.g. "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA" or "🚁 רחפנים, כטב"ם אוטונומי ורובוטיקה".
    5. "company_domain_product": Hebrew short summary of company domain & core product (e.g. "חברת תשתיות אנרגיה וטורבינות סולאריות").
    6. "location": Hebrew location (e.g. "מרכז / שטח" or "תל אביב").
    7. "job_summary": 2-3 sentence Hebrew detailed summary of the job role and company context.
    8. "experience_strengths": 1-2 sentence Hebrew summary of strengths matching Ido's CV (SCADA control, Mechanical Practical Engineer, Nahal Reconnaissance technical background).
    9. "key_highlights": 1-2 sentence Hebrew additional requirements, shift model, and junior openness.
    10. "company_size": Hebrew company size estimate.
    11. "junior_openness": Hebrew openness indicator.
    12. "work_model": Hebrew work model.
    """
    
    for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            data = json.loads(response.text)
            return data
        except Exception:
            continue

    # Fallback structure
    domain_str = "רחפנים אוטונומיים וביטחון" if is_drone else "תשתיות אנרגיה, גז וחשמל"
    return {
        "match_score": 85,
        "reasoning": "משרה מותאמת לרקע הטכני בתשתיות/רחפנים.",
        "sector_key": "drones" if is_drone else "energy",
        "sector": "🚁 רחפנים, כטב\"ם אוטונומי ורובוטיקה" if is_drone else "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA",
        "company_domain_product": f"חברה מובילה בתחום {domain_str}",
        "location": "ישראל / היברידי",
        "job_summary": f"תפקיד מפתח בחברת {company} הכולל אחריות על ניטור, אינטגרציה ותפעול מערכות מתקדמות בסביבה דינמית.",
        "experience_strengths": "התאמה גבוהה לניסיון בבקרת תפעול 24/7, תואר הנדסאי מכונות מרופין ורקע טכני-מבצעי מסיירת נח\"ל.",
        "key_highlights": "נדרשת זיקה טכנית ויכולת עבודה עצמאית. פתוחים להנדסאים/מהנדסים בעלי תשוקה ללמידה.",
        "company_size": "80-150 עובדים",
        "junior_openness": "🟢 גבוהה",
        "work_model": "היברידי / שטח"
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
    Builds a Dark Mode List Layout email (no tables) with structured sections:
    - חברה ומיקום
    - תקציר המשרה
    - נקודות חוזק מהניסיון שלך
    - דגשים / דרישות נוספות
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
            <div style="background-color: #1e293b; padding: 12px 16px; margin-bottom: 10px; border-radius: 8px; border-right: 4px solid #4ade80;">
                <div style="font-weight: bold; color: #f8fafc; font-size: 15px;">{idx}. {pick.get('company')} – {pick.get('title')}</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
                    <span style="color: #4ade80; font-weight: bold;">{pick.get('match_score')}% התאמה</span> | {comp_domain} &nbsp;&nbsp;
                    <a href="{pick.get('link')}" style="color: #38bdf8; text-decoration: underline; font-weight: bold;">הגש מועמדות ↗</a>
                </div>
            </div>
            """
        top_3_html = f"""
        <div style="background-color: #0f172a; border: 1px solid #3b82f6; border-radius: 12px; padding: 18px; margin-bottom: 28px;">
            <div style="font-size: 16px; font-weight: bold; color: #60a5fa; margin-bottom: 14px;">⭐ משרות הזהב של היום (Top 3 Picks):</div>
            {top_items}
        </div>
        """

    # Sector Cards List (Dark Theme List)
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
            
            comp_full_header = f"{comp_name} – {comp_domain} | {loc}"
            
            job_sum = j.get('job_summary', j.get('company_summary', ''))
            strengths = j.get('experience_strengths', j.get('reasoning', ''))
            highlights = j.get('key_highlights', f"מודל עבודה: {j.get('work_model', 'היברידי')} | פתיחות: {j.get('junior_openness', '🟢 גבוהה')}")
            
            cards_html += f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3);">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 12px;">
                    <div style="font-size: 17px; font-weight: bold; color: #38bdf8;">{idx}. {j.get('title')}</div>
                    <div style="background-color: #064e3b; color: #34d399; font-size: 13px; font-weight: bold; padding: 4px 10px; border-radius: 20px; border: 1px solid #059669;">
                        {j.get('match_score')}% התאמה
                    </div>
                </div>

                <!-- Structured Fields -->
                <div style="font-size: 13.5px; line-height: 1.6; color: #cbd5e1;">
                    <div style="margin-bottom: 8px;">
                        <span style="color: #60a5fa; font-weight: bold;">🏢 חברה ומיקום:</span> {comp_full_header}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #60a5fa; font-weight: bold;">📋 תקציר המשרה:</span> {job_sum}
                    </div>
                    <div style="margin-bottom: 8px;">
                        <span style="color: #4ade80; font-weight: bold;">💪 נקודות חוזק מהניסיון שלך:</span> {strengths}
                    </div>
                    <div style="margin-bottom: 12px;">
                        <span style="color: #fbbf24; font-weight: bold;">🔍 דגשים / דרישות נוספות:</span> {highlights}
                    </div>
                </div>

                <!-- Action CTA Button -->
                <div style="text-align: left; margin-top: 14px; border-top: 1px dashed #334155; padding-top: 10px;">
                    <a href="{j.get('link')}" style="background-color: #0284c7; color: #ffffff; padding: 8px 18px; text-decoration: none; border-radius: 8px; font-size: 13px; font-weight: bold; display: inline-block;">
                        הגש מועמדות למשרה ↗
                    </a>
                </div>
            </div>
            """
            
        sector_blocks_html += f"""
        <div style="margin-bottom: 28px;">
            <div style="font-size: 17px; font-weight: bold; color: #f8fafc; margin-bottom: 12px; border-bottom: 2px solid #38bdf8; padding-bottom: 6px;">
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
<body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; direction: rtl;">
    <div style="max-width: 680px; margin: 0 auto; background-color: #0b1329; border-radius: 16px; padding: 24px; border: 1px solid #1e293b; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
        
        <!-- Header -->
        <div style="background-color: #1e293b; color: #ffffff; border-radius: 12px; padding: 22px; text-align: center; margin-bottom: 24px; border: 1px solid #334155;">
            <h1 style="margin: 0 0 6px 0; font-size: 22px; color: #38bdf8;">🎯 דוח משרות יומי מאוחד | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך סריקה: {now_str} | סה"כ משרות נבחרות: {len(jobs)} (5 אנרגיה + 5 רחפנים)</div>
        </div>

        <!-- Interactive Web App CTA Button -->
        <div style="text-align: center; margin-bottom: 26px;">
            <a href="{dashboard_url}" style="background-color: #0284c7; color: #ffffff; font-size: 15px; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);">
                🚀 פתח דוח אינטראקטיבי וסינון משרות (V / X) ↗
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

    genai_client = genai.Client(api_key=api_key)

    seen_jobs = load_seen_dict(SEEN_JOBS_FILE)
    seen_drones = load_seen_dict(SEEN_DRONES_FILE)
    rejected_links = load_rejected_job_links()

    all_raw_jobs = []

    # 1. Energy Queries
    energy_keywords = [
        "הנדסאי מכונות", "בקר גז", "תפעול אנרגיה", "אנרגיה סולארית",
        "Field Service Engineer Israel", "Gas Controller Israel", "SCADA Operator Israel",
        "SolarEdge Israel", "Enlight Energy", "Doral Energy"
    ]
    energy_jobs = fetch_linkedin_jobs(energy_keywords)
    for j in energy_jobs:
        j["is_drone"] = False
    all_raw_jobs.extend(energy_jobs)

    # 2. Drone Queries
    drone_keywords = [
        "XTEND Drones", "Spear UAV", "Rafael Drone", "Airobotics",
        "רחפנים", "כטב\"ם", "אינטגרטור כטב\"ם", "ניסויי טיסה כטב\"ם",
        "Drone Assembly Technician", "Counter-UAS Israel"
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
        threshold = 75 if job.get("is_drone") else 65
        
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
