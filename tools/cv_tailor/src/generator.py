import os
import json
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
try:
    from tools.cv_tailor.src.scraper import JobPosting
    from tools.cv_tailor.src.researcher import CompanyResearch
    from tools.cv_tailor.src.analyzer import ATSAnalysis
    from tools.cv_tailor.src.utils import (
        print_info, print_warning, print_success, save_file, create_html_wrapper,
        load_prompt_template, get_gemini_pool, get_gemini_runtime_module
    )
except ModuleNotFoundError:
    from src.scraper import JobPosting
    from src.researcher import CompanyResearch
    from src.analyzer import ATSAnalysis
    from src.utils import (
        print_info, print_warning, print_success, save_file, create_html_wrapper,
        load_prompt_template, get_gemini_pool, get_gemini_runtime_module
    )

@dataclass
class TailoredPackage:
    cv_markdown: str
    cv_html: str
    cover_letter_markdown: str
    cover_letter_html: str
    interview_talking_points: List[str]
    saved_files: List[str]
    unmatched_requirements: List[str] = field(default_factory=list)
    evaluation_model: str = ""

GENERATION_PROMPT = load_prompt_template("cv_generation_v1.txt")

TONE_INSTRUCTIONS = {
    "technical": "דגש הנדסי-תפעולי: בקרת SCADA, אבחון תקלות, מערכות לחץ/ספיקה, חוק החשמל ונהלי בטיחות.",
    "operational": "דגש תפעולי וסמכות שטח (ATS Keyword Optimized): ניטור 24/7, תיאום משמרות, PRMS, HSE ואמינות אספקה.",
    "strategic": "דגש ממוקד תוצאות וניהול ממשקים (Executive / Impact Focused): תיאום רב-גורמי, שיפור תהליכים וכלי AI.",
}

def generate_tailored_package(
    job: JobPosting,
    base_profile: str,
    analysis: ATSAnalysis,
    research: CompanyResearch,
    lang: str = "he",
    clarifications: Optional[List[str]] = None,
    output_dir: str = None,
    gemini_key: str = "",
    tone_mode: str = "technical",
    save_outputs: bool = True,
) -> TailoredPackage:
    """Generate tailored CV, Cover Letter, and interview talking points adhering to Realism and Israeli standards."""
    print_info(f"מייצר קו״ח מותאמים ומכתב מקדים לפי חוקי הריאליזם (שפה: {'עברית' if lang == 'he' else 'אנגלית'})...")
    client = genai.Client(api_key=gemini_key)
    runtime = get_gemini_runtime_module()
    pool = get_gemini_pool()

    base_lang_rule = "עברית בלבד (RTL). שפה דוגרי, שמות תפקידים מקוריים בלבד, ללא ניפוח." if lang == "he" else "Professional, grounded English (LTR). Original job titles only, zero inflation."
    tone_note = TONE_INSTRUCTIONS.get((tone_mode or "technical").lower(), TONE_INSTRUCTIONS["technical"])
    lang_instruction = f"{base_lang_rule}\nהדגשת סגנון: {tone_note}"

    clarifications_text = "\n".join([f"- {c}" for c in clarifications]) if clarifications else "לא נמסרו הבהרות נוספות."

    prompt = GENERATION_PROMPT.format(
        lang_instruction=lang_instruction,
        base_profile=base_profile,
        job_title=job.title,
        company=job.company,
        job_description=job.description,
        company_research=f"{research.summary}\nפרויקטים: {', '.join(research.recent_projects)}",
        matched_keywords=", ".join(analysis.matched_keywords),
        recommended_changes="\n- ".join(analysis.recommended_changes),
        user_clarifications=clarifications_text
    )

    try:
        data = pool.generate_json(
            client,
            prompt,
            schema=runtime.TailoredCvPackageSchema,
            temperature=0.2,
        )
    except Exception as e:
        print_warning(f"שגיאה בקריאת ייצור התוצרים מ-GeminiPool: {e}")
        raise RuntimeError(f"כל קריאות הייצור ל-Gemini נכשלו: {e}") from e

    cv_md = data.get("cv_markdown", "")
    cover_letter_md = data.get("cover_letter_markdown", "")
    talking_points = list(data.get("interview_talking_points", []))
    unmatched_reqs = list(dict.fromkeys([
        *(analysis.unmatched_requirements or []),
        *(data.get("unmatched_requirements") or []),
    ]))

    # Generate clean A4 HTML representations
    cv_html = create_html_wrapper(f"קורות חיים - עידו גל - {job.company}", cv_md, lang=lang)
    cover_letter_html = create_html_wrapper(f"מכתב מקדים - עידו גל - {job.company}", cover_letter_md, lang=lang)

    saved_files: List[str] = []
    if save_outputs:
        safe_company = re.sub(r'[^\w\s\-_]', '', job.company.strip()).replace(" ", "_") or "Company"
        lang_suffix = "EN" if (lang or "he").lower() == "en" else "HE"
        prefix = f"{safe_company}_{lang_suffix}"

        cv_md_path = save_file(cv_md, f"CV_{prefix}.md", output_dir)
        cv_html_path = save_file(cv_html, f"CV_{prefix}.html", output_dir)
        cl_md_path = save_file(cover_letter_md, f"CoverLetter_{prefix}.md", output_dir)
        cl_html_path = save_file(cover_letter_html, f"CoverLetter_{prefix}.html", output_dir)

        score_label = f"{analysis.overall_score}%" if analysis.overall_score is not None else "לא חושב (מצב חלקי)"
        summary_md = f"""# סיכום התאמה ריאלי למשרה: {job.title} │ {job.company}

**תאריך יצירה:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**ציון התאמת ATS:** {score_label}

---

## מדדי התאמה לפי קטגוריות
"""
        for cat, sc in analysis.scorecard.items():
            summary_md += f"* **{cat}:** {sc}%\n"

        summary_md += f"""
---

## מילות מפתח ATS שהוטמעו
{', '.join(analysis.matched_keywords)}
"""
        if unmatched_reqs:
            summary_md += "\n---\n\n## דרישות מהותיות שנותרו בפער\n"
            for ur in unmatched_reqs:
                summary_md += f"* {ur}\n"

        summary_md += "\n---\n\n## דגשים ונקודות מפתח לראיון סינון ראשוני\n"
        for tp in talking_points:
            summary_md += f"* {tp}\n"

        summary_path = save_file(summary_md, f"Summary_{prefix}.md", output_dir)
        saved_files = [cv_md_path, cv_html_path, cl_md_path, cl_html_path, summary_path]
        print_success(f"כל הקבצים נשמרו בהצלחה בתיקיית: {output_dir or 'output/'}")

    return TailoredPackage(
        cv_markdown=cv_md,
        cv_html=cv_html,
        cover_letter_markdown=cover_letter_md,
        cover_letter_html=cover_letter_html,
        interview_talking_points=talking_points,
        saved_files=saved_files,
        unmatched_requirements=unmatched_reqs,
        evaluation_model=str(data.get("evaluation_model", "")),
    )
