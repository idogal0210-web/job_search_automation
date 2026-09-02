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

from interactive_app_builder import build_and_save_docs_app

load_dotenv()

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "weekly_archive.json")

def load_weekly_jobs():
    """Load jobs from past 7 days from weekly_archive.json."""
    if not os.path.exists(ARCHIVE_FILE):
        return []
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        weekly_jobs = [j for j in jobs if j.get("date", "") >= cutoff_date]
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

    # Sector grouping
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

    # Top 3 Box
    top_3_html = ""
    if top_3_picks:
        top_items = ""
        for idx, pick in enumerate(top_3_picks, 1):
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
            <div style="font-size: 16px; font-weight: bold; color: #92400e; margin-bottom: 12px;">⭐ משרות הזהב של השבוע (Top 3 Picks):</div>
            {top_items}
        </div>
        """

    # Sector tables
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
            <h1 style="margin: 0 0 6px 0; font-size: 22px;">🔗 דוח סיכום שבועי: כל המשרות המובילות | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך הפקה: {now_str} | סה"כ משרות נבחרות השבוע: {len(unique_jobs)}</div>
        </div>

        <!-- Interactive Web App CTA Button -->
        <div style="text-align: center; margin-bottom: 24px;">
            <a href="{dashboard_url}" style="background-color: #0284c7; color: #ffffff; font-size: 15px; font-weight: bold; text-decoration: none; padding: 14px 28px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);">
                🚀 פתח דוח שבועי אינטראקטיבי וסינון משרות (V / X) ↗
            </a>
            <div style="font-size: 12px; color: #64748b; margin-top: 6px;">כולל תובנות AI על החברה, כמות עובדים, מדד פתיחות וסרגל התקדמות</div>
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

def run_weekly_summary():
    print("[+] Starting Saturday Weekly Summary Dispatch...")
    jobs = load_weekly_jobs()
    
    if not jobs:
        print("[!] No jobs found in archive for weekly digest. Sending empty alert.")
        
    # Build GitHub Pages interactive app for Saturday digest
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
