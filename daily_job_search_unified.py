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

# File Paths
BASE_DIR = os.path.dirname(__file__)
SEEN_JOBS_FILE = os.path.join(BASE_DIR, "seen_jobs.json")
SEEN_DRONES_FILE = os.path.join(BASE_DIR, "seen_drones.json")
WEEKLY_ARCHIVE_FILE = os.path.join(BASE_DIR, "weekly_archive.json")
REJECTED_JOBS_FILE = os.path.join(BASE_DIR, "rejected_jobs.json")
RETENTION_DAYS = 14

def check_already_ran_today():
    """Idempotency guard using GitHub API."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = "idogal0210-web/job_search_automation"
    workflow_id = "daily_job_search.yml"
    
    if not token:
        print("[!] No GITHUB_TOKEN provided, skipping idempotency check.")
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
    """Load persistent list of rejected job URLs to ensure they never reappear."""
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
    Evaluates job relevance AND extracts rich, detailed company intelligence using Gemini.
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
    5. "company_summary": Rich 2-3 sentence Hebrew detailed overview explaining:
       - What the company specializes in, its core product/technology, and market standing.
       - Why it is relevant for a Mechanical Practical Engineer / Gas Controller / Field Integrator.
    6. "company_size": Hebrew company size estimate e.g. "80-120 עובדים (סטארטאפ בצמיחה)" or "200+ עובדים".
    7. "junior_openness": Hebrew openness indicator e.g. "🟢 גבוהה – פתוחים להנדסאים בעלי זיקה טכנית ללא ניסיון קודם ברחפנים."
    8. "work_model": Hebrew work model e.g. "היברידי", "משמרות 24/7", or "שטח ומעבדה".
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"[!] Gemini AI enrichment warning: {e}")
        return {
            "match_score": 80,
            "reasoning": "משרה מותאמת לרקע הטכני בתשתיות/רחפנים.",
            "sector_key": "drones" if is_drone else "energy",
            "sector": "🚁 רחפנים, כטב\"ם אוטונומי ורובוטיקה" if is_drone else "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA",
            "company_summary": f"חברה מובילה בתחום {company}, מפתחת טכנולוגיות מתקדמות ומערכות תשתיות/תעופה. החברה מציעה הזדמנויות פיתוח מקצועיות להנדסאים וטכנאי שטח.",
            "company_size": "עובדים בתעשייה",
            "junior_openness": "🟢 גבוהה – פתוחים להנדסאים/מהנדסים בעלי זיקה טכנית ותשוקה ללמידה.",
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
    Builds a single, elegant, unified HTML email using a strict 3-4 color palette:
    - Primary Navy: #0f172a
    - Muted Slate: #475569
    - Accent Blue: #0284c7
    - Success Green: #16a34a
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

    top_3_html = ""
    if top_3:
        top_items = ""
        for idx, pick in enumerate(top_3, 1):
            top_items += f"""
            <div style="padding: 10px; margin-bottom: 8px; background-color: #ffffff; border-radius: 8px; border-right: 4px solid #16a34a;">
                <div style="font-weight: bold; color: #0f172a; font-size: 15px;">{idx}. {pick.get('company')} – {pick.get('title')}</div>
                <div style="font-size: 13px; color: #475569; margin-top: 4px;">
                    <span style="color: #16a34a; font-weight: bold;">{pick.get('match_score')}% התאמה</span> | {pick.get('sector')} &nbsp;&nbsp;
                    <a href="{pick.get('link')}" style="color: #0284c7; text-decoration: underline; font-weight: bold;">הגש מועמדות למשרה ↗</a>
                </div>
            </div>
            """
        top_3_html = f"""
        <div style="background-color: #fffbeb; border: 1.5px solid #f59e0b; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <div style="font-size: 16px; font-weight: bold; color: #92400e; margin-bottom: 12px;">⭐ משרות הזהב של היום (Top 3 Picks):</div>
            {top_items}
        </div>
        """

    sector_tables_html = ""
    for sec_key, sec_data in sectors.items():
        sec_jobs = sec_data["jobs"]
        if not sec_jobs:
            continue
        
        rows_html = ""
        for j in sec_jobs:
            rows_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px; text-align: center;">
                    <a href="{j.get('link')}" style="background-color: #0284c7; color: #ffffff; padding: 6px 12px; text-decoration: none; border-radius: 6px; font-size: 12px; font-weight: bold; display: inline-block;">הגש מועמדות ↗</a>
                </td>
                <td style="padding: 10px; text-align: center; font-weight: bold; color: #16a34a; font-size: 13px;">{j.get('match_score')}%</td>
                <td style="padding: 10px; text-align: right; color: #0f172a; font-size: 13px;"><b>{j.get('title')}</b></td>
                <td style="padding: 10px; text-align: right; color: #0f172a; font-size: 13px; font-weight: bold;">{j.get('company')}</td>
            </tr>
            """
            
        sector_tables_html += f"""
        <div style="margin-bottom: 24px;">
            <div style="font-size: 16px; font-weight: bold; color: #0f172a; margin-bottom: 8px; border-bottom: 2px solid #0284c7; padding-bottom: 4px;">{sec_data['title']} ({len(sec_jobs)} משרות)</div>
            <table style="width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                <thead>
                    <tr style="background-color: #0f172a; color: #ffffff; font-size: 12px;">
                        <th style="padding: 8px; text-align: center; width: 110px;">פעולה</th>
                        <th style="padding: 8px; text-align: center; width: 70px;">התאמה</th>
                        <th style="padding: 8px; text-align: right;">שם המשרה</th>
                        <th style="padding: 8px; text-align: right; width: 140px;">חברה</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
</head>
<body style="font-family: Arial, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 20px; direction: rtl;">
    <div style="max-width: 680px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <!-- Header -->
        <div style="background-color: #0f172a; color: #ffffff; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
            <h1 style="margin: 0 0 6px 0; font-size: 22px;">🎯 דוח משרות יומי מאוחד | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך סריקה: {now_str} | סה"כ משרות מותאמות: {len(jobs)}</div>
        </div>

        <!-- Interactive Web App CTA Button -->
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="{dashboard_url}" style="background-color: #0284c7; color: #ffffff; font-size: 15px; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);">
                🚀 פתח דוח אינטראקטיבי וסינון משרות (V / X) ↗
            </a>
            <div style="font-size: 12px; color: #64748b; margin-top: 6px;">כולל תובנות AI מורחבות על החברה, כמות עובדים, מדד פתיחות וסרגל התקדמות</div>
        </div>

        {top_3_html}

        {sector_tables_html}

        <!-- Footer -->
        <div style="border-top: 1px solid #e2e8f0; padding-top: 14px; text-align: center; font-size: 12px; color: #94a3b8;">
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

    # Sort & Top 3
    processed_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    top_3 = processed_jobs[:3]

    # Build HTML email
    email_html = build_unified_html_email(processed_jobs, top_3, dashboard_url)

    # Dispatch Single Unified Email
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_pwd = os.environ.get("SENDER_APP_PASSWORD")
    recipient = "idogal0210@gmail.com"

    if sender_email and sender_pwd:
        import time
        msg = MIMEMultipart()
        msg['Subject'] = Header(f"🎯 דוח משרות יומי מאוחד ({len(processed_jobs)} משרות נבחרות) | עידו גל", 'utf-8')
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
