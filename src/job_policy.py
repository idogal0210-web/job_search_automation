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
AMBIGUOUS = {"sales", "customer support", "service desk", "מוקד", "רכש", "קניין", "קניינית"}
TECHNICAL = r"\b(?:technical|engineer|technician|scada|plc|hmi|bms)\b|הנדסאי|מהנדס|טכנאי|טכני|בקרה"
BLACKLIST = ["energean", "אנרג'יאן", "אנרג'ין", "ingl", "נתג", "chevron", "שברון"]
KEYWORD_GROUPS = {
    "gas": ["natural gas", "גז טבעי"],
    "energy": ["energy", "אנרגיה", "תחנת כוח", "power plant"],
    "mechanical": ["mechanical", "מכונות", "מכונאי"],
    "control": ["scada", "plc", "hmi", "bms", "בקרה"],
    "solar": ["solar", "pv", "סולארי", "פוטו"],
    "drones": ["drone", "drones", "uav", "uas", "רחפן", "רחפנים", "כטב"],
    "storage": ["bess", "אגירה", "סוללות"],
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


def advertised_high_salary(text):
    """Conservative: explicit monthly ILS lower bound >= 18,000; never hourly/estimated/max-only."""
    number = r"(?:\d{1,2}[,.]\d{3}|\d{4,5}|\d{1,2}(?:\.\d+)?[kK])"
    for line in re.split(r"[\n;|]", text):
        lowtext = line.lower()
        if any(k in lowtext for k in ("לשעה", "שעתי", "hour", "annual", "year", "שנתי", "לשנה", "נטו", "net", "עד ", "up to", "$", "usd", "eur", "€")):
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
            if amounts and 18000 <= min(amounts) <= max(amounts) <= 60000:
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
    for term in NON_TECHNICAL_TITLES:
        if not has_term(title, term):
            continue
        if term in AMBIGUOUS and re.search(TECHNICAL, title, re.I):
            continue
        return rejection("non_technical_role", f"תפקיד שנפסל לפי הכותרת: {term}")
    if re.search(r"חדר בקרה|מוקד בקרה|בקרת חדר|control room", title, re.I):
        text = f"{title} {job.get('snippet', '')}"
        industrial = re.search(r"\b(?:scada|plc|hmi|bms)\b|סקאדה|טלמטריה|גז טבעי|תחנת כוח|תשתיות חשמל|תשתיות מים|מתקן תעשייתי", text, re.I)
        if not industrial and not advertised_high_salary(text):
            return rejection("control_room_lacks_scada_or_high_salary",
                             "אין במודעה עדות לבקרה תעשייתית או לשכר חודשי מובטח של 18,000 ₪ ומעלה")
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
