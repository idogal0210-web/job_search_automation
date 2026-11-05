import os
import json
import re
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
try:
    from tools.cv_tailor.src.scraper import JobPosting
    from tools.cv_tailor.src.researcher import CompanyResearch
    from tools.cv_tailor.src.analyzer import ATSAnalysis
    from tools.cv_tailor.src.utils import (
        print_info, print_warning, print_success, save_file, create_html_wrapper,
        load_prompt_template, get_gemini_pool
    )
except ModuleNotFoundError:
    from src.scraper import JobPosting
    from src.researcher import CompanyResearch
    from src.analyzer import ATSAnalysis
    from src.utils import (
        print_info, print_warning, print_success, save_file, create_html_wrapper,
        load_prompt_template, get_gemini_pool
    )

@dataclass
class TailoredPackage:
    cv_markdown: str
    cv_html: str
    cover_letter_markdown: str
    cover_letter_html: str
    interview_talking_points: List[str]
    saved_files: List[str]

GENERATION_PROMPT = load_prompt_template("cv_generation_v1.txt")

def generate_tailored_package(
    job: JobPosting,
    base_profile: str,
    analysis: ATSAnalysis,
    research: CompanyResearch,
    lang: str = "he",
    clarifications: Optional[List[str]] = None,
    output_dir: str = None,
    gemini_key: str = ""
) -> TailoredPackage:
    """Generate tailored CV, Cover Letter, and interview talking points adhering to Realism and Israeli standards."""
    print_info(f"מייצר קו״ח מותאמים ומכתב מקדים לפי חוקי הריאליזם (שפה: {'עברית' if lang == 'he' else 'אנגלית'})...")
    client = genai.Client(api_key=gemini_key)
    
    lang_instruction = "עברית בלבד (RTL). שפה דוגרי, שמות תפקידים מקוריים בלבד, ללא ניפוח." if lang == "he" else "Professional, grounded English (LTR). Original job titles only, zero inflation."
    
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
                print_warning(f"מודל {model_name} נכשל בייצור, מנסה מודל חלופי... ({err})")
                continue
        if not response_text:
            raise RuntimeError("כל קריאות הייצור ל-Gemini נכשלו.")
        clean_json = response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        data = json.loads(clean_json.strip())

    try:

        data = json.loads(clean_json)
        cv_md = data.get("cv_markdown", "")
        cover_letter_md = data.get("cover_letter_markdown", "")
        talking_points = data.get("interview_talking_points", [])

        # Generate HTML representations
        cv_html = create_html_wrapper(f"קורות חיים - עידו גל - {job.company}", cv_md, lang=lang)
        cover_letter_html = create_html_wrapper(f"מכתב מקדים - עידו גל - {job.company}", cover_letter_md, lang=lang)

        safe_company = re.sub(r'[^\w\s\-_]', '', job.company.strip()).replace(" ", "_") or "Company"
        prefix = safe_company

        # Save files
        cv_md_path = save_file(cv_md, f"CV_{prefix}.md", output_dir)
        cv_html_path = save_file(cv_html, f"CV_{prefix}.html", output_dir)
        cl_md_path = save_file(cover_letter_md, f"CoverLetter_{prefix}.md", output_dir)
        cl_html_path = save_file(cover_letter_html, f"CoverLetter_{prefix}.html", output_dir)

        # Save summary
        summary_md = f"""# סיכום התאמה ריאלי למשרה: {job.title} │ {job.company}

**תאריך יצירה:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
**ציון התאמת ATS:** {analysis.overall_score}%

---

## מדדי התאמה לפי קטגוריות
"""
        for cat, sc in analysis.scorecard.items():
            summary_md += f"* **{cat}:** {sc}%\n"

        summary_md += f"""
---

## מילות מפתח ATS שהוטמעו
{', '.join(analysis.matched_keywords)}

---

## דגשים ונקודות מפתח לראיון סינון ראשוני
"""
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
            saved_files=saved_files
        )
    except Exception as e:
        print_warning(f"שגיאה בעיבוד תוצרי הייצור: {e}")
        raise e
