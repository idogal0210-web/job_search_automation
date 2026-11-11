import json
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
try:
    from tools.cv_tailor.src.scraper import JobPosting
    from tools.cv_tailor.src.keywords import extract_keywords
    from tools.cv_tailor.src.utils import (
        print_info, print_warning, print_success, Colors, load_prompt_template,
        get_gemini_pool, get_gemini_runtime_module
    )
except ModuleNotFoundError:
    from src.scraper import JobPosting
    from src.keywords import extract_keywords
    from src.utils import (
        print_info, print_warning, print_success, Colors, load_prompt_template,
        get_gemini_pool, get_gemini_runtime_module
    )

@dataclass
class ATSAnalysis:
    overall_score: Optional[int]
    match_summary: str
    scorecard: Dict[str, int]
    matched_keywords: List[str]
    missing_keywords: List[str]
    key_strengths: List[str]
    clarification_questions: List[str]
    recommended_changes: List[str]
    unmatched_requirements: List[str] = field(default_factory=list)
    evaluation_model: str = ""
    degraded: bool = False

ANALYSIS_PROMPT = load_prompt_template("cv_analysis_v1.txt")

def _normalize_scorecard(raw_scorecard: Any) -> Dict[str, int]:
    """Convert structured list or dict scorecard into uniform dict[category -> int]."""
    if isinstance(raw_scorecard, dict):
        return {str(k): int(v) for k, v in raw_scorecard.items() if isinstance(v, (int, float))}
    if isinstance(raw_scorecard, list):
        out: Dict[str, int] = {}
        for item in raw_scorecard:
            if isinstance(item, dict) and item.get("category") is not None:
                out[str(item["category"])] = int(item.get("score", 0))
        return out
    return {}

def analyze_job_match(job: JobPosting, base_profile: str, gemini_key: str) -> ATSAnalysis:
    """Analyze job posting against candidate base profile using local keywords + schema-validated GeminiPool."""
    print_info("מבצע חילוץ מילות מפתח ראשוני ומנתח דרישות ATS...")

    raw_kws = extract_keywords(job.description, top_n=12)
    pre_keywords_str = ", ".join([f"{kw} (ציון: {sc})" for kw, sc in raw_kws]) if raw_kws else "לא אותרו מילות מפתח ייחודיות"

    client = genai.Client(api_key=gemini_key)
    runtime = get_gemini_runtime_module()
    pool = get_gemini_pool()

    prompt = ANALYSIS_PROMPT.format(
        base_profile=base_profile,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        pre_extracted_keywords=pre_keywords_str
    )

    try:
        data = pool.generate_json(
            client,
            prompt,
            schema=runtime.AtsStudioAnalysisSchema,
            temperature=0.2,
        )
    except Exception as err:
        print_warning(f"ניתוח Gemini לא הושלם ({err}); מחזיר דוח חילוץ מילולי חלקי ללא ציון AI.")
        fallback_kws = [kw for kw, _ in raw_kws[:8]]
        return ATSAnalysis(
            overall_score=None,
            match_summary="שירות Gemini לא היה זמין; מוצגות מילות מפתח שחולצו מקומית בלבד ללא ציון התאמה של AI.",
            scorecard={},
            matched_keywords=fallback_kws,
            missing_keywords=[],
            key_strengths=[],
            clarification_questions=[],
            recommended_changes=[],
            unmatched_requirements=[],
            evaluation_model="local_keyword_fallback",
            degraded=True,
        )

    overall_score = int(data["overall_score"])
    scorecard = _normalize_scorecard(data.get("scorecard"))
    print_success(f"ניתוח ה-ATS הושלם. ציון התאמה כולל: {overall_score}%")

    return ATSAnalysis(
        overall_score=overall_score,
        match_summary=data.get("match_summary", ""),
        scorecard=scorecard,
        matched_keywords=list(data.get("matched_keywords", [])),
        missing_keywords=list(data.get("missing_keywords", [])),
        key_strengths=list(data.get("key_strengths", [])),
        clarification_questions=list(data.get("clarification_questions", [])),
        recommended_changes=list(data.get("recommended_changes", [])),
        unmatched_requirements=list(data.get("unmatched_requirements", [])),
        evaluation_model=str(data.get("evaluation_model", "")),
        degraded=False,
    )

def print_ats_scorecard(analysis: ATSAnalysis):
    """Print a visually formatted Scorecard in terminal."""
    score = analysis.overall_score
    score_display = f"{score}%" if score is not None else "לא זמין (מצב חלקי)"
    score_color = Colors.YELLOW if score is None else (Colors.GREEN if score >= 80 else (Colors.YELLOW if score >= 65 else Colors.RED))
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}                 דשבורד התאמת ATS                     {Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================{Colors.END}")
    print(f"\n[SCORE] {Colors.BOLD}ציון התאמה כולל:{Colors.END} {score_color}{Colors.BOLD}{score_display}{Colors.END}")
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
