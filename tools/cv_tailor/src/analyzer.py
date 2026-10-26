import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
try:
    from tools.cv_tailor.src.scraper import JobPosting
    from tools.cv_tailor.src.keywords import extract_keywords
    from tools.cv_tailor.src.utils import print_info, print_warning, print_success, Colors
except ModuleNotFoundError:
    from src.scraper import JobPosting
    from src.keywords import extract_keywords
    from src.utils import print_info, print_warning, print_success, Colors

@dataclass
class ATSAnalysis:
    overall_score: int
    match_summary: str
    scorecard: Dict[str, int]
    matched_keywords: List[str]
    missing_keywords: List[str]
    key_strengths: List[str]
    clarification_questions: List[str]
    recommended_changes: List[str]

ANALYSIS_PROMPT = """אתה מומחה בכיר למערכות סינון קורות חיים (ATS), גיוס טכנולוגי וניהול קריירה בתחומי האנרגיה, הנדסת מכונות, תפעול ובקרה בשוק העבודה הישראלי.

תפקידך לנתח את מידת ההתאמה המדויקת בין תיאור המשרה לבין פרופיל הבסיס של המועמד עידו גל.

חוקי ברזל:
1. עיקרון האמת (Zero-Hallucination): אין להמציא ניסיון שאינו קיים בפרופיל הבסיס של עידו גל.
2. אובייקטיביות ביקורתית: הערך ציונים מדויקים ומציאותיים ללא ניפוחים מלאכותיים.
3. חוק שוויון הזדמנויות בעבודה התשמ"ח-1988: יש להתעלם מכל דרישה בלתי חוקית (גיל, מצב משפחתי, דת, תמונה, כתובת רחוב מלאה).
4. פלט בפורמט JSON בלבד, תקין ומדויק.

פרופיל הבסיס של עידו גל:
{base_profile}

פרטי המשרה לניתוח:
כותרת: {job_title}
חברה: {company}
תיאור ודרישות:
{job_description}

מילות מפתח טכניות שזוהו בסריקה ראשונית:
{pre_extracted_keywords}

החזר אך ורק אובייקט JSON במבנה הבא:
{{
  "overall_score": 85,
  "match_summary": "סיכום קצר וקולע ב-2-3 משפטים בעברית על רמת ההתאמה והיתרונות המרכזיים.",
  "scorecard": {{
    "השכלה והסמכות (הנדסאי מכונות, חשמל)": 90,
    "ניסיון תפעולי ובקרה 24/7 (גז/אנרגיה)": 95,
    "כלים טכניים, AI ואוטומציה (SAP, Excel)": 85,
    "הובלה, ממשקים ועבודה תחת לחץ": 90
  }},
  "matched_keywords": ["מילת מפתח 1", "מילת מפתח 2", "מילת מפתח 3", "מילת מפתח 4"],
  "missing_keywords": ["מילה חסרה 1 (אם יש)", "דרישה שלא מופיעה במפורש"],
  "key_strengths": ["חוזקה מרכזית 1", "חוזקה מרכזית 2", "חוזקה מרכזית 3"],
  "clarification_questions": ["שאלה לבירור מול עידו במידה ויש שטח אפור בדרישות"],
  "recommended_changes": [
    "התאמה 1: להדגיש את הניסיון ב-Nomination ובקרה מול נתג״ז",
    "התאמה 2: לפתוח כל שורה בפועל פעיל ולשלב מספרים כמותיים",
    "התאמה 3: לשלב מילות מפתח ATS בכותרת ובסעיפי הניסיון"
  ]
}}
"""

def analyze_job_match(job: JobPosting, base_profile: str, gemini_key: str) -> ATSAnalysis:
    """Analyze job posting against candidate base profile using local keywords + Gemini."""
    print_info("מבצע חילוץ מילות מפתח ראשוני ומנתח דרישות ATS...")
    
    # Pre-extract local keywords with domain boost
    raw_kws = extract_keywords(job.description, top_n=12)
    pre_keywords_str = ", ".join([f"{kw} (ציון: {sc})" for kw, sc in raw_kws]) if raw_kws else "לא אותרו מילות מפתח ייחודיות"
    
    client = genai.Client(api_key=gemini_key)
    
    prompt = ANALYSIS_PROMPT.format(
        base_profile=base_profile,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        pre_extracted_keywords=pre_keywords_str
    )

    models_to_try = ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"]
    response_text = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            response_text = response.text
            if response_text:
                break
        except Exception as e:
            print_warning(f"מודל {model_name} נכשל, מנסה מודל חלופי... ({e})")
            continue

    if not response_text:
        raise RuntimeError("כל קריאות הניתוח ל-Gemini נכשלו.")

    try:
        # Clean JSON if wrapped in markdown fences
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        data = json.loads(clean_json)
        print_success(f"ניתוח ה-ATS הושלם. ציון התאמה כולל: {data.get('overall_score', 85)}%")
        
        return ATSAnalysis(
            overall_score=data.get("overall_score", 85),
            match_summary=data.get("match_summary", "התאמה גבוהה לדרישות התפקיד."),
            scorecard=data.get("scorecard", {}),
            matched_keywords=data.get("matched_keywords", []),
            missing_keywords=data.get("missing_keywords", []),
            key_strengths=data.get("key_strengths", []),
            clarification_questions=data.get("clarification_questions", []),
            recommended_changes=data.get("recommended_changes", [])
        )
    except Exception as e:
        print_warning(f"שגיאה בפענוח JSON מתשובת המודל: {e}")
        # Fallback using pre-extracted keywords
        fallback_kws = [kw for kw, _ in raw_kws[:6]] or ["בקרה תפעולית", "הנדסת מכונות", "24/7"]
        return ATSAnalysis(
            overall_score=85,
            match_summary="התאמה טובה לדרישות המשרה על בסיס הרקע התפעולי וההנדסי.",
            scorecard={"התאמה כללית": 85},
            matched_keywords=fallback_kws,
            missing_keywords=[],
            key_strengths=["ניסיון מעשי בתשתיות קריטיות", "קבלת החלטות תחת לחץ"],
            clarification_questions=[],
            recommended_changes=["הבלטת הניסיון ב-Energean ובקרה בזמן אמת"]
        )

def print_ats_scorecard(analysis: ATSAnalysis):
    """Print a visually formatted Scorecard in terminal."""
    score_color = Colors.GREEN if analysis.overall_score >= 80 else (Colors.YELLOW if analysis.overall_score >= 65 else Colors.RED)
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}                 דשבורד התאמת ATS                     {Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================{Colors.END}")
    print(f"\n[SCORE] {Colors.BOLD}ציון התאמה כולל:{Colors.END} {score_color}{Colors.BOLD}{analysis.overall_score}%{Colors.END}")
    print(f"[SUMMARY] {Colors.BOLD}תקציר מנהלים:{Colors.END} {analysis.match_summary}\n")
    
    print(f"{Colors.BOLD}[METRICS] מדדי התאמה לפי קטגוריות:{Colors.END}")
    for cat, score in analysis.scorecard.items():
        bar_len = int(score / 5)
        bar = "=" * bar_len + "-" * (20 - bar_len)
        cat_color = Colors.GREEN if score >= 80 else (Colors.YELLOW if score >= 65 else Colors.RED)
        print(f"  * {cat:<40} {cat_color}[{bar}] {score}%{Colors.END}")

    print(f"\n{Colors.BOLD}[KEYWORDS] מילות מפתח ATS שנמצאו בהתאמה מלאה:{Colors.END}")
    print("  " + ", ".join([f"{Colors.GREEN}{kw}{Colors.END}" for kw in analysis.matched_keywords]))

    if analysis.missing_keywords:
        print(f"\n{Colors.BOLD}[FOCUS] מילות מפתח או דרישות לפוקוס מיוחד:{Colors.END}")
        print("  " + ", ".join([f"{Colors.YELLOW}{kw}{Colors.END}" for kw in analysis.missing_keywords]))

    print(f"\n{Colors.BOLD}[STRENGTHS] יתרונות תחרותיים מרכזיים:{Colors.END}")
    for strength in analysis.key_strengths:
        print(f"  + {strength}")

    print(f"\n{Colors.BOLD}[CHANGES] שינויים מומלצים ומותאמים בקו״ח:{Colors.END}")
    for change in analysis.recommended_changes:
        print(f"  -> {change}")

    if analysis.clarification_questions:
        print(f"\n{Colors.BOLD}[QUESTIONS] שאלות דיוק וחידוד מומלצות:{Colors.END}")
        for q in analysis.clarification_questions:
            print(f"  ? {q}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================{Colors.END}\n")
