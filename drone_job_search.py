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
            "license_note": job.get("license_note_hebrew", ""),
            "tier_priority": job.get("tier_priority", 2)
        })

    try:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(archive_list, f, ensure_ascii=False, indent=2)
        print(f"[+] Updated {ARCHIVE_FILE} with prioritized drone jobs for weekly digest.")
    except Exception as e:
        print(f"[-] Error writing weekly_archive.json: {e}")

# Complete and Updated Candidate Profile Context for Drone Jobs Evaluation
IDO_DRONE_CV_SUMMARY = """
Name: Ido Gal (עידו גל)
Email: idogal0210@gmail.com | Phone: 052-632-8886 | Location: Tel Aviv - Or Aqiva (Center, Sharon, North, or Relocation).
LinkedIn: linkedin.com/in/idogal0210

Education & Certifications:
- Practical Mechanical Engineer (הנדסאי מכונות), Specializing in Green Energy and Natural Gas (התמחות באנרגיה ירוקה ובגז טבעי), Ruppin Academic Center (2024). NOT a B.Sc. Engineer!
- Certified Electrician (חשמלאי מוסמך), Ruppin Academic Center (Expected completion 2026).
- Drone Pilot License Status: Currently does NOT hold a commercial CAAI (רת"א) drone pilot license.

Technical Tools & Capabilities:
- Advanced Excel: Reports, complex data analysis, automation.
- SAP.
- AI Tools: Copilot 365, Gemini — practical application in professional work environments to improve reporting and workflows.
- Data analysis and operational reporting.

Core Skills:
- Monitoring & coordination of natural gas supply 24/7.
- Working with complex energy systems & high-tech infrastructure.
- Handling abnormal situations & emergency response in real-time under pressure.
- Autonomous decision-making in safety-critical environments.
- Cross-departmental collaboration (commercial, operational, INGL, offshore platform).
- Work process improvement, task prioritization, and employee training/mentoring.

Languages:
- Hebrew: Native language.
- English: Full professional proficiency (5 years international team training in US & Germany).

Professional Experience:
1. Energean Israel Ltd. | Gas Controller | 2022–Present:
   - 24/7 operational oversight of natural gas supply to strategic customers (power stations, large industrial plants).
   - Sole operational representative on night shifts, independently coordinating with offshore platform and INGL (נתג"ז).
   - Real-time pressure monitoring, flow rates, nomination approvals, reporting deviations.
   - Close coordination with commercial team to align operational execution with commercial commitments.
   - Implementation of AI tools (Copilot 365, Gemini) for reporting efficiency.
2. Vulcan / Energean Israel Ltd. | Security Officer, Strategic Energy Facility | 2020–2022:
   - Protection of critical natural gas infrastructure in sensitive, strictly regulated environments.
3. Sales Team Leader & Sales Trainer | International Markets (US & Germany) | 2015–2020:
   - Recruited, trained, and mentored sales reps in US & Germany. Leadership, cross-cultural training, and workflow implementation.
4. MER Group | Solar PV Systems Installer | 2010–2012:
   - Hands-on field work, end-to-end installation and initial commissioning of PV systems, wiring and electrical connections.

Military Service:
- Nahal Reconnaissance Unit (סיירת נח"ל) | Demolitions and Combat Engineering (חבלה והנדסה קרבית) | 2012–2015:
  - Combat soldier and commander in demolitions and combat engineering. Led the unit's demolitions field as a career service member (קבע).
  - Certifications: Rifleman 08 (רובאי 08) and Demolitions & Combat Engineering 07 (הסמכת חבלה והנדסה קרבית 07).

====================================================================
PRIORITIZATION TIERS FOR TARGET DRONE COMPANIES (APPLY SCORE BOOST):
====================================================================
⭐ TIER 1 (MAXIMUM BOOST +15% - Perfect Fit for Combat/Demolitions + Mech/Elec + International Training):
1. XTEND (אקסטנד): Tactical VR Drones, Human-Guided, US/DoD training & ops, flight operations, mechanical/avionics integration.
2. SpearUAV (ספיר): Encapsulated tactical drones Ninox, mechanical launch tubes, demolitions & payload integration.
3. רפאל (Rafael): Defense test arenas, demolitions, tactical drones, laser C-UAS, explosive testing (חבלה 07/08).

🚀 TIER 2 (STRONG BOOST +10% - Energy Facilities, Autonomous Ops & Precision Electro-Mechanics):
4. Percepto (פרספטו): Autonomous Drone-in-a-Box for Energy & Critical Infrastructure (Direct fit to Energean / SCADA / Solar).
5. NextVision (נקסט ויז'ן): Stabilized micro-gimbals, cameras, precision electro-mechanics & NPI.
6. BlueBird Aero Systems / Airobotics / HevenDrones / Steadicopter / Robotican / Flytrex.

🛡️ TIER 3 (MODERATE BOOST +5% - Defense Giants & Avionics/Cyber):
7. Elbit Systems (אלביט מערכות), IAI (התעשייה האווירית), BIRD Aerosystems, Regulus Cyber, ParaZero, D-Fend Solutions, Skylock.

CATEGORIZATION OF DRONE JOBS BY LICENSE REQUIREMENT:
1. None ('none'): Mechanical Assembly, Integration, Control Room / Remote Operations, Electrical & Avionics Wiring, Demolitions/Testing.
2. Training Provided ('training_provided'): Companies offering in-house flight training & operator certification on the job.
3. Advantage ('advantage'): Field testing, flight testing, or customer support where a pilot license is a plus but not strictly mandatory.
4. Mandatory ('mandatory'): Roles strictly requiring an active commercial CAAI (רת"א) pilot license.

EXCLUDED / REJECTED:
❌ Energean, INGL, Chevron Israel, Raycatch.
❌ Jobs requiring ONLY B.Sc. Aerospace/Mechanical Engineer where Practical Engineer (הנדסאי) is strictly rejected.
❌ Minimum Match Score threshold: 65%.
"""

def fetch_drone_jobs(seen_drones_dict):
    """Fetch potential drone, UAV, and autonomous robotics jobs from LinkedIn Israel prioritized by Tiers."""
    jobs = []
    print("[+] Fetching live Drone & UAV job listings from LinkedIn Israel prioritized by Tier 1 & 2 companies...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    # Priority queries focusing on Tier 1 & 2 first
    tier_1_2_company_queries = [
        "XTEND Reality",
        "Spear UAV",
        "Rafael Defense Drones",
        "Percepto Drones",
        "NextVision",
        "BlueBird Aero Systems",
        "Airobotics",
        "Heven Drones",
        "Steadicopter",
        "Robotican"
    ]

    drone_role_queries = [
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
        "מפעיל כטבמ",
        "Elbit Systems UAV",
        "IAI Drones",
        "BIRD Aerosystems"
    ]

    all_queries = []
    for c in tier_1_2_company_queries:
        all_queries.append((c, 0))
    for q in drone_role_queries:
        all_queries.append((q, 0))
        all_queries.append((q, 25))

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
    """Use Gemini AI to analyze fit, prioritize Tiers, and classify licensing for Drone/UAV roles."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        print("[-] GEMINI_API_KEY missing.")
        return []

    client = genai.Client(api_key=gemini_key)
    evaluated_jobs = []

    candidate_batch = job_list[:90]

    prompt = f"""
You are an expert AI Aerospace & Drone Career Advisor evaluating Drone/UAV/Robotics jobs for Ido Gal based on his updated CV and STRICT 3-TIER COMPANY PRIORITIZATION.

CANDIDATE CV PROFILE & RULES:
{IDO_DRONE_CV_SUMMARY}

JOB POSTINGS TO EVALUATE:
{json.dumps(candidate_batch, ensure_ascii=False, indent=2)}

Filter and evaluate the jobs strictly according to the candidate profile, prioritizing Tier 1 (XTEND, SpearUAV, Rafael) and Tier 2 (Percepto, NextVision, BlueBird, Airobotics, HevenDrones).
Return a JSON array of objects with the following schema for jobs matching score >= 65%:
[
  {{
    "title": "שם התפקיד והחברה",
    "link": "URL link",
    "match_score": 85, (integer 65-100, incorporating Tier boosts),
    "company": "שם החברה",
    "location": "מיקום (מרכז / שרון / צפון / Remote)",
    "summary_hebrew": "תקציר ממוקד בעברית של 2 שורות בלבד על התפקיד, הרחפנים/מערכות והאחריות",
    "pros_hebrew": "2-3 נקודות חוזק בולטות להתאמה מהניסיון של עידו",
    "gaps_hebrew": "דרישות חובה או פערים לתשומת לב",
    "license_status": "none" | "training_provided" | "advantage" | "mandatory",
    "license_note_hebrew": "הסבר קצר על סטטוס הרישיון",
    "tier_priority": 1 | 2 | 3 (1 for XTEND/Spear/Rafael, 2 for Percepto/NextVision/BlueBird/Airobotics/Heven, 3 for others)
  }}
]

CRITICAL RULES:
- PRIORITIZE Tier 1 & Tier 2 companies at the very top of the list!
- Categorize 'license_status' accurately ('none', 'training_provided', 'advantage', 'mandatory').
- Reject B.Sc. Engineer ONLY jobs where Practical Engineer (הנדסאי) is strictly rejected.
- Return top 6-8 best matching jobs.
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

    # Sort first by tier priority (Tier 1 first), then by match_score
    evaluated_jobs.sort(key=lambda x: (x.get("tier_priority", 3), -x.get("match_score", 0)))
    return evaluated_jobs[:6]

def build_drone_html_email(evaluated_jobs):
    """Build a specialized Aero-Tech styled RTL HTML email with Tier prioritization badges and distinct colored categories."""
    
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
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #080e1e; margin: 0; padding: 18px; color: #f8fafc; direction: rtl; text-align: right; }}
            .container {{ max-width: 680px; margin: 0 auto; background: #0f172a; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.6); border: 1px solid #1e293b; direction: rtl; text-align: right; }}
            
            /* Header */
            .header {{ background: linear-gradient(135deg, #0369a1 0%, #0f172a 100%); color: #ffffff; padding: 28px 20px; text-align: center; direction: rtl; border-bottom: 2px solid #0284c7; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 800; color: #ffffff; }}
            .header p {{ margin: 6px 0 0 0; opacity: 0.95; font-size: 14px; color: #bae6fd; }}
            
            .content {{ padding: 24px 20px; direction: rtl; text-align: right; }}
            
            /* Tier 1 Spotlight Banner */
            .tier-banner {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border: 1px solid #6366f1; border-radius: 10px; padding: 12px 16px; margin-bottom: 22px; font-size: 13px; color: #e0e7ff; direction: rtl; }}
            
            /* Category Containers */
            .category-box {{ margin-bottom: 26px; border-radius: 12px; padding: 16px; direction: rtl; text-align: right; }}
            
            /* Color Schemes per Category */
            /* 1. None - Emerald Green */
            .cat-box-none {{ background: rgba(6, 78, 59, 0.25); border: 1.5px solid #10b981; }}
            .cat-header-none {{ color: #34d399; font-size: 15.5px; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(16, 185, 129, 0.4); padding-bottom: 8px; }}
            .card-none {{ background: #0b1528; border: 1px solid #10b981; border-right: 5px solid #10b981; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1); }}
            .badge-none {{ background: #10b981; color: #ffffff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-none {{ display: inline-block; background: #059669; color: #ffffff !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; text-align: center; border: 1px solid #34d399; }}
            
            /* 2. Training Provided - Amber / Gold */
            .cat-box-training {{ background: rgba(120, 53, 15, 0.25); border: 1.5px solid #f59e0b; }}
            .cat-header-training {{ color: #fbbf24; font-size: 15.5px; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(245, 158, 11, 0.4); padding-bottom: 8px; }}
            .card-training {{ background: #0b1528; border: 1px solid #f59e0b; border-right: 5px solid #f59e0b; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1); }}
            .badge-training {{ background: #f59e0b; color: #000000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-training {{ display: inline-block; background: #d97706; color: #ffffff !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; text-align: center; border: 1px solid #fbbf24; }}

            /* 3. Advantage - Sky Blue */
            .cat-box-adv {{ background: rgba(12, 74, 110, 0.25); border: 1.5px solid #0284c7; }}
            .cat-header-adv {{ color: #38bdf8; font-size: 15.5px; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(2, 132, 199, 0.4); padding-bottom: 8px; }}
            .card-adv {{ background: #0b1528; border: 1px solid #0284c7; border-right: 5px solid #0284c7; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.1); }}
            .badge-adv {{ background: #0284c7; color: #ffffff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-adv {{ display: inline-block; background: #0284c7; color: #ffffff !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; text-align: center; border: 1px solid #38bdf8; }}

            /* 4. Mandatory - Coral Red */
            .cat-box-mand {{ background: rgba(127, 29, 29, 0.25); border: 1.5px solid #ef4444; }}
            .cat-header-mand {{ color: #f87171; font-size: 15.5px; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(239, 68, 68, 0.4); padding-bottom: 8px; }}
            .card-mand {{ background: #0b1528; border: 1px solid #ef4444; border-right: 5px solid #ef4444; border-radius: 10px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1); }}
            .badge-mand {{ background: #ef4444; color: #ffffff; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold; display: inline-block; }}
            .btn-mand {{ display: inline-block; background: #dc2626; color: #ffffff !important; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 13px; text-align: center; border: 1px solid #f87171; }}

            /* Tier 1 Special Badge */
            .tier1-tag {{ background: linear-gradient(135deg, #4f46e5, #7c3aed); color: #ffffff; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 10px; margin-right: 6px; display: inline-block; }}

            .details {{ font-size: 13.5px; line-height: 1.6; color: #cbd5e1; direction: rtl; text-align: right; }}
            .summary-box {{ background: #131f37; padding: 10px 12px; border-radius: 6px; margin: 8px 0; border-right: 3px solid #38bdf8; font-size: 13px; color: #e2e8f0; direction: rtl; text-align: right; }}
            .pro-list {{ color: #4ade80; margin: 4px 0; padding-right: 15px; font-size: 13px; direction: rtl; text-align: right; }}
            .gap-list {{ color: #fbbf24; margin: 4px 0; padding-right: 15px; font-size: 13px; direction: rtl; text-align: right; }}
            
            .footer {{ background: #080e1e; text-align: center; padding: 16px; font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; direction: rtl; }}
        </style>
    </head>
    <body dir="rtl" style="direction: rtl; text-align: right;">
        <div class="container" dir="rtl" style="direction: rtl; text-align: right;">
            <div class="header" dir="rtl">
                <h1>🚁 משרות מובילות בעולם הרחפנים והכטב"ם | עידו גל</h1>
                <p>סיכום יומי חכם מבוסס AI - מתועדף לפי חברות היעד המובילות (XTEND, Spear, רפאל, פרספטו)</p>
            </div>
            <div class="content" dir="rtl" style="direction: rtl; text-align: right;">
                
                <div class="tier-banner" dir="rtl">
                    🎯 <strong>תעדוף חברות פעיל:</strong> עדיפות עליונה ניתנת לחברות <strong>Tier 1 (XTEND, SpearUAV, רפאל)</strong> ו-<strong>Tier 2 (Percepto, NextVision, BlueBird, Airobotics)</strong> המתאימות במדויק לשילוב של הנדסאי מכונות, חבלה ופיקוד, ובקרה.
                </div>
    """

    def render_card(job, theme):
        score = job.get("match_score", 65)
        lic_note = job.get("license_note_hebrew", "")
        tier = job.get("tier_priority", 2)
        card_class = f"card-{theme}"
        badge_class = f"badge-{theme}"
        btn_class = f"btn-{theme}"

        tier_badge = '<span class="tier1-tag">⭐ חברת עדיפות Tier 1</span>' if tier == 1 else ""

        return f"""
            <div class="{card_class}" dir="rtl" style="direction: rtl; text-align: right;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #1e293b; padding-bottom: 6px; direction: rtl;">
                    <div>
                        <span class="{badge_class}">{score}% התאמה</span>
                        {tier_badge}
                    </div>
                    <a href="{job.get('link', '#')}" target="_blank" style="font-size: 16px; font-weight: bold; color: #ffffff; text-decoration: none;">{job.get('title', 'משרה')}</a>
                </div>
                <div class="details" dir="rtl">
                    <div style="margin-bottom: 6px;">
                        <span style="font-size: 12.5px; font-weight: 600; opacity: 0.9;">📌 סטטוס רישיון: {lic_note}</span>
                    </div>
                    <p style="margin: 4px 0;"><strong>חברה ומיקום:</strong> {job.get('company', '')} | {job.get('location', '')}</p>
                    <div class="summary-box">
                        <strong>תקציר המשרה:</strong> {job.get('summary_hebrew', '')}
                    </div>
                    <p style="margin-bottom: 2px; margin-top: 8px;"><strong>נקודות חוזק מהניסיון שלך:</strong></p>
                    <div class="pro-list">• {job.get('pros_hebrew', '')}</div>
                    
                    <p style="margin-bottom: 2px; margin-top: 8px;"><strong>דגשים / דרישות נוספות:</strong></p>
                    <div class="gap-list">• {job.get('gaps_hebrew', '')}</div>
                    
                    <div style="margin-top: 12px;">
                        <a href="{job.get('link', '#')}" target="_blank" class="{btn_class}">הגש מועמדות למשרה &larr;</a>
                    </div>
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
        # Group 1: None (Emerald)
        if cat_none:
            html += """
            <div class="category-box cat-box-none" dir="rtl">
                <div class="cat-header-none" dir="rtl">
                    <span>🟢 קטגוריה 1: ללא צורך ברישיון מטיס (אינטגרציה, מכניקה, בקרה וחשמל)</span>
                    <span style="font-size: 13px; font-weight: normal; opacity: 0.9;">""" + str(len(cat_none)) + """ משרות</span>
                </div>
            """
            for j in cat_none:
                html += render_card(j, "none")
            html += "</div>"

        # Group 2: Training Provided (Amber/Gold)
        if cat_training:
            html += """
            <div class="category-box cat-box-training" dir="rtl">
                <div class="cat-header-training" dir="rtl">
                    <span>🎓 קטגוריה 2: הכשרה והסמכה לרישיון מטיס ע"ח החברה</span>
                    <span style="font-size: 13px; font-weight: normal; opacity: 0.9;">""" + str(len(cat_training)) + """ משרות</span>
                </div>
            """
            for j in cat_training:
                html += render_card(j, "training_provided")
            html += "</div>"

        # Group 3: Advantage (Sky Blue)
        if cat_adv:
            html += """
            <div class="category-box cat-box-adv" dir="rtl">
                <div class="cat-header-adv" dir="rtl">
                    <span>🟡 קטגוריה 3: רישיון מטיס כיתרון בלבד (אינו דרישת סף)</span>
                    <span style="font-size: 13px; font-weight: normal; opacity: 0.9;">""" + str(len(cat_adv)) + """ משרות</span>
                </div>
            """
            for j in cat_adv:
                html += render_card(j, "adv")
            html += "</div>"

        # Group 4: Mandatory (Coral Red)
        if cat_mand:
            html += """
            <div class="category-box cat-box-mand" dir="rtl">
                <div class="cat-header-mand" dir="rtl">
                    <span>🔴 קטגוריה 4: רישיון מטיס מסחרי כדרישת סף</span>
                    <span style="font-size: 13px; font-weight: normal; opacity: 0.9;">""" + str(len(cat_mand)) + """ משרות</span>
                </div>
            """
            for j in cat_mand:
                html += render_card(j, "mand")
            html += "</div>"

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
    print("[+] Starting Drone & UAV Job Search Automation for Ido Gal (Prioritized Tiers + Licensing Categories)...")

    # 1. Load seen drone jobs history
    seen_drones = load_seen_drones()
    print(f"[+] Loaded {len(seen_drones)} active drone jobs in 14-day history.")

    # 2. Fetch fresh drone jobs prioritized by Tier 1 & 2
    raw_jobs = fetch_drone_jobs(seen_drones)
    print(f"[+] Retrieved {len(raw_jobs)} unique fresh drone job postings for analysis.")

    if not raw_jobs:
        print("[!] No new drone jobs found today.")
        return

    # 3. Evaluate with Gemini AI & classify licensing + tiers
    evaluated_jobs = evaluate_drone_jobs_with_gemini(raw_jobs)
    print(f"[+] Evaluated {len(evaluated_jobs)} matching drone jobs with Gemini AI.")

    # 4. Save newly sent jobs to history & weekly archive
    if evaluated_jobs:
        save_seen_drones(seen_drones, evaluated_jobs)

    # 5. Build & Dispatch HTML Email
    html_content = build_drone_html_email(evaluated_jobs)
    send_drone_email("🚁 משרות מובילות בעולם הרחפנים והכטב\"ם (מתועדף לפי חברות יעד) | עידו גל", html_content, "idogal0210@gmail.com")

if __name__ == "__main__":
    main()
