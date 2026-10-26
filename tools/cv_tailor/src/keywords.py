"""
CV and Job Keywords Extractor for Israeli Engineering, Energy & Tech Postings.
Pure Python implementation with custom tokenization, stopword filtering, and domain-boosted terms.
"""

from __future__ import annotations
import re
from collections import Counter
from typing import List, Tuple

EN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "will",
    "with", "you", "your", "our", "we", "they", "this", "these", "their", "i",
    "am", "us", "if", "so", "but", "not", "no", "can", "do", "does", "did", "would",
    "should", "could", "may", "might", "must", "shall", "about", "into", "than",
    "then", "also", "what", "which", "who", "whom", "whose", "when", "where", "why",
    "how", "all", "any", "each", "every", "some", "such", "more", "most", "other",
    "new", "one", "two", "three", "first", "last", "next", "good", "great", "best",
    "job", "jobs", "role", "roles", "position", "positions", "candidate", "team",
    "company", "work", "working", "looking", "seeking", "join", "hiring", "apply",
    "opportunity", "opportunities", "based", "like", "well", "make", "making",
    "get", "use", "using", "build", "building", "develop", "developing", "create",
    "creating", "help", "helping", "ensure", "ensuring", "deliver", "delivering",
    "years", "year", "experience", "knowledge", "understanding", "strong", "solid",
    "proven", "excellent", "deep", "advanced", "senior", "junior", "mid", "level",
    "office", "remote", "hybrid", "full", "time", "part", "israel", "israeli",
    "tel", "aviv", "herzliya", "haifa", "beer", "sheva"
}

HE_STOPWORDS = {
    "של", "את", "על", "עם", "זה", "זו", "אלה", "אלו", "היא", "הוא", "הם", "הן",
    "אני", "אתה", "את", "אנחנו", "אתם", "אתן", "לא", "כן", "אם", "אז", "גם",
    "רק", "כמו", "יש", "אין", "היה", "היו", "להיות", "לעבוד", "עובד", "עובדים",
    "חברה", "צוות", "תפקיד", "משרה", "ניסיון", "שנים", "שנה", "אנשים", "אדם",
    "כל", "כלל", "בכל", "בתוך", "בין", "לפי", "אחרי", "לפני", "מתוך", "בעיקר",
    "מאוד", "יותר", "פחות", "הכי", "חייב", "צריך", "רצוי", "נדרש", "יכולת",
    "יכולות", "הבנה", "ידע", "כישורים", "תל", "אביב", "הרצליה", "ישראל", "חיפה",
    "אנו", "הכרת", "התפקיד", "ממך", "שלך", "שלנו", "חזק", "רב", "מתאים", "מתאימה"
}

# Domain-specific keyword boost: Energy, Gas, Mechanical, Electrical & Tech/AI
DOMAIN_TECH_BOOST = {
    # Energy & Gas
    "gas", "natural gas", "גז", "גז טבעי", "energean", "אנרג׳יאן", "ingl", "נתג״ז", "נתגז",
    "nomination", "nominations", "re-nomination", "נומינציה", "scada", "plc", "hmi",
    "control room", "בקרת גז", "לחצים", "ספיקות", "fpso", "אסדת הפקה", "הפקה ימית",
    "תחנות כוח", "power plant", "רציפות אספקה", "gas supply", "pressure", "flow rate",

    # Mechanical & Solar Energy
    "mechanical", "הנדסת מכונות", "מכונות", "הנדסאי מכונות", "solar", "pv", "סולארי",
    "סולארית", "bifacial", "monofacial", "דו-צדדי", "פוטו-וולטאי", "turbines", "טורבינות",
    "compressors", "מדחסים", "משאבות", "pumps", "valves", "מגופים", "צנרת", "piping",
    "hvac", "thermodynamics", "תרמודינמיקה",

    # Electrical & High/Low Voltage
    "electrician", "חשמלאי", "חשמלאי מוסמך", "חוק החשמל", "low voltage", "מתח נמוך",
    "מתח גבוה", "high voltage", "לוחות חשמל", "שרטוט חשמלי", "electrical diagrams",

    # Data, ERP & AI Automation
    "excel", "אקסל", "sap", "copilot", "gemini", "ai", "בינה מלאכותית", "automation",
    "אוטומציה", "ניתוח נתונים", "data analysis", "reporting", "דוחות תפעוליים",
    "python", "sql", "powerbi", "bi", "monday.com", "priority",

    # Operations & Shift Leadership
    "24/7", "משמרות", "shift", "shift leader", "בקר תפעול", "operations controller",
    "safety", "בטיחות", "emergency response", "מענה לחירום", "קבלת החלטות",
    "focal point", "ניהול עובדים", "הדרכה", "חניכה"
}

def tokenize(text: str) -> List[str]:
    """Split text into tokens while preserving domain & technical names."""
    text_lower = text.lower()
    # Match English alphanumeric/symbols and Hebrew words
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+#.\-/]*|[\u0590-\u05FF]+", text_lower)
    return [t.strip(".-/") for t in tokens if len(t.strip(".-/")) > 1]

def score_tokens(tokens: List[str]) -> Counter:
    """Score tokens by frequency, boosting matched energy/tech/operations terms."""
    filtered = [
        t for t in tokens
        if t not in EN_STOPWORDS and t not in HE_STOPWORDS and len(t) > 2
    ]
    counts = Counter(filtered)
    scored = Counter()
    for token, freq in counts.items():
        boost = 3 if token in DOMAIN_TECH_BOOST else 1
        scored[token] = freq * boost
    return scored

def extract_keywords(text: str, top_n: int = 15) -> List[Tuple[str, int]]:
    """Extract top N ATS keywords with domain boosting."""
    tokens = tokenize(text)
    scored = score_tokens(tokens)
    return scored.most_common(top_n)
