import os
import sys
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "weekly_archive.json")

def load_weekly_jobs():
    """Load jobs from the past 7 days from weekly_archive.json."""
    if not os.path.exists(ARCHIVE_FILE):
        print("[-] weekly_archive.json not found.")
        return []
    try:
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            jobs = json.load(f)
        
        now = datetime.now()
        # 7-day window
        cutoff_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        weekly_jobs = [j for j in jobs if j.get("date", "") >= cutoff_date]
        return weekly_jobs
    except Exception as e:
        print(f"[-] Error loading weekly jobs: {e}")
        return []

def build_weekly_email_html(jobs):
    """Build a rich, RTL-formatted weekly summary HTML email."""
    # 1. Deduplicate by link for the weekly digest
    seen_links = set()
    unique_jobs = []
    for j in jobs:
        link = j.get("link", "")
        if link not in seen_links:
            seen_links.add(link)
            unique_jobs.append(j)

    # 2. Sort by match score to pick Top 3 Weekly Picks
    sorted_by_score = sorted(unique_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    top_3_picks = sorted_by_score[:3]

    # 3. Group jobs by Date
    jobs_by_date = {}
    for j in unique_jobs:
        d = j.get("date", "")
        if d not in jobs_by_date:
            jobs_by_date[d] = {
                "day_name": j.get("day_name", ""),
                "date": d,
                "jobs": []
            }
        jobs_by_date[d]["jobs"].append(j)

    # Sort dates chronologically
    sorted_dates = sorted(jobs_by_date.keys())

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 15px; color: #1e293b; direction: rtl; text-align: right; }}
            .container {{ max-width: 700px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 25px rgba(0,0,0,0.08); direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #ffffff; padding: 28px 20px; text-align: center; direction: rtl; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; color: #ffffff; }}
            .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; color: #cbd5e1; }}
            .content {{ padding: 22px; direction: rtl; text-align: right; }}
            
            /* Top 3 Box */
            .gold-box {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 18px; margin-bottom: 25px; box-shadow: 0 3px 10px rgba(245, 158, 11, 0.15); direction: rtl; text-align: right; }}
            .gold-title {{ font-size: 17px; font-weight: bold; color: #92400e; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; direction: rtl; }}
            .gold-card {{ background: #ffffff; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; border-right: 4px solid #f59e0b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            
            /* Day Section */
            .day-section {{ margin-bottom: 25px; }}
            .day-header {{ font-size: 16px; font-weight: bold; color: #1e3a8a; background: #eff6ff; padding: 10px 14px; border-radius: 8px; border-right: 4px solid #2563eb; margin-bottom: 12px; direction: rtl; text-align: right; }}
            
            /* Job Table */
            table {{ width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 10px; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; font-size: 13.5px; }}
            th {{ background-color: #f8fafc; color: #475569; padding: 10px 8px; font-weight: 700; border-bottom: 1px solid #e2e8f0; text-align: right; }}
            td {{ padding: 12px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: middle; text-align: right; }}
            tr:last-child td {{ border-bottom: none; }}
            tr:nth-child(even) {{ background-color: #fafbfc; }}
            
            /* Badges & Buttons */
            .score-badge-high {{ background-color: #10b981; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; display: inline-block; }}
            .score-badge-mid {{ background-color: #2563eb; color: white; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; display: inline-block; }}
            .btn-apply {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 12px; white-space: nowrap; text-align: center; }}
            .btn-apply:hover {{ background-color: #1d4ed8; }}
            
            .footer {{ background: #f8fafc; text-align: center; padding: 16px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>📊 דוח סיכום שבועי | עידו גל</h1>
                <p>כל המשרות המותאמות שנאספו השבוע ({len(unique_jobs)} משרות נבחרות)</p>
            </div>
            
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
    """

    # Top 3 Box
    if top_3_picks:
        html += """
                <div class="gold-box" dir="rtl" style="direction: rtl; text-align: right;">
                    <div class="gold-title" dir="rtl">
                        <span>⭐ משרות הזהב של השבוע (Top 3 Picks)</span>
                    </div>
        """
        for rank, job in enumerate(top_3_picks, 1):
            score = job.get("match_score", 90)
            html += f"""
                    <div class="gold-card" dir="rtl">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: bold; font-size: 14.5px; color: #1e293b;">#{rank} {job.get('company')} - {job.get('title')}</span>
                            <span class="score-badge-high">{score}% התאמה</span>
                        </div>
                        <p style="margin: 3px 0 8px 0; font-size: 13px; color: #475569;">{job.get('summary', '')}</p>
                        <a href="{job.get('link')}" target="_blank" class="btn-apply" style="background-color: #d97706;">הגש מועמדות עכשיו &larr;</a>
                    </div>
            """
        html += "</div>"

    # Day by Day Tables
    if not sorted_dates:
        html += """
        <div style="text-align: center; padding: 40px; color: #64748b;">
            <p style="font-size: 16px;">לא נצברו משרות השבוע.</p>
        </div>
        """
    else:
        for date_key in sorted_dates:
            day_data = jobs_by_date[date_key]
            d_formatted = datetime.strptime(date_key, "%Y-%m-%d").strftime("%d.%m.%Y")
            day_name = day_data.get("day_name", "")
            
            html += f"""
                <div class="day-section" dir="rtl">
                    <div class="day-header" dir="rtl">
                        📅 {day_name} | {d_formatted} ({len(day_data['jobs'])} משרות)
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 25%;">חברה</th>
                                <th style="width: 35%;">שם המשרה</th>
                                <th style="width: 20%;">סקטור / תחום</th>
                                <th style="width: 10%; text-align: center;">התאמה</th>
                                <th style="width: 10%; text-align: center;">פעולה</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            # Sort this day's jobs strictly by match score descending
            day_jobs_sorted = sorted(day_data["jobs"], key=lambda x: x.get("match_score", 0), reverse=True)
            
            for j in day_jobs_sorted:
                score = j.get("match_score", 85)
                badge_class = "score-badge-high" if score >= 90 else "score-badge-mid"
                html += f"""
                            <tr>
                                <td><strong>{j.get('company')}</strong></td>
                                <td>{j.get('title')}</td>
                                <td style="font-size: 12.5px; color: #64748b;">{j.get('sector', '')}</td>
                                <td style="text-align: center;"><span class="{badge_class}">{score}%</span></td>
                                <td style="text-align: center;"><a href="{j.get('link')}" target="_blank" class="btn-apply">הגש &larr;</a></td>
                            </tr>
                """

            html += """
                        </tbody>
                    </table>
                </div>
            """

    html += """
            </div>
            <div class="footer" dir="rtl">
                <p>דוח זה הופק באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def send_weekly_email():
    """Build and dispatch the weekly digest email."""
    print("[+] Building Weekly Summary Report for Ido Gal...")
    jobs = load_weekly_jobs()
    print(f"[+] Loaded {len(jobs)} jobs for this week.")

    html_content = build_weekly_email_html(jobs)

    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_APP_PASSWORD")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    recipient_email = "idogal0210@gmail.com"

    if not sender_email or not sender_password:
        print("[-] SENDER_EMAIL or SENDER_APP_PASSWORD missing. Writing preview to sample_weekly_report.html...")
        report_path = os.path.join(os.path.dirname(__file__), "sample_weekly_report.html")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[+] Preview written to {report_path}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "📊 סיכום שבועי: כל המשרות המובילות של השבוע | עידו גל"
        msg["From"] = f"Job Search Automation <{sender_email}>"
        msg["To"] = recipient_email
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"[+] Weekly Summary successfully sent to {recipient_email}!")
        return True
    except Exception as e:
        print(f"[-] Failed to send weekly email: {e}")
        return False

if __name__ == "__main__":
    send_weekly_email()
