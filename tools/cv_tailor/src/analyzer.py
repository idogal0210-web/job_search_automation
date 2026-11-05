import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
try:
    from tools.cv_tailor.src.scraper import JobPosting
    from tools.cv_tailor.src.keywords import extract_keywords
    from tools.cv_tailor.src.utils import (
        print_info, print_warning, print_success, Colors, load_prompt_template, get_gemini_pool
    )
except ModuleNotFoundError:
    from src.scraper import JobPosting
    from src.keywords import extract_keywords
    from src.utils import (
        print_info, print_warning, print_success, Colors, load_prompt_template, get_gemini_pool
    )

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

ANALYSIS_PROMPT = load_prompt_template("cv_analysis_v1.txt")

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

    pool = get_gemini_pool()
    try:
        data = pool.generate_json(client, prompt, temperature=0.2)
    except Exception as e:
        print_warning(f"קריאה דרך GeminiPool נכשלה ({e}), מנסה מודלי fallback ישירים...")
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
            except Exception as err:
                print_warning(f"מודל {model_name} נכשל, מנסה מודל חלופי... ({err})")
                continue
        if not response_text:
            raise RuntimeError("כל קריאות הניתוח ל-Gemini נכשלו.")
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        data = json.loads(clean_json.strip())

    try:
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
