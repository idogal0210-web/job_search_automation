import os
import re
import smtplib
import time
from html import escape
from src.url_utils import safe_http_url
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from datetime import datetime

def is_junior_friendly_job(job):
    """Check if job is open/friendly to juniors, newly certified, or practical engineers."""
    openness = str(job.get("junior_openness") or "").lower()
    title = str(job.get("title") or "").lower()
    keywords = ["גבוהה", "פתוח", "ג'וניור", "junior", "מתאים", "הסמכה טרייה", "1-2", "שנה ניסיון", "כן"]
    return any(k in openness for k in keywords) or "junior" in title or "הנדסאי בתחילת" in openness


def format_salary_badge(job):
    """Format salary with explicit attribution: specified in job vs estimate only."""
    sal_range = (job.get("salary_range") or "").strip()
    sal_type = job.get("salary_source_type", "")
    
    if sal_type == "job_ad":
        return f"{sal_range} - צוין במשרה", True
    elif sal_range and sal_range != "לא צוין" and sal_range != "לא צוין במודעה":
        return f"{sal_range} - לא צוין שכר - הערכה בלבד", False
    else:
        return "לא צוין שכר - הערכה בלבד", False


def wrap_ltr_tokens(text):
    """Wrap Latin text/acronyms in ltr span while preserving HTML entities."""
    if not text:
        return ""
    text_str = str(text)
    has_latin = any('a' <= c.lower() <= 'z' for c in text_str)
    has_hebrew = any('\u0590' <= c <= '\u05ea' for c in text_str)
    if has_latin and not has_hebrew:
        return f'<span class="text-ltr">{text_str}</span>'
    if has_latin and has_hebrew:
        def replacer(m):
            token = m.group(0)
            if token.startswith('&') and token.endswith(';'):
                return token
            return f'<span class="text-ltr">{token}</span>'
        return re.sub(r'(&[a-zA-Z0-9#]+;)|(\b[A-Za-z][A-Za-z0-9\-_/]*\b)', replacer, text_str)
    return text_str


def build_unified_html_email(jobs, top_3, dashboard_url, health=None):
    # Enforce strictly up to 5 jobs in daily email
    jobs = (jobs or [])[:5]
    # Escape copies at the rendering boundary; leave source records untouched.
    def safe_job(job):
        return {key: escape(safe_http_url(value), quote=True) if key in {"link", "salary_source_url"}
                else escape(value, quote=True) if isinstance(value, str) else value
                for key, value in job.items()}
    jobs = [safe_job(job) for job in jobs]
    dashboard_url = escape(safe_http_url(dashboard_url), quote=True)
    now_str = datetime.now().strftime("%d.%m.%Y")
    
    pending = getattr(health, 'pending_evaluations', 0) if health else 0
    incomplete = bool(health and (pending or health.linkedin_failures or health.drushim_failures or getattr(health, "comeet_failures", 0) or health.final_status.startswith('FAILED_')))
    run_notice = (f'הריצה הושלמה חלקית. {pending} משרות ממתינות לבדיקה מלאה; ייתכנו תוצאות חסרות.'
                  if incomplete else 'בדיקת המשרות הושלמה.')

    dashboard_btn_html = ""
    if dashboard_url:
        dashboard_btn_html = f"""
          <tr>
            <td align="center" style="padding-bottom: 20px;">
              <a href="{dashboard_url}" target="_blank" style="display: inline-block; padding: 10px 20px; background-color: #21262d; border: 1px solid #30363d; border-radius: 6px; color: #58a6ff; font-size: 13px; font-weight: 600; text-decoration: none;">
                מעבר לדשבורד המלא וניהול משרות ↗
              </a>
            </td>
          </tr>"""

    notice_row_html = ""
    if incomplete:
        notice_row_html = f"""
          <tr>
            <td style="padding-bottom: 16px;">
              <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #21262d; border: 1px solid #d29922; border-radius: 6px;">
                <tr>
                  <td align="center" style="padding: 10px 14px; color: #e3b341; font-size: 13px;">
                    {run_notice}
                  </td>
                </tr>
              </table>
            </td>
          </tr>"""

    if not jobs:
        empty_card_html = f"""
          <tr>
            <td style="padding-bottom: 16px;">
              <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; overflow: hidden;">
                <tr>
                  <td align="center" style="padding: 24px 16px; color: #c9d1d9; font-size: 14px; line-height: 1.6;">
                    <p style="margin: 0 0 8px 0; color: #f0f6fc; font-size: 15px; font-weight: 600;">אין משרות חדשות שאושרו בדוח זה.</p>
                    <p style="margin: 0 0 8px 0; color: #8b949e; font-size: 13px;">{run_notice}</p>
                    <p style="margin: 0; color: #8b949e; font-size: 13px;">נמשיך לסרוק מחר!</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>"""
        cards_content = empty_card_html
    else:
        cards_list = []
        for idx, j in enumerate(jobs, 1):
            title = j.get("title", "")
            company = j.get("company", "")
            title_html = wrap_ltr_tokens(title)
            comp_html = wrap_ltr_tokens(company)
            
            if comp_html:
                header_title = f"{idx}. {title_html} | {comp_html}"
            else:
                header_title = f"{idx}. {title_html}"

            score = j.get("base_match_score", j.get("match_score", 0))
            _, is_ad = format_salary_badge(j)
            raw_sal = (j.get("salary_range") or "").strip()
            sal_note = "(צוין במשרה)" if is_ad else "(הערכה בלבד)"
            if raw_sal and raw_sal not in {"לא צוין", "לא צוין במודעה"}:
                sal_clean = raw_sal if ("₪" in raw_sal or any(sym in raw_sal for sym in ["$", "€"])) else f"{raw_sal} ₪"
                salary_display = f'<span class="text-ltr">{sal_clean}</span> {sal_note}'
            else:
                salary_display = f'לא צוין {sal_note}'

            domain = j.get('company_domain_product') or j.get('company_summary') or j.get('sector') or 'טכנולוגיה ותשתיות'
            domain_html = wrap_ltr_tokens(domain)

            reqs = j.get('company_requirements') or j.get('key_highlights') or j.get('experience_strengths') or j.get('job_summary') or 'דרישות המשרה מפורטות בלינק המצורף.'
            reqs_html = wrap_ltr_tokens(reqs)

            job_link = j.get("link") or "#"

            card_item = f"""
          <!-- תחילת כרטיס משרה {idx} -->
          <tr>
            <td style="padding-bottom: 16px;">
              <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #161b22; border: 1px solid #30363d; border-radius: 10px; overflow: hidden;">
                <tr>
                  <td style="padding: 16px;">
                    
                    <!-- שם המשרה והחברה -->
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td align="right" style="color: #58a6ff; font-size: 16px; font-weight: bold; line-height: 1.4; padding-bottom: 8px;">
                          {header_title}
                        </td>
                      </tr>
                    </table>

                    <!-- שכר ואחוזי התאמה בשורה מודגשת -->
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="background-color: #21262d; border-radius: 6px; margin-bottom: 12px;">
                      <tr>
                        <td align="right" style="padding: 8px 10px; color: #3fb950; font-size: 13px; font-weight: 600;">
                          התאמה: {score}% &nbsp;|&nbsp; שכר: {salary_display}
                        </td>
                      </tr>
                    </table>

                    <!-- פרטי המשרה -->
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td align="right" style="color: #c9d1d9; font-size: 13px; line-height: 1.6; padding-bottom: 16px;">
                          <strong style="color: #8b949e;">תחום ומוצר:</strong> {domain_html}<br>
                          <strong style="color: #8b949e;">דרישות עיקריות:</strong> {reqs_html}
                        </td>
                      </tr>
                    </table>

                    <!-- כפתור הגשת מועמדות לרוחב מלא -->
                    <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0">
                      <tr>
                        <td align="center" style="background-color: #1f6feb; border-radius: 6px;">
                          <a href="{job_link}" target="_blank" style="display: block; padding: 12px 16px; color: #ffffff; text-decoration: none; font-size: 14px; font-weight: bold; text-align: center; white-space: nowrap;">
                            הגשת מועמדות למשרה ↗
                          </a>
                        </td>
                      </tr>
                    </table>

                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- סוף כרטיס משרה {idx} -->"""
            cards_list.append(card_item)
        cards_content = "\n".join(cards_list)

    html = f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>דוח משרות יומי</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background-color: #0d1117;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
    }}
    table {{
      border-spacing: 0;
      mso-table-lspace: 0pt;
      mso-table-rspace: 0pt;
    }}
    td {{
      padding: 0;
    }}
    img {{
      border: 0;
      -ms-interpolation-mode: bicubic;
    }}
    .text-ltr {{
      direction: ltr !important;
      unicode-bidi: embed !important;
      display: inline-block;
    }}
  </style>
</head>
<body style="margin: 0; padding: 12px; background-color: #0d1117;">

  <!-- מיכל ראשי ממורכז -->
  <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" dir="rtl" style="background-color: #0d1117;">
    <tr>
      <td align="center">
        
        <table role="presentation" width="100%" border="0" cellpadding="0" cellspacing="0" style="max-width: 460px; width: 100%;">
          
          <!-- כותרת ראשית -->
          <tr>
            <td align="center" style="padding: 16px 8px 24px 8px;">
              <h1 style="margin: 0; color: #f0f6fc; font-size: 20px; font-weight: 700; line-height: 1.3;">
                🎯 דוח משרות יומי מאוחד
              </h1>
              <p style="margin: 6px 0 0 0; color: #8b949e; font-size: 13px;">
                תאריך סריקה: <span class="text-ltr">{now_str}</span>
              </p>
            </td>
          </tr>

          <!-- כפתור דשבורד אינטראקטיבי -->{dashboard_btn_html}

          <!-- הודעת סטטוס ריצה חלקי -->{notice_row_html}

          <!-- כרטיסי משרות -->{cards_content}

          <!-- פוטר -->
          <tr>
            <td align="center" style="padding: 16px 8px 24px 8px; border-top: 1px solid #30363d;">
              <p style="margin: 0; color: #8b949e; font-size: 12px; line-height: 1.5;">
                דוח זה הופק באופן אוטומטי ע&quot;י מערכת Job Search Automation עבור עידו גל.
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>

</body>
</html>
"""
    return html

def send_email_report(sender_email, sender_pwd, processed_jobs, curated_email_jobs, top_3, dashboard_url, health):
    email_html = build_unified_html_email(curated_email_jobs, top_3, dashboard_url, health)

    msg = MIMEMultipart()
    if health.pending_evaluations or health.linkedin_failures or health.drushim_failures or getattr(health, "comeet_failures", 0) or health.final_status.startswith('FAILED_'):
        msg['Subject'] = Header('⚠️ דוח משרות חלקי — נותרו בדיקות להשלמה | עידו גל', 'utf-8')
    elif not processed_jobs:
        msg['Subject'] = Header(f"ℹ️ דוח משרות יומי - אין משרות חדשות שעברו סף | עידו גל", 'utf-8')
    else:
        msg['Subject'] = Header(f"🎯 דוח משרות יומי מאוחד ({len(curated_email_jobs)} משרות נבחרות) | עידו גל", 'utf-8')
    
    msg['From'] = Header(f"Job Search Automation <{sender_email}>", 'utf-8')
    msg['To'] = Header("idogal0210@gmail.com", 'utf-8')
    msg.attach(MIMEText(email_html, 'html', 'utf-8'))

    for attempt in range(1, 3):
        delivery_attempted = False
        server = None
        health.email_attempts += 1
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
            server.starttls()
            server.login(sender_email, sender_pwd)
            delivery_attempted = True
            server.sendmail(sender_email, "idogal0210@gmail.com", msg.as_string())
            health.email_success = True
            try:
                server.quit()
            except Exception:
                pass  # DATA was accepted; QUIT failure must not trigger a duplicate send.
            print(f"[EMAIL] Unified daily email successfully dispatched (Attempt {attempt}).")
            health.email_success = True
            break
        except Exception as e:
            print(f"[ERROR] Email dispatch attempt {attempt} failed: {type(e).__name__}")
            if delivery_attempted:
                print("[EMAIL] Delivery outcome uncertain; automatic retry stopped")
                break
            if attempt < 2:
                time.sleep(attempt * 5)
        finally:
            if server is not None:
                try:
                    server.close()
                except Exception:
                    pass
            
    return health.email_success
