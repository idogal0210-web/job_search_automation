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
    """Build a rich, RTL-formatted weekly summary HTML email structured as a comprehensive numbered table."""
    # 1. Deduplicate by link for the weekly digest
    seen_links = set()
    unique_jobs = []
    for j in jobs:
        link = j.get("link", "").strip()
        if link and link not in seen_links:
            seen_links.add(link)
            unique_jobs.append(j)
        elif not link:
            unique_jobs.append(j)

    # 2. Sort jobs by Company (sorted by highest match score per company) and match score descending
    companies = {}
    for j in unique_jobs:
        comp = j.get("company", "").strip() or "חברות שונות"
        comp_clean = comp.replace(" (איירובוטיקס)", "").replace(" (אלביט)", "").replace(" Ltd", "").replace(" Technologies", "").replace(" (ENLT)", "").replace(" Israel", "").replace(" Stabilized Systems", "").strip()
        if comp_clean not in companies:
            companies[comp_clean] = []
        companies[comp_clean].append(j)

    # Sort companies by max score
    sorted_companies = sorted(companies.items(), key=lambda item: max([x.get("match_score", 0) for x in item[1]]), reverse=True)
    
    # Flatten sorted jobs into a single list with sequential numbering
    sorted_unique_jobs = []
    for comp_name, comp_jobs in sorted_companies:
        c_sorted = sorted(comp_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
        sorted_unique_jobs.extend(c_sorted)

    # Top 3 Weekly Picks
    sorted_by_pure_score = sorted(unique_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    top_3_picks = sorted_by_pure_score[:3]

    # Build HTML
    html = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="he">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 15px; color: #1e293b; direction: rtl; text-align: right; }}
            .container {{ max-width: 920px; margin: 0 auto; background: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 25px rgba(0,0,0,0.08); direction: rtl; text-align: right; }}
            .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%); color: #ffffff; padding: 26px 20px; text-align: center; direction: rtl; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; color: #ffffff; }}
            .header p {{ margin: 8px 0 0 0; opacity: 0.9; font-size: 14px; color: #cbd5e1; }}
            .content {{ padding: 22px; direction: rtl; text-align: right; }}
            
            /* Top 3 Box */
            .gold-box {{ background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 2px solid #f59e0b; border-radius: 12px; padding: 18px; margin-bottom: 25px; box-shadow: 0 3px 10px rgba(245, 158, 11, 0.15); direction: rtl; text-align: right; }}
            .gold-title {{ font-size: 17px; font-weight: bold; color: #92400e; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; direction: rtl; }}
            .gold-card {{ background: #ffffff; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px; border-right: 4px solid #f59e0b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
            
            /* Job Table */
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0; font-size: 13px; }}
            th {{ background-color: #f8fafc; color: #334155; padding: 12px 8px; font-weight: 700; border-bottom: 2px solid #cbd5e1; text-align: right; }}
            td {{ padding: 12px 8px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: top; text-align: right; }}
            tr:nth-child(even) {{ background-color: #fafbfc; }}
            tr:hover {{ background-color: #f1f5f9; }}
            
            /* Badges & Buttons */
            .score-badge-high {{ background-color: #10b981; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; display: inline-block; white-space: nowrap; }}
            .score-badge-mid {{ background-color: #2563eb; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; display: inline-block; white-space: nowrap; }}
            .score-badge-normal {{ background-color: #f59e0b; color: white; padding: 4px 8px; border-radius: 12px; font-weight: bold; font-size: 12px; display: inline-block; white-space: nowrap; }}
            .btn-apply {{ display: inline-block; background-color: #2563eb; color: #ffffff !important; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 12px; white-space: nowrap; text-align: center; }}
            .btn-apply:hover {{ background-color: #1d4ed8; }}
            
            .pro-text {{ color: #059669; font-weight: 500; }}
            .gap-text {{ color: #d97706; font-size: 12px; }}
            
            .footer {{ background: #f8fafc; text-align: center; padding: 16px; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>📊 דוח סיכום שבועי מובנה | עידו גל</h1>
                <p>ריכוז כלל המשרות שנאספו השבוע ({len(unique_jobs)} משרות נבחרות מסודרות בטבלה)</p>
            </div>
            
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
    """

    # Top 3 Gold Picks Box
    if top_3_picks:
        html += """
                <div class="gold-box" dir="rtl" style="direction: rtl; text-align: right;">
                    <div class="gold-title" dir="rtl">
                        <span>⭐ משרות הזהב של השבוע (Top 3 Weekly Picks)</span>
                    </div>
        """
        for rank, job in enumerate(top_3_picks, 1):
            score = job.get("match_score", 90)
            summary_txt = job.get("pros") or job.get("summary") or ""
            html += f"""
                    <div class="gold-card" dir="rtl">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-weight: bold; font-size: 14.5px; color: #1e293b;">#{rank} {job.get('company')} - {job.get('title')}</span>
                            <span class="score-badge-high">{score}% התאמה</span>
                        </div>
                        <p style="margin: 3px 0 8px 0; font-size: 13px; color: #475569;">{summary_txt}</p>
                        <a href="{job.get('link')}" target="_blank" class="btn-apply" style="background-color: #d97706;">הגש מועמדות עכשיו &larr;</a>
                    </div>
            """
        html += "</div>"

    # Master Table
    if not sorted_unique_jobs:
        html += """
        <div style="text-align: center; padding: 40px; color: #64748b;">
            <p style="font-size: 16px;">לא נצברו משרות השבוע בארכיון.</p>
        </div>
        """
    else:
        html += f"""
                <h3 style="color: #1e3a8a; border-right: 4px solid #2563eb; padding-right: 8px; margin: 20px 0 12px 0;">
                    📋 טבלת ריכוז משרות מלאה ({len(sorted_unique_jobs)} משרות)
                </h3>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 5%; text-align: center;">מס'</th>
                            <th style="width: 15%;">חברה</th>
                            <th style="width: 22%;">תפקיד</th>
                            <th style="width: 9%; text-align: center;">התאמה</th>
                            <th style="width: 24%;">סיבת ההתאמה (רקע וחוזקות)</th>
                            <th style="width: 17%;">דרישות מחייבות / דגשים</th>
                            <th style="width: 8%; text-align: center;">קישור</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        row_counter = 1
        for comp_name, comp_jobs in sorted_companies:
            c_sorted = sorted(comp_jobs, key=lambda x: x.get("match_score", 0), reverse=True)
            rowspan_count = len(c_sorted)
            for idx_in_comp, j in enumerate(c_sorted):
                score = j.get("match_score", 85)
                if score >= 90:
                    badge_class = "score-badge-high"
                elif score >= 80:
                    badge_class = "score-badge-mid"
                else:
                    badge_class = "score-badge-normal"
                    
                pros_txt = j.get("pros") or j.get("summary") or "התאמה גבוהה לרקע בהנדסאות מכונות, חשמל ותפעול"
                gaps_txt = j.get("gaps") or j.get("license_note") or j.get("sector") or "משרה פעילה"
                link_url = j.get("link", "#")

                html += "<tr>"
                html += f'<td style="text-align: center; font-weight: bold; color: #64748b;">{row_counter}</td>'
                
                # Merge company cell with rowspan if it is the first row for this company
                if idx_in_comp == 0:
                    border_style = "border-left: 1px solid #e2e8f0; " if rowspan_count > 1 else ""
                    html += f'<td rowspan="{rowspan_count}" style="vertical-align: middle; background: #ffffff; font-weight: bold; {border_style}font-size: 13.5px; color: #1e293b;">{comp_name}</td>'
                
                html += f"""
                            <td>{j.get('title')}</td>
                            <td style="text-align: center;"><span class="{badge_class}">{score}%</span></td>
                            <td class="pro-text">{pros_txt}</td>
                            <td class="gap-text">{gaps_txt}</td>
                            <td style="text-align: center;"><a href="{link_url}" target="_blank" class="btn-apply">הגש &larr;</a></td>
                        </tr>
                """
                row_counter += 1
        html += """
                    </tbody>
                </table>
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

    if not jobs:
        print("[!] No jobs found in archive for this week.")
        return False

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
