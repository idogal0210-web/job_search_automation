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

# Load environment variables from .env if present
load_dotenv()

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "seen_jobs.json")
RETENTION_DAYS = 14

def load_seen_jobs():
    """Load previously sent jobs and prune any older than 14 days."""
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
        print(f"[-] Error reading seen_jobs.json: {e}")
        return {}

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "weekly_archive.json")

DAY_NAMES = {
    0: "יום ב'",
    1: "יום ג'",
    2: "יום ד'",
    3: "יום ה'",
    4: "יום ו'",
    5: "יום שבת",
    6: "יום א'"
}

def save_seen_jobs(seen_dict, newly_sent_jobs):
    """Save newly sent jobs into seen_jobs.json and weekly_archive.json."""
    now = datetime.now()
    now_iso = now.isoformat()
    today_str = now.strftime("%Y-%m-%d")
    day_name = DAY_NAMES.get(now.weekday(), "")

    for job in newly_sent_jobs:
        link = job.get("link", "").strip()
        if link:
            seen_dict[link] = now_iso

    # 1. Save seen_jobs.json
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_dict, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated {HISTORY_FILE} with {len(newly_sent_jobs)} newly sent jobs.")
    except Exception as e:
        print(f"[-] Error writing seen_jobs.json: {e}")

    # 2. Append to weekly_archive.json
    archive_list = []
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                archive_list = json.load(f)
        except Exception:
            archive_list = []

    # Filter out archive entries older than 14 days
    cutoff_date = (now - timedelta(days=14)).strftime("%Y-%m-%d")
    archive_list = [j for j in archive_list if j.get("date", "") >= cutoff_date]

    # Add new jobs
    for job in newly_sent_jobs:
        archive_list.append({
            "date": today_str,
            "day_name": day_name,
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "match_score": job.get("match_score", 0),
            "sector": job.get("location", "ישראל"),
            "summary": job.get("summary_hebrew", ""),
            "pros": job.get("pros_hebrew", ""),
            "gaps": job.get("gaps_hebrew", ""),
            "link": job.get("link", "")
        })

    try:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive_list, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated {ARCHIVE_FILE} with rich metadata for weekly digest.")
    except Exception as e:
        print(f"[-] Error writing weekly_archive.json: {e}")

# Candidate Profile Context for AI Evaluation - Extracted Directly from Updated CV (Aug 2026)
IDO_CV_SUMMARY = """
Name: Ido Gal (עידו גל)
Title: Gas Controller & Energy Systems Operations | Practical Mechanical Engineer | Real-Time Control & Supply Continuity
Location: Tel Aviv | Phone: 052-632-8886 | Email: idogal0210@gmail.com | LinkedIn: www.linkedin.com/in/ido-g

Education & Certifications:
- Practical Mechanical Engineer, Natural Gas & Green Energy (הנדסאי מכונות, התמחות בגז טבעי ובאנרגיה ירוקה), Ruppin Academic Center (2024). NOT a B.Sc. Engineer!
- Certified Electrician Studies (לימודי חשמלאי מוסמך), Ruppin Academic Center (Expected completion 2026).

Technical Tools & Systems:
- Advanced Excel: Analysis, formulas, operational reports, automation.
- SAP in organizational environments.
- Microsoft 365 Copilot, Gemini: Practical application in workflows.
- Operational data analysis and reporting, supply quantity tracking and control.
- Shift reports and handover documentation.
- AI and automation implementation in workflows.

Core Skills:
- Real-time gas and energy operations control 24/7.
- Pressure, flow-rate and quantity monitoring.
- Nomination / Re-nomination handling and supply allocations.
- Operational event and deviation response in safety-critical environments.
- Independent decision-making under pressure (sole focal point on night shifts).
- Cross-functional and external coordination (offshore platform, INGL/נתג"ז, commercial teams, strategic customers).
- Operational continuity and prioritization.
- Data analysis, reporting, process improvement, automation.
- Employee training, mentoring, and leadership.

Languages:
- Hebrew: Native.
- English: Full professional proficiency.

Professional Experience:
1. Energean Israel Ltd | Gas Controller | 2022–Present:
   - Continuous operational control of natural gas supply to strategic customers (power stations, major industrial plants) 24/7.
   - Real-time monitoring of pressures, flow rates, supply quantities, and operational data; rapid deviation identification.
   - Nomination and Re-nomination handling, reviewing quantity changes and updating gas allocations.
   - Independent coordination between offshore platform, INGL, commercial department, and customers.
   - Translating commercial requirements into operational execution as the independent focal point on night shifts.
   - Making real-time decisions under pressure in response to demand changes and unplanned events.
   - Producing reports, supply data, and operational documentation for control, analysis, reporting, and shift handover.
   - Implementing Excel, Microsoft 365 Copilot, and Gemini solutions to reduce manual work, shorten execution time, and improve consistency.
2. Vulcan / Energean Israel Ltd | Security Officer, Strategic Energy Facility | 2020–2022:
   - Secured sensitive natural gas infrastructure in a regulated strategic energy facility under strict safety, security, and access-control procedures.
   - Coordinated with operational and professional stakeholders while supporting site continuity, alertness, and rapid event response.
3. Sales Team Leader & Sales Trainer | International Activity | 2015–2020:
   - Recruited, trained, and supported sales reps in international markets, mainly the U.S. and Israel–Germany activity.
   - Led learning, adaptation, and performance-improvement processes in dynamic multicultural environments.
4. MER Group | PV Solar Systems Installer | 2010–2012:
   - Installed, wired, and assisted with initial commissioning of photovoltaic systems; hands-on renewable energy construction.

Military Service:
- Nahal Reconnaissance Unit (סיירת נח"ל) | Demolitions & Combat Engineering (חבלה והנדסה קרבית) | 2012–2015:
  - Combat soldier, commander, and career service member leading the unit's demolitions field.
  - Certifications: Rifleman 08 (רובאי 08) and Demolitions & Combat Engineering 07 (הסמכת פלס/חבלה 07).

TARGET SECTORS & COMPANIES (+10% BOOST):
⭐ Solar & Green Energy: Enlight, Doral, Nofar, Energix, EDF Renewables Israel, Shikun & Binui Energy, Afcon, Enerpoint.
⭐ Energy Tech / AI: SolarEdge, Augury, BrightSource, Driivz, REplace, Siemens Energy Israel, Honeywell Israel, ABB Israel, Brightmerge.
⭐ Natural Gas & Power: NewMed Energy, OPC Energy, Dorad Energy, Edeltech.
⭐ Energy Storage (BESS) & Tech: Nostromo, Brenmiller, StoreDot, Electreon, H2Pro, GenCell.
⭐ Heavy Industry & Infrastructure: ICL (כיל), חברת החשמל, מקורות, IDE Technologies, בז"ן.

EXCLUDED / REJECTED COMPANIES & SHIFTS:
❌ Energean (אנרג'יאן) - EXCLUDE per candidate request (current employer).
❌ נתג"ז (INGL) - EXCLUDE per candidate request.
❌ Chevron Israel (שברון) - EXCLUDE per candidate request (2-week shift model).
❌ Raycatch - EXCLUDE.
❌ FIFO / remote shift jobs abroad without full relocation.
❌ Jobs requiring ONLY B.Sc. Engineer degree where Practical Engineer (הנדסאי) is NOT accepted.

STRICT FILTERING RULES:
- Minimum Match Score threshold: 65%.
"""

def fetch_jobs_google_search(seen_jobs_dict):
    """Fetch potential job leads across a broad spectrum of keywords, target companies, and pagination."""
    jobs = []
    print("[+] Fetching live job listings from LinkedIn Israel & Israeli Job Feeds...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # 1. Broad role & skill keywords
    role_keywords = [
        "הנדסאי מכונות",
        "בקר גז",
        "תפעול אנרגיה",
        "אנרגיה סולארית",
        "הנדסאי אחזקה",
        "טכנאי שטח",
        "Field Service Engineer",
        "Plant Operator Israel",
        "Gas Controller",
        "הנדסאי תהליך",
        "Process Technician",
        "BESS Israel",
        "אגירת אנרגיה",
        "Solar Project Engineer",
        "Commissioning Engineer",
        "Site Manager Energy",
        "SCADA Operator Israel",
        "מנהל עבודה סולארי",
        "מנהל פרויקטים תשתיות",
        "תפעול חדר בקרה"
    ]

    # 2. Specific Target Companies Searches
    company_keywords = [
        "Enlight Renewable Energy",
        "Doral Energy",
        "SolarEdge Israel",
        "Nofar Energy",
        "Energix Renewable Energies",
        "EDF Renewables Israel",
        "Siemens Energy Israel",
        "OPC Energy",
        "Dorad Energy",
        "ICL Group Israel",
        "Afcon Holdings",
        "Electra Energy",
        "Augury Israel",
        "StoreDot Israel",
        "IDE Technologies",
        "Shikun & Binui Energy"
    ]

    all_queries = []
    # Primary role queries with pagination (start=0 and start=25)
    for kw in role_keywords:
        all_queries.append((kw, 0))
        all_queries.append((kw, 25))

    # Company queries (start=0)
    for comp in company_keywords:
        all_queries.append((comp, 0))

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
                        
                        # 1. Skip already seen jobs in the last 14 days
                        if link in seen_jobs_dict or link in seen_links_current_run:
                            continue

                        # 2. Exclude Energean, INGL, Chevron, Raycatch
                        if any(ex in company.lower() or ex in title.lower() for ex in ["energean", "אנרג'יאן", "ingl", "נתג", "chevron", "שברון", "raycatch"]):
                            continue
                            
                        seen_links_current_run.add(link)
                        jobs.append({
                            "title": f"{company} - {title}",
                            "snippet": f"משרה בחברת {company} במיקום {loc}. דרישות תפקיד: {title}",
                            "link": link
                        })
        except Exception as e:
            # Continue on error
            pass

    print(f"[+] Successfully fetched {len(jobs)} FRESH candidate jobs (after 14-day history filtering & deduplication).")
    return jobs


def evaluate_jobs_with_gemini(job_list):
    """Use Gemini AI to analyze job fit against Ido Gal's CV with strict filters."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("[-] GEMINI_API_KEY missing.")
        return []

    client = genai.Client(api_key=gemini_key)
    evaluated_jobs = []

    # Send up to 80 candidate jobs to Gemini in one prompt for efficiency
    candidate_batch = job_list[:80]

    prompt = f"""
You are an expert AI Career Advisor evaluating jobs for Ido Gal.

CANDIDATE CV PROFILE & RULES:
{IDO_CV_SUMMARY}

JOB POSTINGS TO EVALUATE:
{json.dumps(candidate_batch, ensure_ascii=False, indent=2)}

Filter and evaluate the jobs strictly according to the candidate profile and rules.
Return a JSON array of objects with the following schema for jobs matching score >= 65%:
[
  {{
    "title": "שם התפקיד והחברה",
    "link": "URL link",
    "match_score": 85, (integer 65-100),
    "company": "שם החברה",
    "location": "מיקום (ישראל / רילוקיישן / Remote)",
    "summary_hebrew": "תקציר ממוקד בעברית של 2 שורות בלבד על התפקיד והאחריות",
    "pros_hebrew": "2-3 נקודות חוזק בולטות להתאמה מהניסיון של עידו",
    "gaps_hebrew": "דרישות חובה או פערים לתשומת לב (אם קיימים)"
  }}
]

CRITICAL RULES:
- ONLY include jobs with match_score >= 65.
- Reject B.Sc. Engineer ONLY jobs where Practical Engineer (הנדסאי) is strictly rejected.
- Reject Energean, INGL, Chevron Israel, Raycatch, and FIFO shifts without relocation.
- Maximum 5 best jobs returned.
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
                print(f"[+] Evaluating with model: {model_name} (attempt {attempt+1})...")
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
                    print(f"[+] Successfully evaluated {len(evaluated_jobs)} matching jobs.")
                    break
            except Exception as e:
                print(f"[-] Model {model_name} error: {e}")
                time.sleep(2)
        if evaluated_jobs:
            break

    evaluated_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return evaluated_jobs[:5]

def build_html_email(evaluated_jobs):
    """Build a refined HTML email summary with explicit RTL right-to-left layout for Gmail."""
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #1e293b; direction: rtl; text-align: right; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #ffffff; padding: 25px; text-align: center; direction: rtl; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; }}
            .header p {{ margin: 6px 0 0 0; opacity: 0.9; font-size: 14px; color: #e2e8f0; }}
            .content {{ padding: 22px; direction: rtl; text-align: right; }}
            .job-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-right: 5px solid #2563eb; border-radius: 8px; padding: 18px; margin-bottom: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); direction: rtl; text-align: right; }}
            .job-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; direction: rtl; }}
            .job-title {{ font-size: 17px; font-weight: bold; color: #1e293b; text-decoration: none; text-align: right; }}
            .score-badge {{ background: #10b981; color: white; padding: 4px 10px; border-radius: 16px; font-weight: bold; font-size: 13px; display: inline-block; margin-left: 10px; }}
            .details {{ font-size: 14px; line-height: 1.6; color: #334155; direction: rtl; text-align: right; }}
            .summary-box {{ background: #f8fafc; padding: 10px 12px; border-radius: 6px; margin: 10px 0; border-right: 3px solid #64748b; font-size: 13.5px; direction: rtl; text-align: right; }}
            .pro-list {{ color: #047857; margin: 4px 0; padding-right: 15px; font-size: 13.5px; direction: rtl; text-align: right; }}
            .gap-list {{ color: #b45309; margin: 4px 0; padding-right: 15px; font-size: 13.5px; direction: rtl; text-align: right; }}
            .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13.5px; margin-top: 12px; text-align: center; }}
            .footer {{ background: #f8fafc; text-align: center; padding: 14px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>🎯 משרות מותאמות אישית (תאימות 65%+) | עידו גל</h1>
                <p>סיכום אוטומטי יומי מבוסס AI - {len(evaluated_jobs)} משרות נבחרות חדשות</p>
            </div>
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
    """
    
    if not evaluated_jobs:
        html += """
        <div class="job-card" dir="rtl" style="direction: rtl; text-align: center; padding: 25px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h3 style="color: #1e3c72; margin-top: 0;">✅ הסריקה היומית הושלמה בהצלחה</h3>
            <p style="font-size: 15px; color: #475569; line-height: 1.6; margin: 10px 0;">
                כלל מילות המפתח וחברות היעד בתחומי האנרגיה, הגז הטבעי, BESS והבקרה נסרקו הבוקר.<br>
                לא אותרו משרות חדשות שטרם נשלחו ב-14 הימים האחרונים שעברו את סף ההתאמה (65%+).
            </p>
            <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">
                הסריקה האוטומטית הבאה תתבצע מחר ב-06:35 בבוקר בענן.
            </p>
        </div>
        """
    else:
        for job in evaluated_jobs:
            score = job.get("match_score", 65)
            
            html += f"""
                <div class="job-card" dir="rtl" style="direction: rtl; text-align: right;">
                    <div class="job-header" dir="rtl" style="direction: rtl; text-align: right;">
                        <span class="score-badge">התאמה: {score}%</span>
                        <a href="{job.get('link', '#')}" class="job-title" target="_blank" dir="rtl" style="direction: rtl; text-align: right;">{job.get('title', 'משרה')}</a>
                    </div>
                    <div class="details" dir="rtl" style="direction: rtl; text-align: right;">
                        <p style="margin:4px 0; direction: rtl; text-align: right;"><strong>חברה ומיקום:</strong> {job.get('company', '')} | {job.get('location', '')}</p>
                        <div class="summary-box" dir="rtl" style="direction: rtl; text-align: right;">
                            <strong>תקציר המשרה:</strong> {job.get('summary_hebrew', '')}
                        </div>
                        <p style="margin-bottom:2px; margin-top:8px; direction: rtl; text-align: right;"><strong>נקודות חוזק מהניסיון שלך:</strong></p>
                        <div class="pro-list" dir="rtl" style="direction: rtl; text-align: right;">• {job.get('pros_hebrew', '')}</div>
                        
                        <p style="margin-bottom:2px; margin-top:8px; direction: rtl; text-align: right;"><strong>דגשים / דרישות נוספות:</strong></p>
                        <div class="gap-list" dir="rtl" style="direction: rtl; text-align: right;">• {job.get('gaps_hebrew', '')}</div>
                        
                        <a href="{job.get('link', '#')}" class="btn" target="_blank" dir="rtl" style="direction: rtl;">צפה במשרה והגש מועמדות &larr;</a>
                    </div>
                </div>
            """

    html += """
            </div>
            <div class="footer" dir="rtl" style="direction: rtl; text-align: center;">
                <p>הודעה זו נשלחה באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html



def send_email(subject, html_content, recipient_email):
    """Send email via SMTP."""
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_APP_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    if not sender_email or not sender_password:
        print("[-] SENDER_EMAIL or SENDER_APP_PASSWORD missing. Printing HTML output to file for preview...")
        report_path = os.path.join(os.path.dirname(__file__), "sample_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Preview saved to {report_path}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Job Search Automation <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"[+] Email successfully sent to {recipient_email}!")
        return True
    except Exception as e:
        print(f"[-] Failed to send email: {e}")
        return False

def expand_energy_queries_with_ai(client, seen_jobs_dict):
    """Muscle 3: Dynamically generate and execute expanded queries if daily results are low."""
    print("[+] Muscle 3 Activated: Generating dynamic energy queries via Gemini AI...")
    prompt = f"""
Given the candidate profile for Ido Gal (Practical Mechanical Engineer, Natural Gas & Solar Energy, Control Room Operator, Electrician student, ex-combat demolitions commander):
Generate 4 novel, specific search keywords in Hebrew or English to discover hidden energy, infrastructure, commissioning, or control room jobs in Israel (e.g. niche EPC contractors, commissioning tech, biogas, microgrids, industrial telemetry).
Return ONLY a raw JSON array of 4 strings, e.g. ["query 1", "query 2", "query 3", "query 4"].
"""
    expanded_jobs = []
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        queries = json.loads(text.strip())
        print(f"[+] AI Generated Dynamic Queries: {queries}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8"
        }
        for kw in queries:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location=Israel&start=0"
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for card in soup.find_all("li"):
                    title_elem = card.find("h3", class_="base-search-card__title")
                    comp_elem = card.find("h4", class_="base-search-card__subtitle")
                    link_elem = card.find("a", class_="base-card__full-link")
                    if title_elem and link_elem:
                        link = link_elem.get("href", "").split("?")[0].strip()
                        comp = comp_elem.text.strip() if comp_elem else ""
                        title = title_elem.text.strip()
                        if link and link not in seen_jobs_dict:
                            expanded_jobs.append({
                                "title": f"{comp} - {title}",
                                "snippet": f"{comp} - {title}",
                                "link": link
                            })
    except Exception as e:
        print(f"[-] Query expansion fallback: {e}")
    return expanded_jobs

def main():
    print("[+] Starting Job Search Automation for Ido Gal (with 14-Day History Deduplication)...")
    
    # 1. Load seen jobs history (14 days window)
    seen_jobs_dict = load_seen_jobs()
    print(f"[+] Loaded {len(seen_jobs_dict)} active jobs in 14-day history.")

    # 2. Fetch Fresh Job Leads (Standard Google/LinkedIn Feeds)
    raw_jobs = fetch_jobs_google_search(seen_jobs_dict)
    print(f"[+] Retrieved {len(raw_jobs)} unique fresh job postings for analysis.")

    # 3. Muscle 2: Fetch Direct ATS Jobs (Comeet / Career Portals)
    try:
        from ats_scraper import get_energy_ats_jobs
        ats_jobs = get_energy_ats_jobs()
        added_ats = 0
        for aj in ats_jobs:
            link = aj.get("link", "").strip()
            if link and link not in seen_jobs_dict:
                raw_jobs.append(aj)
                added_ats += 1
        print(f"[+] Muscle 2: Added {added_ats} direct ATS jobs from company portals.")
    except Exception as e:
        print(f"[-] ATS scraper note: {e}")

    # 4. Evaluate with Gemini AI
    evaluated_jobs = []
    if raw_jobs:
        evaluated_jobs = evaluate_jobs_with_gemini(raw_jobs)
        print(f"[+] Evaluated {len(evaluated_jobs)} matching jobs with Gemini AI.")

    # 5. Muscle 3: Autonomous Query Expansion if few results found
    if len(evaluated_jobs) < 2:
        print("[!] Low yield detected. Activating Muscle 3 (Autonomous Query Expansion)...")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                client = genai.Client(api_key=gemini_key)
                expanded_raw = expand_energy_queries_with_ai(client, seen_jobs_dict)
                if expanded_raw:
                    extra_eval = evaluate_jobs_with_gemini(expanded_raw)
                    for ej in extra_eval:
                        if ej.get("link") not in [x.get("link") for x in evaluated_jobs]:
                            evaluated_jobs.append(ej)
                    print(f"[+] Muscle 3 added {len(extra_eval)} new matching jobs.")
            except Exception as e:
                print(f"[-] Query expansion error: {e}")

    # 6. Save newly sent jobs to history & weekly archive
    if evaluated_jobs:
        save_seen_jobs(seen_jobs_dict, evaluated_jobs)
    else:
        print("[!] No fresh jobs found today. Sending daily status confirmation email.")

    # 7. Build & Dispatch HTML Email Report (always dispatched so user gets daily report)
    html_content = build_html_email(evaluated_jobs)
    send_email("🎯 משרות מותאמות אישית עבור עידו גל - סיכום יומי", html_content, "idogal0210@gmail.com")

if __name__ == "__main__":
    main()
