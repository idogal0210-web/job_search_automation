import os
import sys
import json
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

try:
    from src.interactive_app_builder import build_and_save_docs_app
except ImportError:
    from interactive_app_builder import build_and_save_docs_app

DATA_DIR = os.path.join(BASE_DIR, "data")
ARCHIVE_FILE = os.path.join(DATA_DIR, "weekly_archive.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "weekly_archive.json")
REJECTED_JOBS_FILE = os.path.join(DATA_DIR, "rejected_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "rejected_jobs.json")
SAVED_JOBS_FILE = os.path.join(DATA_DIR, "saved_jobs.json") if os.path.exists(DATA_DIR) else os.path.join(BASE_DIR, "saved_jobs.json")

def load_rejected_job_links():
    if not os.path.exists(REJECTED_JOBS_FILE):
        return set()
    try:
        with open(REJECTED_JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data if isinstance(data, list) else data.keys())
    except Exception:
        return set()

EXCLUDED_COMPANIES = [
    "energean", "אנרג'יאן", "נתג\"ז", "נתגז", "ingl", "chevron", "שברון", "raycatch", "רייקאץ'"
]

def load_weekly_jobs():
    """
    Load all valid jobs from past 7 days from weekly_archive.json:
    - Includes ALL jobs that were not removed/rejected (rejected_jobs.json, is_removed, status=='rejected')
    - Excludes strictly forbidden companies (Energean, INGL, Chevron, Raycatch)
    - Enforces passing score threshold (60+ energy, 70+ drones/defense)
    - Deduplicates by job link so each position appears once
    """
    if not os.path.exists(ARCHIVE_FILE):
        return []
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        rejected_set = load_rejected_job_links()
        
        seen_links = set()
        weekly_jobs = []
        for j in jobs:
            link = j.get("link", "")
            if not link or link in seen_links:
                continue

            # Check date (past 7 days)
            if j.get("date", "") < cutoff_date:
                continue

            # Check user rejection
            if link in rejected_set or j.get("is_removed") or j.get("status") == "rejected":
                continue

            # Check strictly excluded companies
            comp = j.get("company", "").lower()
            title = j.get("title", "").lower()
            if any(ex in comp or ex in title for ex in EXCLUDED_COMPANIES):
                continue

            # Check threshold
            is_drone = j.get("sector_key") in ["drones", "cuas", "avionics"]
            threshold = 70 if is_drone else 60
            if j.get("match_score", 0) < threshold:
                continue

            seen_links.add(link)
            weekly_jobs.append(j)

        return weekly_jobs
    except Exception as e:
        print(f"[-] Error loading weekly jobs: {e}")
        return []

def build_weekly_email_html(jobs, dashboard_url):
    """
    Build clean 3-4 color palette Saturday Weekly Summary HTML.
    Palette: Navy #0f172a, Muted Slate #475569, Accent Blue #0284c7, Success Green #16a34a.
    """
    now_str = datetime.now().strftime("%d.%m.%Y")
    
    seen_links = set()
    unique_jobs = []
    for j in jobs:
        link = j.get("link", "")
        if link not in seen_links:
            seen_links.add(link)
            unique_jobs.append(j)

    sorted_by_score = sorted(unique_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    top_3_picks = sorted_by_score[:3]

    sectors = {
        "energy": {"title": "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA", "jobs": []},
        "drones": {"title": "🚁 רחפנים, כטב\"ם אוטונומי ורובוטיקה", "jobs": []},
        "cuas": {"title": "🛡️ מערכות הגנת C-UAS וביטחון", "jobs": []},
        "avionics": {"title": "📡 מטע\"דים, אלקטרו-אופטיקה ואוויוניקה", "jobs": []}
    }

    for j in unique_jobs:
        sec_key = j.get("sector_key", "energy")
        if sec_key not in sectors:
            sec_key = "energy"
        sectors[sec_key]["jobs"].append(j)

    top_3_html = ""
    if top_3_picks:
        top_items = ""
        for idx, pick in enumerate(top_3_picks, 1):
            top_items += f"""
            <div style="padding: 12px; margin-bottom: 8px; background-color: #1e293b; border-radius: 8px; border-right: 4px solid #10b981; border: 1px solid #334155;">
                <div style="font-weight: bold; color: #f8fafc; font-size: 15px;">{idx}. {pick.get('company')} – {pick.get('title')}</div>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">
                    <span style="color: #34d399; font-weight: bold;">{pick.get('match_score')}% התאמה</span> | {pick.get('sector')} &nbsp;&nbsp;
                    <a href="{pick.get('link')}" style="color: #38bdf8; text-decoration: underline; font-weight: bold;">הגש מועמדות למשרה ↗</a>
                </div>
            </div>
            """
        top_3_html = f"""
        <div style="background-color: #1e293b; border: 1.5px solid #f59e0b; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <div style="font-size: 16px; font-weight: bold; color: #fbbf24; margin-bottom: 12px;">⭐ משרות הזהב של השבוע (Top 3 Picks):</div>
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
                        {j.get('match_score')}% התאמה
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
            <div style="font-size: 18px; font-weight: bold; color: #f8fafc; margin-bottom: 14px; border-bottom: 2px solid #0284c7; padding-bottom: 6px;">
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
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; direction: rtl;">
    <div style="max-width: 680px; margin: 0 auto; background-color: #0f172a; padding: 10px;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 16px; padding: 24px; text-align: center; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.4);">
            <h1 style="margin: 0 0 8px 0; font-size: 22px; color: #ffffff; font-weight: 800;">🔗 דוח סיכום שבועי: כל המשרות המובילות | עידו גל</h1>
            <div style="font-size: 13.5px; color: #94a3b8;">תאריך הפקה: {now_str} | סה"כ משרות נבחרות השבוע: {len(unique_jobs)}</div>
        </div>

        <!-- Interactive Web App CTA Button -->
        <div style="text-align: center; margin-bottom: 28px;">
            <a href="{dashboard_url}" style="background-color: #0284c7; color: #ffffff; font-size: 15px; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4);">
                🚀 פתח דוח אינטראקטיבי וניהול משרות (✔️ / ✖️) ↗
            </a>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 8px;">כולל סינון מתקדם לפי תחומים, שמירת משרות והסרת משרות לא רלוונטיות</div>
        </div>

        {top_3_html}

        {sector_blocks_html}

        <!-- Footer -->
        <div style="border-top: 1px solid #334155; padding-top: 16px; text-align: center; font-size: 12px; color: #64748b; margin-top: 30px;">
            דוח זה הופק באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל.
        </div>

    </div>
</body>
</html>
"""
    return html

def run_weekly_summary():
    print("[+] Starting Saturday Weekly Summary Dispatch...")
    jobs = load_weekly_jobs()
    
    if not jobs:
        print("[!] No jobs found in archive for weekly digest. Sending empty alert.")
        
    build_and_save_docs_app(jobs, is_weekly=True)
    dashboard_url = "https://idogal0210-web.github.io/job_search_automation/"

    email_html = build_weekly_email_html(jobs, dashboard_url)

    sender_email = os.environ.get("SENDER_EMAIL")
    sender_pwd = os.environ.get("SENDER_APP_PASSWORD")
    recipient = "idogal0210@gmail.com"

    if sender_email and sender_pwd:
        msg = MIMEMultipart()
        msg['Subject'] = Header(f"🔗 דוח סיכום שבועי: כל המשרות המובילות ({len(jobs)} משרות) | עידו גל", 'utf-8')
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
                print(f"[+] Saturday weekly email successfully dispatched to {recipient} (Attempt {attempt}).")
                break
            except Exception as e:
                print(f"[!] Saturday email dispatch attempt {attempt} failed: {e}")
                time.sleep(attempt * 5)

if __name__ == "__main__":
    run_weekly_summary()
