import os
import sys
import json
import smtplib
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "seen_drones.json")
ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "weekly_archive.json")
RETENTION_DAYS = 14

DAY_NAMES = {
    0: "יום ב'",
    1: "יום ג'",
    2: "יום ד'",
    3: "יום ה'",
    4: "יום ו'",
    5: "יום שבת",
    6: "יום א'"
}

def load_seen_drones():
    """Load previously sent drone jobs and prune any older than 14 days."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
        fresh_data = {}
        for link, ts_str in data.items():
            try:
                ts = datetime.fromisoformat(ts_str)
                if ts > cutoff:
                    fresh_data[link] = ts_str
            except Exception:
                pass
        return fresh_data
    except Exception as e:
        print(f"[-] Error reading seen_drones.json: {e}")
        return {}

def save_seen_drones(seen_dict, newly_sent_jobs):
    """Save newly sent drone jobs into seen_drones.json and weekly_archive.json."""
    now = datetime.now()
    now_iso = now.isoformat()
    today_str = now.strftime("%Y-%m-%d")
    day_name = DAY_NAMES.get(now.weekday(), "")

    for job in newly_sent_jobs:
        link = job.get("link", "").strip()
        if link:
            seen_dict[link] = now_iso

    # 1. Save seen_drones.json
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_dict, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated {HISTORY_FILE} with {len(newly_sent_jobs)} newly sent drone jobs.")
    except Exception as e:
        print(f"[-] Error writing seen_drones.json: {e}")

    # 2. Append to weekly_archive.json
    archive_list = []
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive_list = json.load(f)
        except Exception:
            archive_list = []

    cutoff_date = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    archive_list = [j for j in archive_list if j.get("date", "") >= cutoff_date]

    for job in newly_sent_jobs:
        archive_list.append({
            "date": today_str,
            "day_name": day_name,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "match_score": job.get("match_score", 0),
            "sector": "רחפנים, כטב\"ם ורובוטיקה",
            "summary": job.get("summary_hebrew", ""),
            "link": job.get("link", ""),
            "license_status": job.get("license_status", "none"),
            "license_note": job.get("license_note_hebrew", "")
        })

    try:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive_list, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated {ARCHIVE_FILE} with categorized drone jobs for weekly digest.")
    except Exception as e:
        print(f"[-] Error writing weekly_archive.json: {e}")

# Candidate Profile Context for Drone Jobs Evaluation
IDO_DRONE_CV_SUMMARY = """
Name: Ido Gal (עידו גל)
Email: idogal0210@gmail.com | Phone: 052-632-8886 | Location: Tel Aviv - Or Aqiva (Center, Sharon, North, or Relocation).

Degree / Qualifications:
- Practical Mechanical Engineer (הנדסאי מכונות), Ruppin Academic Center (2024). NOT a B.Sc. Engineer!
- Certified Electrician (חשמלאי מוסמך), Ruppin Academic Center (Expected 2026).
- Drone Pilot License Status: Currently does NOT hold a commercial CAAI (רת"א) drone pilot license.

Military & Combat Leadership:
- Combat Commander & Demolitions in Nahal Reconnaissance Unit (סיירת נח"ל - חבלה ופיקוד 07/08): High technical discipline, field leadership under pressure, hands-on mechanical & tactical operational skills.

Professional Experience:
- Gas Controller at Energean Israel Ltd. (2022–Present): 24/7 real-time operations, telemetry monitoring, SCADA, critical emergency decision making under stress.
- Security Officer at Energean/Vulcan (2020–2022): Tactical security & infrastructure protection.
- International Sales Team Leader & Trainer (2015–2020): US & Germany, team leadership, cross-cultural training.
- Solar PV Systems Installer at MER Group (2010–2012): Electrical wiring, hands-on installation & commissioning.

TARGET DRONE & AEROSPACE COMPANIES (BOOST +10%):
⭐ Drone Pioneers: Percepto, XTEND, HevenDrones, Airobotics, SpearUAV, Steadicopter, Flytrex, Robotican, Copterpix, High Lander, Sightec.
⭐ Defense & Aerospace Giants: Elbit Systems (אלביט מערכות), IAI (התעשייה האווירית), Rafael (רפאל), BlueBird Aero Systems.
⭐ Drone Tech, Payloads & Avionics: NextVision (נקסט ויז'ן), ParaZero, D-Fend Solutions, Skylock, Axon Vision, Sentrycs.

CATEGORIZATION OF DRONE JOBS BY LICENSE REQUIREMENT:
1. None (ללא צורך ברישיון מטיס): Mechanical Assembly, Integration, Control Room / Remote Operations, Electrical & Avionics Wiring, Demolitions/Testing.
2. Training Provided (החברה מספקת הכשרה והסמכה): Companies that train candidates to become certified drone pilots/operators on the job.
3. Advantage (רישיון מטיס כיתרון): Field testing or customer support where a pilot license is a plus but not strictly mandatory.
4. Mandatory (רישיון מטיס כדרישת סף): Roles strictly requiring an active commercial CAAI (רת"א) pilot license.

EXCLUDED / REJECTED:
❌ Energean, INGL, Chevron Israel, Raycatch.
❌ Jobs requiring ONLY B.Sc. Aerospace/Mechanical Engineer where Practical Engineer (הנדסאי) is strictly rejected.
❌ Minimum Match Score threshold: 65%.
"""

def fetch_drone_jobs(seen_drones_dict):
    """Fetch potential drone, UAV, and autonomous robotics jobs from LinkedIn Israel."""
    jobs = []
    print("[+] Fetching live Drone & UAV job listings from LinkedIn Israel...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # 1. Drone specific role queries
    drone_queries = [
        "רחפנים",
        "כטבמ",
        "כטב\"ם",
        "Drone Engineer",
        "UAV Technician",
        "Flight Test Technician Israel",
        "מטיס רחפנים",
        "הנדסאי מכונות רחפנים",
        "אינטגרטור כטב\"ם",
        "טכנאי רחפנים",
        "Avionics Technician Israel",
        "Drone Operator Israel",
        "Autonomous Systems Technician Israel",
        "Field Operator Drones",
        "UAV Integration",
        "מפעיל כטבמ"
    ]

    # 2. Drone specific companies queries
    drone_companies = [
        "Percepto Drones",
        "XTEND Reality",
        "Heven Drones",
        "Airobotics",
        "Spear UAV",
        "Steadicopter",
        "Flytrex",
        "BlueBird Aero Systems",
        "Robotican",
        "NextVision",
        "ParaZero",
        "D-Fend Solutions",
        "Elbit Systems UAV",
        "IAI Drones",
        "Rafael Defense Drones"
    ]

    all_queries = []
    for q in drone_queries:
        all_queries.append((q, 0))
        all_queries.append((q, 25))
    for c in drone_companies:
        all_queries.append((c, 0))

    seen_links_current_run = set()

    for kw, start_idx in all_queries:
        try:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location=Israel&start={start_idx}"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for card in soup.find_all("li"):
                    title_elem = card.find("h3", class_="base-search-card__title")
                    comp_elem = card.find("h4", class_="base-search-card__subtitle")
                    link_elem = card.find("a", class_="base-card__full-link")
                    loc_elem = card.find("span", class_="job-search-card__location")

                    if title_elem and link_elem:
                        title = title_elem.text.strip()
                        company = comp_elem.text.strip() if comp_elem else ""
                        link = link_elem.get("href", "").split("?")[0].strip()
                        loc = loc_elem.text.strip() if loc_elem else "ישראל"

                        if link in seen_drones_dict or link in seen_links_current_run:
                            continue

                        if any(ex in company.lower() or ex in title.lower() for ex in ["energean", "אנרג'יאן", "ingl", "נתג", "chevron", "שברון", "raycatch"]):
                            continue

                        seen_links_current_run.add(link)
                        jobs.append({
                            "title": f"{company} - {title}",
                            "snippet": f"משרה בתחום הרחפנים/כטב\"ם בחברת {company} במיקום {loc}. דרישות: {title}",
                            "link": link
                        })
        except Exception:
            pass

    print(f"[+] Successfully fetched {len(jobs)} FRESH drone candidate jobs (after 14-day history filtering & deduplication).")
    return jobs

def evaluate_drone_jobs_with_gemini(job_list):
    """Use Gemini AI to analyze fit and classify licensing requirements for Drone/UAV roles."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("[-] GEMINI_API_KEY missing.")
        return []

    client = genai.Client(api_key=gemini_key)
    evaluated_jobs = []

    candidate_batch = job_list[:80]

    prompt = f"""
You are an expert AI Aerospace & Drone Career Advisor evaluating Drone/UAV/Robotics jobs for Ido Gal.

CANDIDATE CV PROFILE & RULES:
{IDO_DRONE_CV_SUMMARY}

JOB POSTINGS TO EVALUATE:
{json.dumps(candidate_batch, ensure_ascii=False, indent=2)}

Filter and evaluate the jobs strictly according to the candidate profile and categorize by drone licensing status.
Return a JSON array of objects with the following schema for jobs matching score >= 65%:
[
  {{
    "title": "שם התפקיד והחברה",
    "link": "URL link",
    "match_score": 85, (integer 65-100),
    "company": "שם החברה",
    "location": "מיקום (מרכז / שרון / צפון / Remote)",
    "summary_hebrew": "תקציר ממוקד בעברית של 2 שורות בלבד על התפקיד, הרחפנים/מערכות והאחריות",
    "pros_hebrew": "2-3 נקודות חוזק בולטות להתאמה מהניסיון של עידו",
    "gaps_hebrew": "דרישות חובה או פערים לתשומת לב",
    "license_status": "none" | "training_provided" | "advantage" | "mandatory",
    "license_note_hebrew": "הסבר קצר על סטטוס הרישיון (למשל: 'אין צורך ברישיון מטיס', 'החברה מכשירה ומסמיכה מטיסים', 'רישיון מטיס כיתרון בלבד', 'רישיון מטיס רת\"א כדרישת סף')"
  }}
]

CRITICAL RULES:
- ONLY include jobs relevant to Drones, UAV, Autonomous Robotics, Flight Testing, Integration, Mechanical, or Defense Systems.
- ONLY include jobs with match_score >= 65.
- Categorize 'license_status' accurately:
  * 'none': For Mechanical Engineering, Integration, Control Room, Electrical/Avionics wiring, Demolitions/Explosives testing.
  * 'training_provided': For companies offering in-house flight training & operator certification.
  * 'advantage': When flight license is listed as a plus/advantage only.
  * 'mandatory': When an active commercial drone pilot license is strictly required.
- Reject B.Sc. Engineer ONLY jobs where Practical Engineer (הנדסאי) is strictly rejected.
- Maximum 6 best jobs returned.
- Return ONLY valid raw JSON array inside backticks.
"""

    models_to_try = [
        'gemini-3.5-flash',
        'gemini-3.6-flash',
        'gemini-flash-latest',
        'gemini-2.5-flash-lite'
    ]

    import time
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                print(f"[+] [DRONES] Evaluating with model: {model_name} (attempt {attempt+1})...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]

                evaluated_jobs = json.loads(text.strip())
                if evaluated_jobs:
                    print(f"[+] [DRONES] Successfully evaluated {len(evaluated_jobs)} matching drone jobs.")
                    break
            except Exception as e:
                print(f"[-] [DRONES] Model {model_name} error: {e}")
                time.sleep(2)
        if evaluated_jobs:
            break

    evaluated_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return evaluated_jobs[:6]

def build_drone_html_email(evaluated_jobs):
    """Build a specialized Aero-Tech styled RTL HTML email with explicit licensing badges and categories."""
    
    # Categorize jobs for structured display
    cat_none = [j for j in evaluated_jobs if j.get("license_status") == "none"]
    cat_training = [j for j in evaluated_jobs if j.get("license_status") == "training_provided"]
    cat_adv = [j for j in evaluated_jobs if j.get("license_status") == "advantage"]
    cat_mand = [j for j in evaluated_jobs if j.get("license_status") == "mandatory"]

    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #0b1329; margin: 0; padding: 18px; color: #f8fafc; direction: rtl; text-align: right; }}
            .container {{ max-width: 660px; margin: 0 auto; background: #131f37; border-radius: 14px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.45); border: 1px solid #233554; direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #0284c7 0%, #0369a1 50%, #075985 100%); color: #ffffff; padding: 26px 20px; text-align: center; direction: rtl; }}
            .header h1 {{ margin: 0; font-size: 23px; font-weight: 800; color: #ffffff; }}
            .header p {{ margin: 6px 0 0 0; opacity: 0.95; font-size: 14px; color: #e0f2fe; }}
            .content {{ padding: 22px; direction: rtl; text-align: right; }}
            
            /* Section Titles */
            .section-title {{ font-size: 15px; font-weight: bold; padding: 8px 12px; border-radius: 6px; margin: 20px 0 12px 0; display: flex; align-items: center; justify-content: space-between; direction: rtl; }}
            .title-none {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border-right: 4px solid #10b981; }}
            .title-training {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-right: 4px solid #f59e0b; }}
            .title-adv {{ background: rgba(59, 130, 246, 0.15); color: #60a5fa; border-right: 4px solid #3b82f6; }}
            .title-mand {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border-right: 4px solid #ef4444; }}

            /* Job Card */
            .job-card {{ background: #0b1329; border: 1px solid #1e2d4a; border-radius: 10px; padding: 18px; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.25); direction: rtl; text-align: right; }}
            .job-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #1e2d4a; padding-bottom: 8px; direction: rtl; }}
            .job-title {{ font-size: 16.5px; font-weight: bold; color: #38bdf8; text-decoration: none; text-align: right; }}
            
            /* Badges */
            .score-badge {{ background: linear-gradient(135deg, #0284c7, #0369a1); color: white; padding: 4px 10px; border-radius: 14px; font-weight: bold; font-size: 12.5px; display: inline-block; }}
            .license-badge-none {{ background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 6px; }}
            .license-badge-training {{ background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 6px; }}
            .license-badge-adv {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 6px; }}
            .license-badge-mand {{ background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 6px; }}
            
            .details {{ font-size: 13.5px; line-height: 1.6; color: #cbd5e1; direction: rtl; text-align: right; }}
            .summary-box {{ background: #131f37; padding: 10px 12px; border-radius: 6px; margin: 8px 0; border-right: 3px solid #38bdf8; font-size: 13px; color: #e2e8f0; direction: rtl; text-align: right; }}
            .pro-list {{ color: #4ade80; margin: 4px 0; padding-right: 15px; font-size: 13px; direction: rtl; text-align: right; }}
            .gap-list {{ color: #fbbf24; margin: 4px 0; padding-right: 15px; font-size: 13px; direction: rtl; text-align: right; }}
            .btn {{ display: inline-block; background: #0284c7; color: #ffffff !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; margin-top: 10px; text-align: center; border: 1px solid #38bdf8; }}
            .footer {{ background: #0b1329; text-align: center; padding: 14px; font-size: 12px; color: #64748b; border-top: 1px solid #1e2d4a; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>🚁 משרות מובילות בעולם הרחפנים והכטב"ם | עידו גל</h1>
                <p>סיכום יומי מבוסס AI - מחולק לפי דרישות רישיון והכשרת מטיסים</p>
            </div>
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
    """

    def render_job_card(job):
        score = job.get("match_score", 65)
        lic_stat = job.get("license_status", "none")
        lic_note = job.get("license_note_hebrew", "")
        
        if lic_stat == "none":
            badge_html = f'<span class="license-badge-none">🟢 ללא צורך ברישיון מטיס: {lic_note}</span>'
            card_border = "border-right: 5px solid #10b981;"
        elif lic_stat == "training_provided":
            badge_html = f'<span class="license-badge-training">🎓 הכשרה והסמכה ע"ח החברה: {lic_note}</span>'
            card_border = "border-right: 5px solid #f59e0b;"
        elif lic_stat == "advantage":
            badge_html = f'<span class="license-badge-adv">🟡 רישיון כיתרון (לא חובה): {lic_note}</span>'
            card_border = "border-right: 5px solid #3b82f6;"
        else:
            badge_html = f'<span class="license-badge-mand">🔴 רישיון מטיס כדרישת סף: {lic_note}</span>'
            card_border = "border-right: 5px solid #ef4444;"

        return f"""
            <div class="job-card" dir="rtl" style="{card_border} direction: rtl; text-align: right;">
                <div class="job-header" dir="rtl">
                    <span class="score-badge">התאמה: {score}%</span>
                    <a href="{job.get('link', '#')}" class="job-title" target="_blank" dir="rtl">{job.get('title', 'משרה')}</a>
                </div>
                <div class="details" dir="rtl">
                    <div>{badge_html}</div>
                    <p style="margin:4px 0;"><strong>חברה ומיקום:</strong> {job.get('company', '')} | {job.get('location', '')}</p>
                    <div class="summary-box">
                        <strong>תקציר המשרה:</strong> {job.get('summary_hebrew', '')}
                    </div>
                    <p style="margin-bottom:2px; margin-top:8px;"><strong>נקודות חוזק מהניסיון שלך:</strong></p>
                    <div class="pro-list">• {job.get('pros_hebrew', '')}</div>
                    
                    <p style="margin-bottom:2px; margin-top:8px;"><strong>דגשים / דרישות נוספות:</strong></p>
                    <div class="gap-list">• {job.get('gaps_hebrew', '')}</div>
                    
                    <a href="{job.get('link', '#')}" class="btn" target="_blank">צפה במשרה והגש מועמדות &larr;</a>
                </div>
            </div>
        """

    if not evaluated_jobs:
        html += """
        <div dir="rtl" style="text-align:center; padding: 35px; direction: rtl;">
            <p style="font-size:16px; color:#94a3b8;">לא נמצאו משרות רחפנים חדשות שעברו את סף ההתאמה (65%+) היום.</p>
            <p style="font-size:13px; color:#64748b;">הסריקה האוטומטית תמשיך לרוץ בענן מחר ב-07:00 בבוקר!</p>
        </div>
        """
    else:
        # Group 1: None
        if cat_none:
            html += '<div class="section-title title-none">🟢 משרות ללא צורך ברישיון מטיס (מכניקה, אינטגרציה, בקרה, חשמל)</div>'
            for j in cat_none:
                html += render_job_card(j)

        # Group 2: Training Provided
        if cat_training:
            html += '<div class="section-title title-training">🎓 משרות עם הכשרה והסמכה לרישיון מטיס ע"ח החברה</div>'
            for j in cat_training:
                html += render_job_card(j)

        # Group 3: Advantage
        if cat_adv:
            html += '<div class="section-title title-adv">🟡 משרות שבהן רישיון מטיס הוא יתרון בלבד (לא חובה)</div>'
            for j in cat_adv:
                html += render_job_card(j)

        # Group 4: Mandatory
        if cat_mand:
            html += '<div class="section-title title-mand">🔴 משרות הדורשות רישיון מטיס מסחרי קיים כדרישת סף</div>'
            for j in cat_mand:
                html += render_job_card(j)

    html += """
            </div>
            <div class="footer" dir="rtl">
                <p>הודעה זו נשלחה באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_drone_email(subject, html_content, recipient_email):
    """Send email via SMTP."""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_APP_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    if not sender_email or not sender_password:
        print("[-] SENDER_EMAIL or SENDER_APP_PASSWORD missing. Writing preview to sample_drone_report.html...")
        with open("sample_drone_report.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("[+] Preview saved to sample_drone_report.html")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Drone Job Search Automation <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"[+] Drone Jobs Email successfully sent to {recipient_email}!")
        return True
    except Exception as e:
        print(f"[-] Failed to send email: {e}")
        return False

def main():
    print("[+] Starting Drone & UAV Job Search Automation for Ido Gal (Categorized by License Requirements)...")

    # 1. Load seen drone jobs history
    seen_drones = load_seen_drones()
    print(f"[+] Loaded {len(seen_drones)} active drone jobs in 14-day history.")

    # 2. Fetch fresh drone jobs
    raw_jobs = fetch_drone_jobs(seen_drones)
    print(f"[+] Retrieved {len(raw_jobs)} unique fresh drone job postings for analysis.")

    if not raw_jobs:
        print("[!] No new drone jobs found today.")
        return

    # 3. Evaluate with Gemini AI & classify licensing
    evaluated_jobs = evaluate_drone_jobs_with_gemini(raw_jobs)
    print(f"[+] Evaluated {len(evaluated_jobs)} matching drone jobs with Gemini AI.")

    # 4. Save newly sent jobs to history & weekly archive
    if evaluated_jobs:
        save_seen_drones(seen_drones, evaluated_jobs)

    # 5. Build & Dispatch HTML Email
    html_content = build_drone_html_email(evaluated_jobs)
    send_drone_email("🚁 משרות מובילות בעולם הרחפנים והכטב\"ם (מחולק לפי דרישות רישיון) | עידו גל", html_content, "idogal0210@gmail.com")

if __name__ == "__main__":
    main()
