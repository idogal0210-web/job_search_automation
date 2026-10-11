import json
import time
from google.genai import types

CV_CONTEXT = """
Candidate: Ido Gal (עידו גל)
Core Profile: Multidisciplinary Technical Professional & Practical Mechanical Engineer with Deep Specialization in Energy Systems (Natural Gas, Solar PV, BESS Energy Storage), Real-Time Operations Control (SCADA / NOC / 24/7 Control Rooms), Electrical Studies (Certified Electrician in progress), and Combat Engineering / Tactical Field Operations Leadership (סיירת נח"ל).
Education & Credentials:
- Certified Practical Mechanical Engineer (הנדסאי מכונות), Natural Gas & Green Energy Specialization, Ruppin Academic Center (2024).
- Certified Electrician Studies (חשמלאי מוסמך - לקראת סיום ההסמכה).
- Military: Combat Engineering / Demolitions & Breaching Team Leader, Nahal Reconnaissance (סיירת נח"ל).
Key Competencies:
- Energy & Utilities: Natural gas transmission/distribution control, nomination allocations, pressure/flow monitoring, solar PV field systems, battery storage (BESS), clean-tech integration.
- Operations, C2 & SCADA: 24/7 mission-critical control room operations, crisis response, supply continuity, process automation.
- Field, Integration & Hands-on: Electro-mechanical systems, site supervision, equipment commissioning, troubleshooting, drone/UAV integration and flight operations.
- Tech & AI: Python automation, Gemini/Copilot AI workflows, SAP, Excel data modeling.
"""

NON_TECHNICAL_TITLES = [
    "שיווק", "מנהל מותג", "מנהלת מותג", "משאבי אנוש", "רכזת גיוס", "רכז גיוס", "גיוס עובדים",
    "הנהלת חשבונות", "מנהל חשבונות", "מנהלת חשבונות", "רואה חשבון", "רואת חשבון", "חשב שכר", "חשבת שכר",
    "יועץ משפטי", "יועצת משפטית", "עורך דין", "עורכת דין", "משפטי", "סיעוד", "אח מוסמך", "אחות מוסמכת",
    "רופא", "רופאה", "רוקח", "רוקחת", "מכירות טלפוניות", "טלמרקטינג", "נציג שירות", "נציגת שירות",
    "נציג מכירות", "נציגת מכירות", "מוקד", "מוקדן רואה", "מוקדן מצלמות", "בקר מצלמות", "סייר מוקד", "מוקדן ביטחון", "מוקדן אבטחה", "מוקד 106", "קופאי", "קופאית", "מלצר", "מלצרית", "מזכיר", "מזכירה",
    "מנהל משרד", "מנהלת משרד", "קוסמטיקה", "טיפוח", "ביוטי", "רכש", "קניין", "קניינית",
    "ניקיון", "עובד ניקיון", "עובדת ניקיון", "בוחן חיובים", "בוחנת חיובים", "מנתח מערכות data", "cctv operator", "security dispatcher",
    "brand manager", "marketing", "digital marketing", "social media", "seo", "human resources",
    "talent acquisition", "recruiter", "sourcer", "accountant", "bookkeeper", "payroll",
    "finance manager", "cfo", "legal counsel", "attorney", "lawyer", "compliance officer",
    "nurse", "nursing", "physician", "pharmacist", "sales representative", "telemarketing",
    "customer service", "customer support", "cashier", "receptionist", "office manager", "cosmetics", "beauty",
    "user acquisition", "procurement", "buyer", "cleaner", "tax preparer", "service desk",
    "bi analyst", "data analyst", "full stack", "web developer", "frontend", "backend", "software developer",
    "copywriter", "content writer", "salesperson", "sales manager", "product designer", "country club", "crm dynamics",
    "collections", "salesforce", "account manager", "brand marketing", "vp of sales", "sales"
]


class QuotaExhaustedError(Exception):
    """Raised when the Gemini API daily quota is confirmed exhausted.
    Signals the caller to activate the circuit breaker and skip Gemini
    for ALL remaining jobs in this run, going straight to keyword fallback.
    """
    pass


def evaluate_and_enrich_job_with_gemini(client, title, company, snippet, is_drone, health_metrics):
    title_lower = title.lower()
    company_lower = company.lower()

    # Deterministic Pre-Filters
    for bl in ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון"]:
        if bl in company_lower:
            print(f"[FILTER] Disqualifying Blacklist: {company} - {title}")
            return None

    for non_tech in NON_TECHNICAL_TITLES:
        if non_tech in title_lower:
            print(f"[FILTER] Disqualifying non-technical role: {company} - {title} ('{non_tech}')")
            return None

    prompt = f"""
    You are an expert AI Technical Career Coach evaluating a job opportunity for Ido Gal.

    Candidate Profile (Source of Truth):
    {CV_CONTEXT}

    Target Job Details:
    - Title: {title}
    - Company: {company}
    - Snippet/Description: {snippet}
    - Is Drone/Defense domain: {is_drone}

    Evaluation & Screening Rules (Cognitive & Domain Flexibility):
    1. COGNITIVE & DOMAIN FLEXIBILITY (גמישות מחשבתית):
       - DO NOT restrict matches solely to jobs explicitly titled "הנדסאי מכונות".
       - Actively match and value diverse technical and operational roles connected to Ido's multidisciplinary foundation:
         * Energy, Solar & Utilities: Solar PV, Energy Storage (BESS), Natural Gas, Power Stations, Cleantech, Microgrids, EV Infrastructure.
         * Field Leadership & Execution: Site Inspection & Construction Supervision (פיקוח הקמה / אתרים), Commissioning (מסירה והפעלה), Field Service & O&M.
         * Real-Time Operations & C2: Control Room Operator, NOC/OCC Controller, Supply Continuity Controller, Technical Operations Coordinator.
         * Autonomous & Tactical Systems: Drone/UAV Integrator, Field Testing & Flight Operator, Payload/Robotics Technician, Counter-UAS (C-UAS).
         * Technical Projects & Coordination: Multidisciplinary Project Coordinator, Technical Site Supervisor, Operations Specialist.
    2. B.Sc. REQUIREMENT & PRAGMATIC REALISM:
       - Ido is a certified Practical Engineer with strong hands-on and operational experience.
       - If a job mentions B.Sc. or "מהנדס/ת" but the actual day-to-day work is operational, commissioning, field supervision, integration, or control room dispatch where practical engineering and real-world execution matter more than theoretical R&D/academic research — DO NOT disqualify! Award a solid match score and highlight how his practical background provides immediate execution value.
       - Disqualify only if the role strictly requires academic R&D/deep algorithmic development or purely theoretical design with zero operational/practical aspect.
    3. STRICT CONTROL ROOM FILTERING RULE (חדר בקרה):
       - Ido is an experienced gas controller at Energean specializing in mission-critical SCADA operations.
       - If a target job is a Control Room / Monitoring / Dispatch role (חדר בקרה, בקר, מפעיל חדר בקרה, מוקד בקרה, control room):
         DO NOT qualify or recommend it UNLESS:
         a) It explicitly involves SCADA, industrial telemetry, PLC, HMI, BMS, or critical infrastructure (גז, חשמל, אנרגיה, מים, מתקנים תעשייתיים).
         OR
         b) It offers a very high salary (שכר גבוה מאוד - 18,000+ ₪ ומעלה).
       - Generic security camera monitoring (מוקד רואה/מצלמות), municipal/parking dispatch, or low-level/minimum-wage control room positions MUST BE DISQUALIFIED (match_score = 0, concrete_matches_count = 0)!
    4. DOMAIN PREFERENCES:
       - Strong preference and bonus for Solar PV, Energy Storage (BESS), Natural Gas, C-UAS/Drone operations, and Mission-Critical Control.
    5. MATCH SCORING (0-100):
       - Score based on whether Ido can realistically succeed and thrive in this role given his multidisciplinary toolkit.

    Return STRICT JSON with keys:
    1. "match_score": integer (0 to 100).
    2. "concrete_matches_count": integer (0 to 10).
    3. "reasoning": 1-2 sentence Hebrew justification.
    4. "sector_key": one of ["solar", "natural_gas", "energy_tech", "drones", "cuas", "scada", "operations", "energy", "other"].
    5. "sector": Hebrew sector title (e.g. "☀️ PV ומערכות סולאריות", "🏭 גז טבעי ותשתיות", "🔋 אגירת אנרגיה", "🚁 רחפנים", "🛡️ מערכות C-UAS", "⚙️ בקרה ו-SCADA", "🔧 תפעול ואחזקה", "🏗️ פיקוח והקמה").
    6. "location": Hebrew location in 2-4 words.
    7. "company_domain_product": 10-15 words Hebrew concise summary strictly describing the company's core domain and product.
    8. "job_summary": 2-3 sentence Hebrew concise summary of core job duties and responsibilities.
    9. "experience_strengths": 1-2 sentence Hebrew tailored strengths mapping.
    10. "key_highlights": 1-2 sentence Hebrew highlights.
    11. "company_size": string.
    12. "junior_openness": string.
    13. "work_model": string.
    14. "company_requirements": 1-2 sentence Hebrew summary of company requirements.
    15. "salary_range": Hebrew string for monthly salary range in NIS (e.g. "13,000 - 16,000 ₪").
    16. "salary_source_type": one of ["company_verified", "job_ad", "sector_benchmark"].
        - "job_ad": ONLY if the job description snippet explicitly states a salary figure.
        - "company_verified": ONLY if there are verified crowdsourced/public reports (Glassdoor, Indeed, collective agreements, major financial publications) for {company} in Israel for technicians/practical engineers/service operators.
        - "sector_benchmark": If NO verified company-specific salary reports exist for {company} in Israel. DO NOT INVENT A NUMBER FOR THE COMPANY. Use the realistic Israeli market benchmark for this role (e.g. practical engineer: 11,000-14,000 ₪, SCADA/gas: 13,000-17,000 ₪, drone/defense: 14,000-18,000 ₪).
    17. "salary_source_label": Hebrew short label.
        - If company_verified: "מבוסס דיווחי שכר ב-{company}"
        - If job_ad: "פורסם במודעת המשרה"
        - If sector_benchmark: "הערכת ענף (אין דיווחי שכר פומביים ל-{company})"
    18. "salary_source_url": URL for verification.
        - If company_verified: "https://www.google.com/search?q=" + URL-encoded search query for company + role + salary Israel
        - If sector_benchmark: "https://www.google.com/search?q=טבלת+שכר+הנדסאי+מכונות+ישראל"
        - If job_ad: ""
    19. "salary_evidence": 1 sentence Hebrew summary explaining the evidence and basis for the figure.
    """

    time.sleep(1.5)

    health_metrics.gemini_attempts += 1

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
    ]

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            data = json.loads(response.text)

            # Validation
            req_keys = ["match_score", "concrete_matches_count", "reasoning", "sector_key", "salary_range"]
            if not all(k in data for k in req_keys):
                print(f"[VALIDATION] Missing keys in Gemini response from {model_name}")
                continue

            if not isinstance(data.get("match_score"), int) or not isinstance(data.get("concrete_matches_count"), int):
                print(f"[VALIDATION] Type error in Gemini response from {model_name}")
                continue

            # Ensure salary intelligence defaults
            if not data.get("salary_source_type"):
                data["salary_source_type"] = "sector_benchmark"
            if not data.get("salary_source_label"):
                data["salary_source_label"] = f"הערכת ענף (אין דיווחי שכר פומביים ל-{company})"
            if not data.get("salary_source_url"):
                data["salary_source_url"] = "https://www.google.com/search?q=טבלת+שכר+הנדסאי+מכונות+ישראל"
            if not data.get("salary_evidence"):
                data["salary_evidence"] = "מבוסס על סקרי שכר ענפיים של חברות השמה (CPS/נישה/אתגר) להנדסאי מכונות ותפעול בישראל."

            health_metrics.gemini_successes += 1
            print(f"[AI] Successfully evaluated using {model_name}")


            # Post-Gemini Python Deterministic Enforcement
            # 1. Minimum matches and score
            if data["concrete_matches_count"] < 2 or data.get("match_score", 0) < 50:
                print(f"[VALIDATION] Job disqualified (insufficient matches or low score): {company} - {title}")
                data["match_score"] = 0
                return data

            # 2. Strict Control Room Guardrail: Disqualify control room roles without SCADA or high salary (>= 18k)
            is_control_room = any(k in title_lower or k in snippet.lower() for k in ["חדר בקרה", "מוקד בקרה", "בקרת חדר", "control room"])
            if is_control_room:
                full_text_lower = f"{title_lower} {snippet.lower()} {str(data.get('job_summary', '')).lower()}"
                has_scada = any(k in full_text_lower for k in ["scada", "סקאדה", "plc", "hmi", "bms", "טלמטריה", "תשתיות", "גז", "אנרגיה", "טורבינ", "חשמל", "תחנת כוח"])
                import re
                salary_str = str(data.get("salary_range", ""))
                salary_nums = [int(n) for n in re.findall(r"\b(\d{2}),000\b", salary_str)]
                has_high_salary = any(n >= 18 for n in salary_nums)
                if not has_scada and not has_high_salary:
                    print(f"[FILTER] Disqualifying Control Room job lacking SCADA or high salary: {company} - {title}")
                    data["match_score"] = 0
                    return data

            return data

        except Exception as e:
            err_str = str(e)
            is_last_model = (model_name == models_to_try[-1])

            # If it's a hard quota exhaustion or overload on the final fallback model,
            # trip the circuit breaker for all subsequent jobs in this run.
            if is_last_model:
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and "quota" in err_str.lower():
                    print(f"[CIRCUIT BREAKER] Daily quota exhausted across all models. Skipping all remaining Gemini calls.")
                    health_metrics.gemini_failures += 1
                    raise QuotaExhaustedError(f"Daily quota exhausted: {err_str}") from e
                elif "503" in err_str or "UNAVAILABLE" in err_str:
                    print(f"[CIRCUIT BREAKER] All models overloaded (503). Skipping Gemini for this run.")
                    health_metrics.gemini_failures += 1
                    raise QuotaExhaustedError(f"API Overloaded (503): {err_str}") from e

            # Otherwise, log and proceed to the next fallback model
            print(f"[GEMINI] {model_name} unavailable ({err_str[:80]}...). Trying next fallback model.")
            continue

    print(f"[ERROR] All Gemini models failed for {company} - {title}.")
    health_metrics.gemini_failures += 1
    return None
