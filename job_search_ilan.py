import os
import sys
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Candidate Profile Context for AI Evaluation – ILAN GAL
ILAN_CV_SUMMARY = """
Name: Ilan Gal (אילן גל)
Email: ilangal46@gmail.com | Phone: 050-7010198 | Location: Or Aqiva (אור עקיבא), Israel.

GEOGRAPHIC PREFERENCES:
- Israel: Full availability.
- Africa & Europe: ONLY with Israeli companies or subsidiaries of Israeli companies.
- FIFO: Open ONLY with excellent terms (full relocation or high salary).

Degree / Qualifications:
- Certified HSE Manager (מנהל מוסמך בריאות ובטיחות), Ministry of Labor, Israel (2013).
- Certified Work Inspector (מפקח עבודה), Ministry of Labor, Israel (2013).
- International School, Hamburg, Germany.
- NOT a B.Sc./Academic degree holder – Exclude jobs requiring academic degree only.

Professional Experience (13+ years):
- Senior Operations & Interface Manager at Noga – Israel System Operator (נוגה שירותי ומרכז S.O.S) (2022–2026, Hadera, Israel):
  Full operational management, cross-functional coordination, managing teams of 50+ workers, budget management,
  maintaining critical energy infrastructure, supplier management, safety & regulatory compliance.

- Sales Operations Manager at Friedlander Vehicle Agency (2018–2022, Haifa, Israel):
  Sales team management, fleet operations, logistics coordination.

- Greenfield Operations Manager (2018, South Africa):
  Greenfield construction planning and execution for energy/mining projects,
  FIFO operations management in Africa, cross-cultural team leadership.

- Turnkey Project Manager (2017, West Africa):
  End-to-end Turnkey project delivery, vendor management, site commissioning.

- Senior Operation Manager at Telemenia (2013–2016, West Africa):
  Full P&L responsibility, logistics & supply chain for remote African operations,
  asset management, local team recruitment & training, safety compliance.

- IDF Navy Combat Veteran (חיל הים – צה"ל).

KEY STRENGTHS:
⭐ 13+ years managing complex operational systems in energy & infrastructure.
⭐ Proven Greenfield & Turnkey project delivery (Africa).
⭐ HSE certified – safety & regulatory expertise.
⭐ International operations leadership (Africa, Europe, Israel).
⭐ Managing 50+ employee teams, budgets, suppliers, and cross-functional interfaces.
⭐ Logistics, supply chain, and fleet management.

HIGH PRIORITY TARGET SECTORS & COMPANIES:
⭐ Energy Infrastructure: חברת החשמל, OPC Energy, Dorad, Noga, Energean, NewMed Energy.
⭐ Renewable / Solar / Wind: Enlight, Doral, Nofar, Energix, EDF Renewables, Shikun & Binui Energy.
⭐ EPC Contractors: אלקטרה, אפקון, אלקו, מנרב, שפיר הנדסה, Ashtrom.
⭐ Heavy Industry & Mining: ICL (כיל), Dead Sea Works, בז"ן, IDE Technologies.
⭐ International Israeli Ops: Shikun & Binui International, Ashtrom International, Electra Global.
⭐ Logistics & Supply Chain: צים, DHL Israel, DB Schenker Israel.
⭐ Water & Infrastructure: מקורות, נתיבי ישראל, חברת נמלי ישראל.

EXCLUDED / REJECTED:
❌ Jobs requiring ONLY B.Sc./Academic degree where practical experience is NOT accepted.
❌ FIFO jobs without full relocation or competitive compensation.
❌ Junior/entry-level positions.
❌ Pure software/IT/coding roles with no operations component.

Target Roles:
1. Senior Operations Manager / מנהל תפעול בכיר.
2. Project Manager (Greenfield / Turnkey / EPC) / מנהל פרויקטים.
3. Interface Manager / מנהל ממשקים.
4. HSE Manager / מנהל בטיחות.
5. Site Manager / מנהל שטח / מנהל אתר.
6. Maintenance Manager / מנהל תחזוקה.
7. Logistics / Supply Chain Manager / מנהל לוגיסטיקה ושרשרת אספקה.

STRICT FILTERING RULES:
- Boost match score (+10%) for target companies (Enlight, Doral, OPC, Noga, אלקטרה, אפקון, ICL, etc.).
- Reject B.Sc./Academic degree ONLY jobs.
- Reject junior/entry-level positions.
- Reject pure IT/software roles.
- Minimum Match Score threshold: 65%.
"""

def fetch_jobs_for_ilan():
    """Fetch potential job leads targeting Israel & international operations/management roles for Ilan Gal."""
    jobs = []
    print("[+] [ILAN] Fetching live job listings from LinkedIn Israel & international feeds...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # Keywords tailored for Ilan's profile
    keywords = [
        "מנהל תפעול בכיר",
        "מנהל פרויקטים הנדסה",
        "מנהל שטח",
        "Site Manager Israel",
        "Operations Manager Israel",
        "HSE Manager Israel",
        "מנהל ממשקים",
        "מנהל לוגיסטיקה",
        "Greenfield Project Manager",
        "מנהל תחזוקה",
        "EPC Project Manager",
        "Supply Chain Manager Israel"
    ]

    for kw in keywords:
        try:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={requests.utils.quote(kw)}&location=Israel&start=0"
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
                        link = link_elem.get("href", "").split("?")[0]
                        loc = loc_elem.text.strip() if loc_elem else "ישראל"

                        jobs.append({
                            "title": f"{company} - {title}",
                            "snippet": f"משרה בחברת {company} במיקום {loc}. דרישות תפקיד: {title}",
                            "link": link
                        })
        except Exception as e:
            print(f"[-] [ILAN] LinkedIn fetch error for '{kw}': {e}")

    # Deduplicate by link
    seen_links = set()
    unique_jobs = []
    for job in jobs:
        if job["link"] not in seen_links:
            seen_links.add(job["link"])
            unique_jobs.append(job)

    print(f"[+] [ILAN] Successfully fetched {len(unique_jobs)} unique live jobs.")
    return unique_jobs


def evaluate_jobs_with_gemini(job_list):
    """Use Gemini AI to analyze job fit against Ilan Gal's CV with strict filters."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("[-] [ILAN] GEMINI_API_KEY missing.")
        return []

    client = genai.Client(api_key=gemini_key)
    evaluated_jobs = []

    prompt = f"""
You are an expert AI Career Advisor evaluating jobs for Ilan Gal (אילן גל).

CANDIDATE CV PROFILE & RULES:
{ILAN_CV_SUMMARY}

JOB POSTINGS TO EVALUATE:
{json.dumps(job_list, ensure_ascii=False, indent=2)}

Filter and evaluate the jobs strictly according to the candidate profile and rules.
Return a JSON array of objects with the following schema for jobs matching score >= 65%:
[
  {{
    "title": "שם התפקיד והחברה",
    "link": "URL link",
    "match_score": 85, (integer 65-100),
    "company": "שם החברה",
    "location": "מיקום (ישראל / אפריקה / אירופה / Remote)",
    "summary_hebrew": "תקציר ממוקד בעברית של 2 שורות בלבד על התפקיד והאחריות",
    "pros_hebrew": "2-3 נקודות חוזק בולטות להתאמה מהניסיון של אילן",
    "gaps_hebrew": "דרישות חובה או פערים לתשומת לב (אם קיימים)"
  }}
]

CRITICAL RULES:
- ONLY include jobs with match_score >= 65.
- Reject B.Sc./Academic degree ONLY jobs where practical experience is strictly rejected.
- Reject junior/entry-level positions.
- Reject pure IT/software roles with no operations component.
- For international jobs: ONLY include if company is Israeli or an Israeli subsidiary.
- Maximum 5 best jobs returned.
- Return ONLY valid raw JSON array inside backticks.
"""

    for model_name in ['gemini-flash-latest', 'gemini-2.0-flash', 'gemini-1.5-flash']:
        try:
            print(f"[+] [ILAN] Evaluating with model: {model_name}...")
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
                print(f"[+] [ILAN] Successfully evaluated {len(evaluated_jobs)} matching jobs.")
                break
        except Exception as e:
            print(f"[-] [ILAN] Model {model_name} error: {e}")

    evaluated_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    return evaluated_jobs[:5]

def build_html_email(evaluated_jobs):
    """Build a refined HTML email summary with explicit RTL right-to-left layout for Gmail – for Ilan Gal."""
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f6f9; margin: 0; padding: 20px; color: #1e293b; direction: rtl; text-align: right; }}
            .container {{ max-width: 650px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%); color: #ffffff; padding: 25px; text-align: center; direction: rtl; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; color: #ffffff; }}
            .header p {{ margin: 6px 0 0 0; opacity: 0.9; font-size: 14px; color: #d1fae5; }}
            .content {{ padding: 22px; direction: rtl; text-align: right; }}
            .job-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-right: 5px solid #059669; border-radius: 8px; padding: 18px; margin-bottom: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); direction: rtl; text-align: right; }}
            .job-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; direction: rtl; }}
            .job-title {{ font-size: 17px; font-weight: bold; color: #1e293b; text-decoration: none; text-align: right; }}
            .score-badge {{ background: #059669; color: white; padding: 4px 10px; border-radius: 16px; font-weight: bold; font-size: 13px; display: inline-block; margin-left: 10px; }}
            .details {{ font-size: 14px; line-height: 1.6; color: #334155; direction: rtl; text-align: right; }}
            .summary-box {{ background: #f0fdf4; padding: 10px 12px; border-radius: 6px; margin: 10px 0; border-right: 3px solid #059669; font-size: 13.5px; direction: rtl; text-align: right; }}
            .pro-list {{ color: #047857; margin: 4px 0; padding-right: 15px; font-size: 13.5px; direction: rtl; text-align: right; }}
            .gap-list {{ color: #b45309; margin: 4px 0; padding-right: 15px; font-size: 13.5px; direction: rtl; text-align: right; }}
            .btn {{ display: inline-block; background: #059669; color: #ffffff !important; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13.5px; margin-top: 12px; text-align: center; }}
            .footer {{ background: #f0fdf4; text-align: center; padding: 14px; font-size: 12px; color: #64748b; border-top: 1px solid #d1fae5; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>🎯 משרות מותאמות אישית (תאימות 65%+) | אילן גל</h1>
                <p>סיכום אוטומטי יומי מבוסס AI - {len(evaluated_jobs)} משרות נבחרות</p>
            </div>
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
    """

    if not evaluated_jobs:
        html += """
        <div dir="rtl" style="text-align:center; padding: 30px; direction: rtl;">
            <p style="font-size:16px; color:#64748b;">לא נמצאו משרות חדשות שעברו את סף ההתאמה (65%+) היום.</p>
            <p style="font-size:13px; color:#94a3b8;">הסריקה תמשיך לרוץ אוטומטית בענן מחר ב-07:00 בבוקר!</p>
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
                <p>הודעה זו נשלחה באופן אוטומטי ע"י מערכת Job Search Automation עבור אילן גל</p>
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
        print("[-] [ILAN] SENDER_EMAIL or SENDER_APP_PASSWORD missing. Printing HTML output to file for preview...")
        with open("/Users/ido/.gemini/antigravity/scratch/job_search_automation/sample_report_ilan.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("[+] [ILAN] Preview saved to sample_report_ilan.html")
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
        print(f"[+] [ILAN] Email successfully sent to {recipient_email}!")
        return True
    except Exception as e:
        print(f"[-] [ILAN] Failed to send email: {e}")
        return False

def main():
    print("[+] Starting Job Search Automation for ILAN GAL...")

    # 1. Fetch Job Leads
    raw_jobs = fetch_jobs_for_ilan()
    print(f"[+] [ILAN] Retrieved {len(raw_jobs)} job postings for analysis.")

    if not raw_jobs:
        print("[!] [ILAN] No job leads found today.")
        return

    # 2. Evaluate with Gemini AI
    evaluated_jobs = evaluate_jobs_with_gemini(raw_jobs)
    print(f"[+] [ILAN] Evaluated {len(evaluated_jobs)} jobs with Gemini AI.")

    # 3. Build & Dispatch HTML Email Report
    html_content = build_html_email(evaluated_jobs)
    send_email("🎯 משרות מותאמות אישית עבור אילן גל - סיכום יומי", html_content, "ilangal46@gmail.com")

if __name__ == "__main__":
    main()
