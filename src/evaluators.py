import json
import time
from google.genai import types

CV_CONTEXT = """
Name: Ido Gal (עידו גל)
Title: Gas Controller - Operations & Product (בקר גז - תפעול ומוצר) & Energy Systems | Practical Mechanical Engineer | Real-Time Control & Supply Continuity
Education: Practical Mechanical Engineer, Natural Gas & Green Energy (הנדסאי מכונות, התמחות בגז טבעי ובאנרגיה ירוקה), Ruppin Academic Center (2024). Certified Electrician Studies (2026 - לקראת סיום הלימודים, חודשיים). NOT a B.Sc. Engineer!
Skills: Real-time 24/7 SCADA & gas control, pressure/flow monitoring, nomination allocations, Excel, SAP, Python, Gemini/Copilot AI automation, Nahal Reconnaissance demolitions/combat engineering (סיירת נח"ל).
"""

NON_TECHNICAL_TITLES = [
    "שיווק", "מנהל מותג", "מנהלת מותג", "משאבי אנוש", "רכזת גיוס", "רכז גיוס", "גיוס עובדים",
    "הנהלת חשבונות", "מנהל חשבונות", "מנהלת חשבונות", "רואה חשבון", "רואת חשבון", "חשב שכר", "חשבת שכר",
    "יועץ משפטי", "יועצת משפטית", "עורך דין", "עורכת דין", "משפטי", "סיעוד", "אח מוסמך", "אחות מוסמכת",
    "רופא", "רופאה", "רוקח", "רוקחת", "מכירות טלפוניות", "טלמרקטינג", "נציג שירות", "נציגת שירות",
    "נציג מכירות", "נציגת מכירות", "מוקד", "קופאי", "קופאית", "מלצר", "מלצרית", "מזכיר", "מזכירה",
    "מנהל משרד", "מנהלת משרד", "קוסמטיקה", "טיפוח", "ביוטי", "רכש", "קניין", "קניינית",
    "ניקיון", "עובד ניקיון", "עובדת ניקיון", "בוחן חיובים", "בוחנת חיובים", "מנתח מערכות data",
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

    Evaluation & Screening Rules:
    1. B.Sc. REQUIREMENT & FLEXIBILITY:
       - Ido is a certified Practical Mechanical Engineer (הנדסאי מכונות), NOT a B.Sc. engineer.
       - ONLY allow B.Sc.-titled jobs if you identify genuine flexibility, practical openness, or if the company is known to accept experienced practical engineers (הנדסאים).
    2. DOMAIN PREFERENCES:
       - Energy: Give a strong preference / bonus to Solar PV, Energy Storage (BESS), Energy Tech and Natural Gas opportunities.
    3. MATCH SCORING (0-100):
       - Score objectively based on Ido's genuine background.

    Return STRICT JSON with keys:
    1. "match_score": integer (0 to 100).
    2. "concrete_matches_count": integer (0 to 10).
    3. "reasoning": 1-2 sentence Hebrew justification.
    4. "sector_key": one of ["energy", "drones", "cuas", "avionics", "other"].
    5. "sector": Hebrew sector title e.g. "⚡ תשתיות אנרגיה, גז טבעי ו-SCADA" or "🚁 רחפנים וכטב״ם אוטונומי".
    6. "location": Hebrew location in 2-4 words.
    7. "company_domain_product": 10-15 words Hebrew concise summary strictly describing the company's core domain and product.
    8. "job_summary": 2-3 sentence Hebrew concise summary of core job duties and responsibilities.
    9. "experience_strengths": 1-2 sentence Hebrew tailored strengths mapping.
    10. "key_highlights": 1-2 sentence Hebrew highlights.
    11. "company_size": string.
    12. "junior_openness": string.
    13. "work_model": string.
    14. "company_requirements": 1-2 sentence Hebrew summary of company requirements (degree/practical engineer, required experience, certifications, and technical tools).
    """

    time.sleep(1.5)

    health_metrics.gemini_attempts += 1

    models_to_try = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
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
            req_keys = ["match_score", "concrete_matches_count", "reasoning", "sector_key"]
            if not all(k in data for k in req_keys):
                print(f"[VALIDATION] Missing keys in Gemini response from {model_name}")
                continue

            if not isinstance(data.get("match_score"), int) or not isinstance(data.get("concrete_matches_count"), int):
                print(f"[VALIDATION] Type error in Gemini response from {model_name}")
                continue

            health_metrics.gemini_successes += 1

            # Post-Gemini Python Deterministic Enforcement
            if data["concrete_matches_count"] < 3:
                print(f"[VALIDATION] Job disqualified (concrete matches < 3): {company} - {title}")
                return None

            return data

        except Exception as e:
            err_str = str(e)
            # Circuit Breaker: Hard daily quota exhaustion (429 + "quota" keyword).
            # Retrying other models wastes the remaining quota — raise immediately
            # so the caller can skip Gemini for all remaining jobs in this run.
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and "quota" in err_str.lower():
                print(f"[CIRCUIT BREAKER] Daily quota exhausted on {model_name}. Skipping all remaining Gemini calls.")
                health_metrics.gemini_failures += 1
                raise QuotaExhaustedError(f"Daily quota exhausted: {err_str}") from e
            # Transient errors (503 overload, network blip) → try next model.
            print(f"[GEMINI] Transient failure with {model_name}: {e}. Trying next model.")
            continue

    print(f"[ERROR] All Gemini models failed for {company} - {title}.")
    health_metrics.gemini_failures += 1
    return None
