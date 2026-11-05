import os
import re

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


# Ambiguous words must not disqualify a technical title by themselves.
AMBIGUOUS = {
    "sales", "customer support", "service desk", "מוקד", "רכש", "קניין", "קניינית",
    "סליקה", "מנייה", "התחשבנות", "billing", "settlement", "commercial"
}
TECHNICAL = (
    r"\b(?:technical|engineer|technician|scada|plc|hmi|bms|aveva|operator|operations|dispatcher|"
    r"bess|grid|commercial|nominations?|renominations?|settlement|billing|energy|solar|gas|pv)\b|"
    r"הנדסאי|מהנדס|טכנאי|טכני|בקרה|תפעול|משמרת|רשת|גז|אנרגיה|סולאר|אגירה|רנומינצי|נומינצי|מנייה|התחשבנות|סליקה|מתקנ"
)

from src.config import get_excluded_employers

# Excluded employers: defaults with environment override via EXCLUDED_EMPLOYERS
_env_blacklist = os.environ.get("EXCLUDED_EMPLOYERS", "")
if _env_blacklist:
    BLACKLIST = [e.strip().lower() for e in _env_blacklist.split(",") if e.strip()]
else:
    BLACKLIST = get_excluded_employers()

KNOWN_ENTERPRISE_EMPLOYERS = {
    "opc", "dalia", "דליה", "או פי סי", "enlight", "אנלייט", "energix", "אנרג'יקס", "אנרגיקס",
    "ormat", "אורמת", "doral", "דוראל", "nofar", "נופר", "שיכון ובינוי", "shikun & binui",
    "shikun vebinui", "econergy", "אקונרג'י", "teralight", "טראילייט", "solaredge", "סולאראדג'",
    "סולאראדג", "supergas", "סופרגז", "rimon", "רימון", "newmed", "ניו-מד", "ניומד", "isramco",
    "ישראמקו", "edeltech", "אדלטק", "ecoppia", "אקופיה", "robotican", "רובוטיקאן", "percepto",
    "פרספטו", "xtend", "אקסטנד", "elbit", "אלביט", "rafael", "רפאל", "iai", "תעשייה אווירית",
    "תעשיה אווירית", "תע\"א", "חברת החשמל", "חח\"י", "iec", "מקורות", "mekorot", "בזן", "bazan"
}

def is_known_enterprise(company_name):
    if not company_name:
        return False
    c = company_name.lower().strip()
    return any(has_term(c, term) for term in KNOWN_ENTERPRISE_EMPLOYERS)

KEYWORD_GROUPS = {
    "gas": ["natural gas", "גז טבעי", "מתקני גז", "מתקן גז", "prms"],
    "energy": ["energy", "אנרגיה", "תחנת כוח", "power plant", "תשתיות אנרגיה"],
    "mechanical": ["mechanical", "מכונות", "מכונאי", "ציוד סובב", "מתקני לחץ"],
    "control": ["scada", "plc", "hmi", "bms", "aveva", "בקרה", "אוטומציה"],
    "solar": ["solar", "pv", "סולארי", "פוטו", "פוטו-וולטאי", "bifacial"],
    "drones": ["drone", "drones", "uav", "uas", "רחפן", "רחפנים", "כטב", "מטיס"],
    "storage": ["bess", "אגירה", "סוללות", "bess operator", "אנרגיה מתחדשת ואגירה"],
    "grid": ["grid interconnection", "חיבורי רשת", "רשת חשמל", "תחנת השנאה", "הסדרה"],
    "commercial": ["nominations", "renominations", "רנומינציות", "נומינציות", "תפעול מסחרי", "סליקה", "מנייה", "התחשבנות", "settlement", "billing"],
    "dispatch": ["dispatcher", "בקר אנרגיה", "מנהל משמרת", "בקר גז בכיר", "בקר בכיר", "gas dispatcher"]
}


def has_term(text, term):
    return bool(re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", text.lower()))


def is_drone_job(job):
    text = " ".join(str(job.get(k, "")) for k in ("title", "snippet", "query", "sector_key", "sector")).lower()
    return any(has_term(text, k) for k in ("drone", "drones", "uav", "uas", "cuas", "c-uas")) or any(
        k in text for k in ("רחפן", "רחפנים", "כטב", "מטע\"ד", "מטיס"))


def rejection(reason, detail):
    return {"status": "DISQUALIFIED", "match_score": 0, "base_match_score": 0,
            "concrete_matches_count": 0, "reasoning": detail,
            "disqualification_reason": reason, "evaluation_complete": True,
            "evaluation_source": "deterministic", "priority_bonus": 0}


def extract_advertised_monthly_ils_amounts(text, *, exclude_up_to=True):
    """Extract explicit monthly ILS amount bounds from ad text."""
    number = r"(?:\d{1,2}[,.]\d{3}|\d{4,5}|\d{1,2}(?:\.\d+)?[kK])"
    excluded_keywords = ["לשעה", "שעתי", "hour", "annual", "year", "שנתי", "לשנה", "נטו", "net", "$", "usd", "eur", "€"]
    if exclude_up_to:
        excluded_keywords.extend(["עד ", "up to"])

    amounts_list = []
    for line in re.split(r"[\n;|]", text):
        lowtext = line.lower()
        if any(k in lowtext for k in excluded_keywords):
            continue
        if not re.search(r"שכר|משכורת|salary|compensation|comp:", lowtext):
            continue
        if not re.search(r"חודש|month", lowtext):
            continue
        if not re.search(r"₪|ש[״\"]ח|שקלים|\b(?:nis|ils)\b", lowtext):
            continue
        match = re.search(r"(" + number + r")(?:\s*[-–]\s*(" + number + r"))?", line)
        if match:
            def value(s):
                return float(s[:-1]) * 1000 if s.lower().endswith("k") else int(s.replace(",", "").replace(".", ""))
            amounts = [value(s) for s in match.groups() if s]
            if amounts:
                amounts_list.append(amounts)
    return amounts_list


def advertised_high_salary(text, min_lower_bound=18000, max_upper_bound=60000):
    """Conservative: explicit monthly ILS lower bound >= min_lower_bound; never hourly/estimated/max-only."""
    for amounts in extract_advertised_monthly_ils_amounts(text, exclude_up_to=True):
        if min_lower_bound <= min(amounts) <= max(amounts) <= max_upper_bound:
            return True
    return False


def advertised_very_high_salary(text, min_lower_bound=20000, max_upper_bound=80000):
    """Conservative: explicit monthly ILS lower bound >= min_lower_bound."""
    for amounts in extract_advertised_monthly_ils_amounts(text, exclude_up_to=True):
        if min_lower_bound <= min(amounts) <= max(amounts) <= max_upper_bound:
            return True
    return False


def advertised_low_salary(text, max_upper_bound=15000, min_lower_bound=5000):
    """Conservative: explicit monthly ILS upper bound strictly < max_upper_bound."""
    for amounts in extract_advertised_monthly_ils_amounts(text, exclude_up_to=False):
        if max(amounts) < max_upper_bound and min(amounts) >= min_lower_bound:
            return True
    return False


def deterministic_filter(job):
    title, company = job.get("title", ""), job.get("company", "")
    for term in BLACKLIST:
        if has_term(company, term):
            return rejection("blacklist", f"חברה ברשימת החרגה: {company}")
    # Explicit irrelevant occupations; do not reject the bare Hebrew word בקר.
    if re.search(r"קצב(?:/ית|/ה)?(?:\s|$)|מפעל בקר|לבקר תנובה|פקיד/ת קבלה", title):
        return rejection("irrelevant_occupation", "תוצאת חיפוש שאינה תפקיד טכני")

    # Manual workshop / assembly line work with no engineering horizon
    if re.search(r"מכונאי\s+רכב|מוסך|מכונאות\s+רכב|פחח|צמיגאי|מרכיב\s+בפס\s+ייצור|עובד/ת?\s+פס\s+ייצור|מרכיב/ת?\s+לפס|מתקין\s+מערכות\s+שמע|מרכיב\s+מכני\s+בפס", title):
        if not re.search(r"מהנדס|הנדסאי|מנהל|lead|head|scada|plc", title, re.I):
            return rejection("manual_no_engineering_horizon", "עבודה ידנית או מוסכית ללא אופק הנדסי")

    text = f"{title} {job.get('snippet', '')}"

    # Explicit low salary rejection (< 15,000 ILS / month)
    if advertised_low_salary(text):
        return rejection("below_salary_floor", "שכר מפורסם נמוך מ-15,000 ₪ לחודש")

    for term in NON_TECHNICAL_TITLES:
        if not has_term(title, term):
            continue
        if term in AMBIGUOUS and re.search(TECHNICAL, title, re.I):
            continue
        return rejection("non_technical_role", f"תפקיד שנפסל לפי הכותרת: {term}")

    # Control room validation
    if re.search(r"חדר בקרה|מוקד בקרה|בקרת חדר|control room", title, re.I):
        industrial = re.search(r"\b(?:scada|plc|hmi|bms|aveva)\b|סקאדה|טלמטריה|גז טבעי|תחנת כוח|תשתיות חשמל|תשתיות מים|מתקן תעשייתי|bess|אגירה|טורבינ", text, re.I)
        if not industrial and not advertised_high_salary(text):
            return rejection("control_room_lacks_scada_or_high_salary",
                             "אין במודעה עדות לבקרה תעשייתית או לשכר חודשי מובטח של 18,000 ₪ ומעלה")

        # 24/7 shifts check: requires industrial process control AND (advertised salary >= 20k OR known enterprise company)
        is_24_7 = bool(re.search(r"24/7|משמרות\s+לילה|סבב\s+משמרות|משמרות\s+סביב\s+השעון", text, re.I))
        if is_24_7 and not advertised_very_high_salary(text) and not is_known_enterprise(company):
            return rejection("control_room_24_7_unverified_high_salary",
                             "משרת משמרות 24/7 ללא עדות לשכר חודשי מובטח של 20,000 ₪ ומעלה או שיוך למעסיק מוביל")

    return None


def apply_keyword_fallback(job, reason="ai_unavailable"):
    rejected = deterministic_filter(job)
    if rejected:
        return rejected
    text = f"{job.get('title', '')} {job.get('snippet', '')}"
    groups = [name for name, terms in KEYWORD_GROUPS.items() if any(has_term(text, term) for term in terms)]
    return {"status": "RETRY_PENDING", "match_score": 0, "base_match_score": 0,
            "keyword_score": min(100, len(groups) * 15), "matched_keyword_groups": groups,
            "concrete_matches_count": 0, "evaluation_complete": False,
            "evaluation_source": "keyword_fallback", "retry_reason": reason,
            "reasoning": "הערכה חלקית במילות מפתח; ממתינה לבדיקת התאמה מלאה.",
            "priority_bonus": 0}


def extract_curated_tags(job):
    """
    Extracts up to 5 curated operational tags with strict positive triggers
    and negative guards (anti-hallucination / false-positive protection).
    Returns a dict with:
      - is_field_work (bool)
      - provides_company_car (bool)
      - is_shifts_24_7 (bool)
      - is_junior_friendly (bool)
      - stated_ad_salary (str | None)
      - curated_tags (list of dicts with type, icon, label)
    """
    if not isinstance(job, dict):
        return {
            "is_field_work": False,
            "provides_company_car": False,
            "is_shifts_24_7": False,
            "is_junior_friendly": False,
            "stated_ad_salary": None,
            "curated_tags": [],
        }

    tags = []

    # 1. Stated Salary: strictly from original job ad (never model predicted)
    salary_source = (job.get("salary_source_type") or "").strip().lower()
    salary_val = (job.get("salary_range") or "").strip()
    is_stated_salary = (
        salary_source in ("job_ad", "ad", "employer")
        and bool(salary_val)
        and salary_val not in ("לא צוין במודעה", "לא צוין")
    )
    stated_ad_salary = salary_val if is_stated_salary else None
    if is_stated_salary:
        tags.append({
            "type": "tag-salary",
            "icon": "ph-bold ph-currency-circle-dollar",
            "label": salary_val
        })

    # Aggregate text corpus
    text_corpus = " ".join(str(job.get(k) or "") for k in (
        "title", "snippet", "company_requirements", "job_summary",
        "experience_strengths", "reasoning", "key_highlights"
    )).lower()

    # 2. Field Work
    field_pos_regex = re.compile(
        r"(?:עבודת שטח|טכנאי שטח|מהנדס שטח|הנדסאי שטח|אנשי שטח|שירות שטח|התקנות שטח|פעילות שטח|אתרי לקוח|שירות באתרי לקוח|אתרי לקוחות|שירות באתרים|field technician|field engineer|field service|field operations)",
        re.I
    )
    field_neg_regex = re.compile(
        r"(?:ללא עבודת שטח|ללא שטח|אינו כולל שטח|אינה כוללת שטח|לא עבודת שטח)",
        re.I
    )
    is_field_work = bool(field_pos_regex.search(text_corpus)) and not bool(field_neg_regex.search(text_corpus))
    if is_field_work:
        tags.append({
            "type": "tag-field",
            "icon": "ph-bold ph-wrench",
            "label": "עבודת שטח"
        })

    # 3. Company Car
    car_pos_regex = re.compile(
        r"(?:רכב חברה|רכב צמוד|רכב שירות|כולל רכב|רכב לצרכי עבודה|company car)",
        re.I
    )
    car_neg_regex = re.compile(
        r"(?:ללא רכב|אינו כולל רכב|אינה כוללת רכב|לא כולל רכב|לא רכב חברה|אין רכב חברה|אין רכב)",
        re.I
    )
    provides_company_car = bool(car_pos_regex.search(text_corpus)) and not bool(car_neg_regex.search(text_corpus))
    if provides_company_car:
        tags.append({
            "type": "tag-car",
            "icon": "ph-bold ph-car",
            "label": "רכב חברה"
        })

    # 4. 24/7 Shifts / NOC
    shifts_pos_regex = re.compile(
        r"(?:24[/]7|משמרות 24[/]7|סבב 24[/]7|משמרות לילה|לילות וסופ[\"״]?ש|לילות וסופי שבוע|noc 24[/]7|חדר בקרה 24[/]7|24[/]7 shifts|משמרות כולל לילות|סבב משמרות מלא)",
        re.I
    )
    shifts_neg_regex = re.compile(
        r"(?:ללא משמרות|ללא 24[/]7|ללא לילות|ללא סופ[\"״]?ש|ללא סופי שבוע)",
        re.I
    )
    is_shifts_24_7 = bool(shifts_pos_regex.search(text_corpus)) and not bool(shifts_neg_regex.search(text_corpus))
    if is_shifts_24_7:
        tags.append({
            "type": "tag-shifts",
            "icon": "ph-bold ph-clock-countdown",
            "label": "משמרות 24/7"
        })

    # 5. Junior / Beginners
    junior_pos_regex = re.compile(
        r"(?:junior|ג['\"״]?וניור|entry[ -]?level|ללא ניסיון|ללא נסיון|0-2 שנות ניסיון|0-1 שנות ניסיון|עד שנתיים ניסיון|מתאים למתחילים|פתיחות לבוגרים ללא ניסיון|פתיחות לבוגרים|בוגרים טריים|הכשרה מלאה על חשבון החברה|דריסת רגל|תפקיד כניסה)",
        re.I
    )
    junior_neg_regex = re.compile(
        r"(?:לא מתאים לג['\"״]?וניור|לא מתאים למתחילים|דורש ניסיון משמעותי|לא ללא ניסיון)",
        re.I
    )
    junior_openness_flag = str(job.get("junior_openness") or "").strip().lower() in ("כן", "true", "yes")

    has_junior_positive = bool(junior_pos_regex.search(text_corpus)) or junior_openness_flag
    has_junior_negative = bool(junior_neg_regex.search(text_corpus))
    title_text = str(job.get("title") or "").lower()
    has_senior_title = bool(re.search(r"\b(?:senior|lead)\b|ראש צוות|מנהל צוות", title_text))

    is_junior_friendly = has_junior_positive and not has_junior_negative and not has_senior_title
    if is_junior_friendly:
        tags.append({
            "type": "tag-junior",
            "icon": "ph-bold ph-graduation-cap",
            "label": "Junior"
        })

    return {
        "is_field_work": is_field_work,
        "provides_company_car": provides_company_car,
        "is_shifts_24_7": is_shifts_24_7,
        "is_junior_friendly": is_junior_friendly,
        "stated_ad_salary": stated_ad_salary,
        "curated_tags": tags[:5],
    }
