"""Salary Intelligence & Benchmark Engine for Job Search Automation.

Provides authoritative, multi-tier salary estimation for practical engineering,
energy, natural gas, SCADA, and UAV roles in Israel.

Strictly follows deterministic data extraction before model inference:
Tier 1: Direct extraction from job posting text (100% confidence).
Tier 2: Authoritative 2026 Israeli salary benchmark matrix tailored for
        certified Practical Engineers (הנדסאי מכונות, בוגר 2022, 2-4 שנות ניסיון).
Tier 3: Transparent 'Unspecified' when role is outside core sectors.
"""

import re
from typing import Dict, Any, Optional

# Verified Israeli Salary Surveys & Benchmarks (CPS Jobs, Nisha Cleantech, AllJobs, Ethosia)
CPS_SURVEY_URL = "https://www.cps.co.il/salary-survey"
ALLJOBS_SURVEY_URL = "https://www.alljobs.co.il/SalarySurvey.aspx"

BENCHMARK_MATRIX = {
    "scada_control_room": {
        "title": "חדר בקרה ו-SCADA (אנרגיה ותשתיות קריטיות)",
        "base_min": 13000,
        "base_max": 16000,
        "shift_min": 16000,
        "shift_max": 21000,
        "source": "סקר שכר CPS Jobs ונישה: מפעילי חדר בקרה ו-SCADA (2-4 שנות ניסיון)",
        "url": CPS_SURVEY_URL,
    },
    "natural_gas": {
        "title": "גז טבעי ותחנות כוח",
        "base_min": 14000,
        "base_max": 18500,
        "shift_min": 17000,
        "shift_max": 22000,
        "source": "סקר שכר ענפי תשתיות וגז טבעי (הנדסאי מוסמך 2-4 שנות ניסיון)",
        "url": CPS_SURVEY_URL,
    },
    "solar_bess": {
        "title": "סולארי ואגירת אנרגיה (PV / BESS)",
        "base_min": 12500,
        "base_max": 16500,
        "shift_min": 14500,
        "shift_max": 18500,
        "has_vehicle_norm": True,
        "source": "סקר שכר נישה קלינטק: טכנאי והנדסאי שטח O&M סולאר ואגירה",
        "url": CPS_SURVEY_URL,
    },
    "drones_cuas": {
        "title": "רחפנים, כטב״ם ומערכות C-UAS",
        "base_min": 14000,
        "base_max": 19000,
        "shift_min": 16000,
        "shift_max": 21000,
        "source": "סקר שכר תעשיות ביטחוניות וכטב״ם: אינטגרציה וניסויי טיסה",
        "url": CPS_SURVEY_URL,
    },
    "power_plant_maintenance": {
        "title": "אחזקת תחנות כוח וציוד סובב",
        "base_min": 12500,
        "base_max": 16500,
        "shift_min": 15000,
        "shift_max": 19500,
        "source": "סקר שכר ענף האנרגיה: מכונאי אחזקה והנדסאי תחנות כוח",
        "url": CPS_SURVEY_URL,
    },
    "industrial_operations": {
        "title": "תפעול, אחזקה ומכונות תעשייתיות",
        "base_min": 11500,
        "base_max": 15000,
        "shift_min": 13500,
        "shift_max": 17500,
        "source": "סקר שכר AllJobs ו-CPS: הנדסאי מכונות ושירות שטח",
        "url": ALLJOBS_SURVEY_URL,
    },
}

SHIFT_KEYWORDS = [
    "משמרות", "סבב משמרות", "24/7", "7/24", "לילות", "לילה", "סופי שבוע",
    "שבתות", "משמרת לילה", "עבודה במשמרות", "shifts", "shift work", "shift"
]

COMPANY_CAR_KEYWORDS = [
    "רכב צמוד", "רכב חברה", "כולל רכב", "רכב שירות", "רכב צמוד מלא",
    "company car", "vehicle"
]

ON_CALL_KEYWORDS = [
    "כוננויות", "כוננות", "קריאות פתע", "on-call", "on call"
]


def detect_shifts(text: str) -> bool:
    """Check if the job posting explicitly mentions shift work."""
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in SHIFT_KEYWORDS)


def detect_company_car(text: str) -> bool:
    """Check if the job posting mentions a company vehicle."""
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in COMPANY_CAR_KEYWORDS)


def detect_on_call(text: str) -> bool:
    """Check if on-call duty is mentioned."""
    if not text:
        return False
    lower = text.lower()
    return any(kw in lower for kw in ON_CALL_KEYWORDS)


def extract_salary_from_ad(text: str) -> Optional[Dict[str, Any]]:
    """
    Tier 1 Parser: Extracts explicit salary statements directly from job text.
    Handles ranges in thousands, direct monthly NIS amounts, and hourly wages.
    """
    if not text:
        return None

    # Pattern A: Monthly range with explicit numbers (e.g. 14,000 - 18,000 ₪ or 14000-18000)
    match_range = re.search(
        r'(\d{1,2})[,.]?000\s*[-–עדto]+\s*(\d{1,2})[,.]?000\s*(?:₪|ש"ח|שח|שקלים|nis)?',
        text,
        re.IGNORECASE
    )
    if match_range:
        num1 = int(match_range.group(1)) * 1000
        num2 = int(match_range.group(2)) * 1000
        low = min(num1, num2)
        high = max(num1, num2)
        return {
            "salary_range": f"{low:,} - {high:,} ₪",
            "salary_source_type": "job_ad",
            "salary_source_label": "פורסם במודעת המשרה",
            "salary_source_url": "",
            "salary_evidence": f"שכר שפורסם במפורש בגוף מודעת המשרה ({low:,} - {high:,} ₪ בחודש).",
            "salary_confidence": "high",
            "quality_level": "high",
            "quality_reasons": ["שכר נקוב שפורסם ישירות בגוף מודעת המשרה על ידי המעסיק"],
            "estimate_type": "advertised",
            "compensation_basis": "gross_base",
            "pay_period": "month",
            "extracted_min": low,
            "extracted_max": high,
            "p25": low,
            "p50": (low + high) // 2,
            "p75": high,
        }

    # Pattern B: Notation with 'K' (e.g. 15k - 18k or 15K-18K)
    match_k = re.search(
        r'(\d{1,2})\s*[kK]\s*[-–עדto]+\s*(\d{1,2})\s*[kK]',
        text
    )
    if match_k:
        low = min(int(match_k.group(1)), int(match_k.group(2))) * 1000
        high = max(int(match_k.group(1)), int(match_k.group(2))) * 1000
        return {
            "salary_range": f"{low:,} - {high:,} ₪",
            "salary_source_type": "job_ad",
            "salary_source_label": "פורסם במודעת המשרה (אמינות 100%)",
            "salary_source_url": "",
            "salary_evidence": f"שכר שפורסם במפורש במודעה בקיצור אלפים ({match_k.group(0)}).",
            "salary_confidence": "high",
            "quality_level": "high",
            "quality_reasons": ["שכר נקוב שפורסם ישירות במודעה בקיצור אלפים"],
            "estimate_type": "advertised",
            "compensation_basis": "gross_base",
            "pay_period": "month",
            "extracted_min": low,
            "extracted_max": high,
            "p25": low,
            "p50": (low + high) // 2,
            "p75": high,
        }

    # Pattern C: Explicit single monthly amount (e.g. שכר של 16,000 ש"ח או שכר 15000)
    match_single = re.search(
        r'(?:שכר|משכורת|שכר בסיס)\s*(?:של|:)?\s*(\d{1,2})[,.]?000\s*(?:₪|ש"ח|שח|שקלים|nis)?',
        text,
        re.IGNORECASE
    )
    if match_single:
        amount = int(match_single.group(1)) * 1000
        low = int(amount * 0.95)
        high = int(amount * 1.05)
        return {
            "salary_range": f"{amount:,} ₪",
            "salary_source_type": "job_ad",
            "salary_source_label": "פורסם במודעת המשרה (אמינות 100%)",
            "salary_source_url": "",
            "salary_evidence": f"שכר נקוב שפורסם במפורש במודעה ({amount:,} ₪).",
            "salary_confidence": "high",
            "quality_level": "high",
            "quality_reasons": ["שכר נקוב שפורסם ישירות במודעת המשרה על ידי המעסיק"],
            "estimate_type": "advertised",
            "compensation_basis": "gross_base",
            "pay_period": "month",
            "extracted_min": low,
            "extracted_max": high,
            "p25": low,
            "p50": amount,
            "p75": high,
        }

    # Pattern D: Hourly rate (e.g. 55 ש"ח לשעה -> converted to standard 182 monthly hours)
    match_hourly = re.search(
        r'(\d{2,3})\s*(?:₪|ש"ח|שח|שקלים)\s*(?:לשעה|שעה|שעתי)',
        text
    )
    if match_hourly:
        hourly = int(match_hourly.group(1))
        monthly = hourly * 182
        return {
            "salary_range": f"{monthly:,} ₪ (לפי {hourly} ₪/שעה)",
            "salary_source_type": "job_ad",
            "salary_source_label": "פורסם במודעת המשרה (שכר שעתי)",
            "salary_source_url": "",
            "salary_evidence": f"שכר שעתי נקוב של {hourly} ₪ לשעה במשרה מלאה (182 שעות חודשיות = {monthly:,} ₪ ברוטו).",
            "salary_confidence": "high",
            "quality_level": "high",
            "quality_reasons": ["שכר שעתי נקוב שפורסם במודעת המשרה (חישוב לפי 182 שעות חודשיות במשרה מלאה)"],
            "estimate_type": "advertised",
            "compensation_basis": "gross_base",
            "pay_period": "hour",
            "extracted_min": monthly,
            "extracted_max": monthly,
            "p25": monthly,
            "p50": monthly,
            "p75": monthly,
        }

    return None


def classify_role_category(title: str, sector_key: str, snippet: str) -> str:
    """Classifies the job into the most accurate benchmark category."""
    combined = f"{title} {sector_key} {snippet}".lower()

    if any(k in combined for k in [
        "scada", "בקר scada", "חדר בקרה", "מוקד בקרה", "בקרת מבנה", "bms", "noc",
        "בקרה ואוטומציה", "הנדסאי בקרה", "תכנת בקרה", "בקר plc", "hmi", "בקר תהליך"
    ]):
        return "scada_control_room"

    if any(k in combined for k in [
        "גז טבעי", "הולכת גז", "מפחיתות", "cng", "prms", "natural gas", "מתקן גז", "צנרת גז"
    ]):
        return "natural_gas"

    if any(k in combined for k in [
        "רחפן", "רחפנים", "כטב\"ם", "כטבם", "uav", "drone", "c-uas", "cuas", "מטע\"ד", "ניסויי טיסה"
    ]):
        return "drones_cuas"

    if any(k in combined for k in [
        "סולאר", "סולארי", "פוטו-וולטאי", "אגירת אנרגיה", "bess", "pv", "solar", "אנרגיות מתחדשות", "קלינטק"
    ]):
        return "solar_bess"

    if any(k in combined for k in [
        "תחנת כוח", "תחנות כוח", "ציוד סובב", "טורבינה", "מכונאי תחנת כוח", "power plant", "מתח גבוה", "מתח עליון"
    ]):
        return "power_plant_maintenance"

    if any(k in combined for k in [
        "מכונות", "הנדסאי מכונות", "טכנאי שירות", "אינטגרטור", "אלקטרו-מכני", "תפעול", "אחזקה"
    ]):
        return "industrial_operations"

    return "unspecified"


def evaluate_job_salary(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Authoritative Multi-Tier Salary Intelligence Evaluator.
    Evaluates tier 1 (ad extraction), tier 2 (benchmark matrix + perks), or tier 3 (neutral abstention).
    """
    title = str(job.get("title", ""))
    company = str(job.get("company", ""))
    snippet = str(job.get("snippet", ""))
    sector_key = str(job.get("sector_key", ""))
    full_text = f"{title} {snippet}"

    # Tier 1: Direct Ad Extraction
    ad_sal = extract_salary_from_ad(full_text)
    if ad_sal:
        return ad_sal

    has_shifts = detect_shifts(full_text)
    has_car = detect_company_car(full_text)
    has_on_call = detect_on_call(full_text)

    # Tier 2: Benchmark Matrix
    cat_key = classify_role_category(title, sector_key, snippet)
    if cat_key == "unspecified" or cat_key not in BENCHMARK_MATRIX:
        # Graceful Abstention (No fabricated salary numbers)
        return {
            "salary_range": "לא צוין במודעה",
            "salary_source_type": "none",
            "salary_source_label": "לא צוין שכר",
            "salary_source_url": "",
            "salary_evidence": "מודעת המשרה אינה מציינת שכר, ולא קיימים נתוני סקר ענפיים מוסמכים לתפקיד זה.",
            "salary_confidence": "insufficient",
            "quality_level": "insufficient",
            "quality_reasons": ["מודעת המשרה אינה כוללת שכר נקוב", "התפקיד אינו משויך לטבלאות השכר המאושרות"],
            "estimate_type": "insufficient_data",
            "compensation_basis": "unknown",
            "pay_period": "month",
            "has_shifts": has_shifts,
            "has_company_car": has_car,
            "has_on_call": has_on_call,
            "p25": None,
            "p50": None,
            "p75": None,
        }

    bench = BENCHMARK_MATRIX[cat_key]
    has_car = has_car or bench.get("has_vehicle_norm", False)

    # For SCADA and control room roles, shifts are very common
    if cat_key == "scada_control_room":
        # If control room mentions shifts or 24/7 or is a typical operator role
        if has_shifts or "מפעיל" in title or "בקר" in title or "operator" in title.lower():
            sal_min = bench["shift_min"]
            sal_max = bench["shift_max"]
            sal_range = f"{sal_min:,} - {sal_max:,} ₪"
            evidence = (
                f"מבוסס סקר שכר CPS ונישה למפעילי חדר בקרה ו-SCADA (2-4 שנות ניסיון). "
                f"כולל תוספת משמרות 24/7, שבתות ושעות נוספות (שכר בסיס ללא משמרות: {bench['base_min']:,} - {bench['base_max']:,} ₪)."
            )
            label = "סקר ענפי 2026 • כולל משמרות 24/7"
        else:
            sal_min = bench["base_min"]
            sal_max = bench["base_max"]
            sal_range = f"{sal_min:,} - {sal_max:,} ₪"
            evidence = f"מבוסס סקר שכר CPS ונישה למהנדסי/בקרי SCADA במשרת יום (2-4 שנות ניסיון)."
            label = "סקר ענפי 2026 • משרת יום"
    else:
        if has_shifts:
            sal_min = bench["shift_min"]
            sal_max = bench["shift_max"]
            sal_range = f"{sal_min:,} - {sal_max:,} ₪"
            evidence = f"מבוסס סקר שכר ענפי מוסמך להנדסאי (2-4 שנות ניסיון), כולל תוספת עבודת משמרות."
            label = "סקר ענפי 2026 • כולל משמרות"
        else:
            sal_min = bench["base_min"]
            sal_max = bench["base_max"]
            sal_range = f"{sal_min:,} - {sal_max:,} ₪"
            car_note = " + רכב צמוד" if has_car else ""
            evidence = f"מבוסס סקר שכר מוסמך 2026 להנדסאי מכונות/תשתיות עם 2-4 שנות ניסיון{car_note}."
            label = "סקר ענפי 2026 • הנדסאי 2-4 שנים"

    if has_car:
        sal_range += " + רכב צמוד"

    return {
        "salary_range": sal_range,
        "salary_source_type": "sector_benchmark",
        "salary_source_label": label,
        "salary_source_url": bench["url"],
        "salary_evidence": evidence,
        "salary_confidence": "medium",
        "quality_level": "medium",
        "quality_reasons": ["מבוסס סקר שכר ענפי מוסמך 2026 להנדסאים (2-4 שנות ניסיון)", f"התאמה למגזר: {bench['title']}"],
        "estimate_type": "market_estimate",
        "compensation_basis": "gross_base",
        "pay_period": "month",
        "has_shifts": has_shifts,
        "has_company_car": has_car,
        "has_on_call": has_on_call,
        "p25": sal_min,
        "p50": (sal_min + sal_max) // 2,
        "p75": sal_max,
    }
