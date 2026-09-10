import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

def build_unified_html_email(jobs, top_3, dashboard_url):
    now_str = datetime.now().strftime("%d.%m.%Y")
    
    if not jobs:
        return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<body style="font-family: Arial, sans-serif; background-color: #020617; color: #f8fafc; padding: 20px; direction: rtl; text-align: center;">
    <h1 style="color: #38bdf8;">🎯 דוח משרות יומי - {now_str}</h1>
    <p>הסריקה עברה בהצלחה, אך לא נמצאו משרות רלוונטיות היום שעוברות את רף הציון הנדרש.</p>
    <p>נמשיך לסרוק מחר!</p>
</body>
</html>
"""

    sectors = {
        "energy": {"title": "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA", "jobs": []},
        "drones": {"title": '🚁 רחפנים, כטב"ם אוטונומי ורובוטיקה', "jobs": []},
        "cuas": {"title": "🛡️ מערכות הגנת C-UAS וביטחון", "jobs": []},
        "avionics": {"title": '📡 מטע"דים, אלקטרו-אופטיקה ואוויוניקה', "jobs": []}
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
            
            if sec_key in ['drones', 'cuas', 'avionics']:
                badge_html = '<span style="background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">🚁 רחפנים וכטב"ם אוטונומי</span>'
            else:
                badge_html = '<span style="background-color: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 11px; font-weight: bold; display: inline-block; margin-bottom: 6px;">⚡ תשתיות אנרגיה וגז טבעי</span>'

            boxes_html = ""
            if comp_domain and comp_domain.strip():
                boxes_html += f'<div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #38bdf8; font-weight: bold;">🏢 תחום ומוצר החברה:</span> {comp_domain}</div>'
            if job_sum and job_sum.strip():
                boxes_html += f'<div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(51, 65, 85, 0.6); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #38bdf8; font-weight: bold;">📋 תקציר המשרה:</span> {job_sum}</div>'
            if strengths and strengths.strip():
                boxes_html += f'<div style="background-color: rgba(6, 78, 59, 0.2); border: 1px solid rgba(5, 150, 105, 0.35); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #e2e8f0;"><span style="color: #4ade80; font-weight: bold;">💪 נקודות חוזק מהניסיון שלך:</span> {strengths}</div>'
            comp_reqs = j.get('company_requirements', j.get('key_highlights', ''))
            if comp_reqs and comp_reqs.strip():
                boxes_html += f'<div style="background-color: rgba(2, 6, 23, 0.6); border: 1px solid rgba(14, 165, 233, 0.4); border-radius: 10px; padding: 10px 14px; font-size: 13px; line-height: 1.5; color: #cbd5e1;"><span style="color: #38bdf8; font-weight: bold;">🎯 דרישות החברה עבור המשרה:</span> {comp_reqs}</div>'

            cards_html += f"""
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 20px; margin-bottom: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.35);">
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
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    {boxes_html}
                </div>
                <div style="border-top: 1px solid rgba(51, 65, 85, 0.6); padding-top: 14px; margin-top: 14px; text-align: left;">
                    <a href="{j.get('link')}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; padding: 9px 22px; text-decoration: none; border-radius: 8px; font-size: 12.5px; font-weight: bold; display: inline-block;">
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
        
        <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; border-radius: 14px; padding: 24px; text-align: center; margin-bottom: 24px; border: 1px solid #334155;">
            <h1 style="margin: 0 0 6px 0; font-size: 22px; color: #38bdf8; font-weight: 800;">🎯 דוח משרות יומי מאוחד | עידו גל</h1>
            <div style="font-size: 13px; color: #94a3b8;">תאריך סריקה: {now_str} | סה"כ משרות נבחרות: {len(jobs)}</div>
        </div>

        <div style="text-align: center; margin-bottom: 26px;">
            <a href="{dashboard_url}" target="_blank" style="background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); color: #ffffff; font-size: 14.5px; font-weight: bold; text-decoration: none; padding: 13px 28px; border-radius: 12px; display: inline-block;">
                🚀 פתח דוח אינטראקטיבי וניהול משרות (✔️ / ✖️) ↗
            </a>
        </div>

        {top_3_html}
        {sector_blocks_html}

        <div style="border-top: 1px solid #1e293b; padding-top: 16px; text-align: center; font-size: 12px; color: #64748b;">
            דוח זה הופק באופן אוטומטי ע"י מערכת Job Search Automation עבור עידו גל.
        </div>
    </div>
</body>
</html>
"""
    return html

def send_email_report(sender_email, sender_pwd, processed_jobs, curated_email_jobs, top_3, dashboard_url, health):
    email_html = build_unified_html_email(curated_email_jobs, top_3, dashboard_url)

    msg = MIMEMultipart()
    if not processed_jobs:
        msg['Subject'] = Header(f"ℹ️ דוח משרות יומי - אין משרות חדשות שעברו סף | עידו גל", 'utf-8')
    else:
        msg['Subject'] = Header(f"🎯 דוח משרות יומי מאוחד ({len(curated_email_jobs)} משרות נבחרות) | עידו גל", 'utf-8')
    
    msg['From'] = Header(f"Job Search Automation <{sender_email}>", 'utf-8')
    msg['To'] = Header("idogal0210@gmail.com", 'utf-8')
    msg.attach(MIMEText(email_html, 'html', 'utf-8'))

    for attempt in range(1, 4):
        health.email_attempts += 1
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(sender_email, sender_pwd)
            server.sendmail(sender_email, "idogal0210@gmail.com", msg.as_string())
            server.quit()
            print(f"[EMAIL] Unified daily email successfully dispatched (Attempt {attempt}).")
            health.email_success = True
            break
        except Exception as e:
            print(f"[ERROR] Email dispatch attempt {attempt} failed: {e}")
            time.sleep(attempt * 5)
            
    return health.email_success
