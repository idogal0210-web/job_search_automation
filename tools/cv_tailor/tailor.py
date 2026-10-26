#!/usr/bin/env python3
"""
CV Tailoring Engine (מנוע התאמת קורות חיים למשרה)
Candidate: Ido Gal (עידו גל)
"""

import os
import sys
import argparse
import warnings
from typing import Optional, List

warnings.filterwarnings("ignore")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from tools.cv_tailor.src.utils import (
        Colors,
        print_banner,
        print_step,
        print_info,
        print_success,
        print_warning,
        print_error,
        load_config,
        load_base_profile
    )
    from tools.cv_tailor.src.scraper import scrape_job, parse_job_text, JobPosting
    from tools.cv_tailor.src.researcher import research_company, CompanyResearch
    from tools.cv_tailor.src.analyzer import analyze_job_match, print_ats_scorecard, ATSAnalysis
    from tools.cv_tailor.src.generator import generate_tailored_package, TailoredPackage
except ModuleNotFoundError:
    from src.utils import (
        Colors,
        print_banner,
        print_step,
        print_info,
        print_success,
        print_warning,
        print_error,
        load_config,
        load_base_profile
    )
    from src.scraper import scrape_job, parse_job_text, JobPosting
    from src.researcher import research_company, CompanyResearch
    from src.analyzer import analyze_job_match, print_ats_scorecard, ATSAnalysis
    from src.generator import generate_tailored_package, TailoredPackage

def get_pasted_input() -> str:
    """Prompt user to paste multi-line job description into terminal."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}הדבק כאן את תיאור המשרה (סיום בהקשת Ctrl+D או כתיבת 'EOF' בשורה נפרדת):{Colors.END}")
    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "EOF":
                break
            lines.append(line)
    except EOFError:
        pass
    return "\n".join(lines).strip()

def run_interactive_wizard(config: dict) -> argparse.Namespace:
    """Interactive wizard if no arguments provided."""
    print_banner()
    print(f"{Colors.BOLD}בחר את אופן הזנת המשרה:{Colors.END}")
    print("1. הזנת קישור (URL) של מודעת הדרושים")
    print("2. קריאה מקובץ טקסט קיים (.txt / .md)")
    print("3. הדבקה ישירה של תיאור המשרה בטרמינל")
    
    choice = input(f"\n{Colors.BOLD}הקלד בחירה (1/2/3): {Colors.END}").strip()
    args = argparse.Namespace(
        url=None,
        file=None,
        paste=False,
        text=None,
        company="",
        title="",
        lang="he",
        no_research=False,
        non_interactive=False,
        output_dir="output"
    )

    if choice == "1":
        args.url = input("הכנס URL של המשרה: ").strip()
        args.company = input("שם החברה (אופציונלי): ").strip()
        args.title = input("כותרת המשרה (אופציונלי): ").strip()
    elif choice == "2":
        args.file = input("נתיב לקובץ המשרה: ").strip()
    elif choice == "3":
        args.paste = True
    else:
        print_error("בחירה לא תקינה.")
        sys.exit(1)

    lang_choice = input(f"שפת קו״ח רצויה - עברית [he] או אנגלית [en] (ברירת מחדל: he): ").strip().lower()
    if lang_choice in ["en", "english"]:
        args.lang = "en"
    else:
        args.lang = "he"

    return args

def collect_user_clarifications(questions: List[str]) -> List[str]:
    """Interactively prompt user to answer clarification questions."""
    if not questions:
        return []
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}[?] זוהו שאלות דיוק על בסיס דרישות המשרה.{Colors.END}")
    ans = input(f"{Colors.BOLD}האם ברצונך להזין פרטים/דיוקים כעת? [y/N]: {Colors.END}").strip().lower()
    if ans not in ["y", "yes", "כן"]:
        print_info("ממשיך בייצור קו״ח על בסיס פרופיל הבסיס בלבד.")
        return []
    
    clarifications = []
    print(f"\n{Colors.CYAN}הקלד את תשובתך לכל שאלה (לחץ Enter לדילוג):{Colors.END}")
    for idx, q in enumerate(questions, 1):
        print(f"\n{Colors.BOLD}[{idx}] {q}{Colors.END}")
        user_response = input("  תשובה: ").strip()
        if user_response:
            clarifications.append(f"שאלה: {q} | מענה עידו: {user_response}")
            print_success("הדיוק נשמר וישולב בקו״ח.")
    return clarifications

def main():
    parser = argparse.ArgumentParser(
        description="מנוע התאמת קורות חיים למשרה (CV Tailoring Engine) — עידו גל",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
דוגמאות שימוש:
  1. לפי URL:
     python3 tailor.py --url "https://www.drushim.co.il/job/12345" --company "Energean" --title "מנהל תפעול"

  2. לפי קובץ:
     python3 tailor.py --file job_description.txt --lang en

  3. הדבקה ידנית:
     python3 tailor.py --paste
        """
    )
    parser.add_argument("--url", type=str, help="קישור ישיר למודעת הדרושים (Firecrawl / Web Scrape)")
    parser.add_argument("--file", type=str, help="נתיב לקובץ המכיל את תיאור המשרה")
    parser.add_argument("--paste", action="store_true", help="מצב הדבקה אינטראקטיבי של תיאור משרה")
    parser.add_argument("--text", type=str, help="טקסט תיאור המשרה ישירות כארגומנט")
    parser.add_argument("--company", type=str, default="", help="שם החברה המגייסת")
    parser.add_argument("--title", type=str, default="", help="כותרת המשרה המבוקשת")
    parser.add_argument("--lang", type=str, choices=["he", "en"], default="he", help="שפת היעד של קורות החיים (he / en)")
    parser.add_argument("--no-research", action="store_true", help="דילוג על מחקר חברה ב-Tavily")
    parser.add_argument("--non-interactive", action="store_true", help="הרצה אוטומטית ללא שאלות אינטראקטיביות")
    parser.add_argument("--output-dir", type=str, default="output", help="תיקיית יעד לשמירת קבצי הפלט")

    args = parser.parse_args()

    # If no flags passed, launch interactive wizard
    if not (args.url or args.file or args.paste or args.text):
        args = run_interactive_wizard(load_config())
    else:
        print_banner()

    config = load_config()

    # 1. Check Gemini Key
    gemini_key = config.get("gemini_api_key")
    if not gemini_key:
        print_error("מפתח GEMINI_API_KEY לא נמצא ב-.env או במערכת. אנא הגדר אותו בקובץ .env")
        sys.exit(1)

    # 2. Load Base Profile
    try:
        base_profile = load_base_profile(config.get("base_profile_path"))
        print_success("פרופיל בסיס של עידו גל (base_profile.md) נטען בהצלחה.")
    except Exception as e:
        print_error(f"שגיאה בטעינת פרופיל הבסיס: {e}")
        sys.exit(1)

    # 3. Step 1: Ingest Job Posting
    print_step(1, "קליטה ועיבוד של תיאור המשרה")
    job_posting: Optional[JobPosting] = None

    if args.url:
        job_posting = scrape_job(
            url=args.url,
            firecrawl_key=config.get("firecrawl_api_key"),
            company_hint=args.company,
            title_hint=args.title
        )
    elif args.file:
        if not os.path.exists(args.file):
            print_error(f"הקובץ המבוקש לא נמצא: {args.file}")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
        job_posting = parse_job_text(content, company_hint=args.company, title_hint=args.title, source="file")
    elif args.paste:
        content = get_pasted_input()
        if not content:
            print_error("לא הוזן תוכן משרה.")
            sys.exit(1)
        job_posting = parse_job_text(content, company_hint=args.company, title_hint=args.title, source="pasted")
    elif args.text:
        job_posting = parse_job_text(args.text, company_hint=args.company, title_hint=args.title, source="text_arg")

    if not job_posting or not job_posting.description:
        print_error("שגיאה בקריאת פרטי המשרה.")
        sys.exit(1)

    print_success(f"נקלטה משרה: {job_posting.title} │ חברה: {job_posting.company}")

    # 4. Step 2: Company Research (Tavily)
    print_step(2, "מחקר רקע על החברה והתעשייה")
    research: CompanyResearch
    if args.no_research:
        print_info("דילוג על מחקר חברה לבקשת המשתמש (--no-research).")
        research = CompanyResearch(
            company_name=job_posting.company,
            summary="מחקר חברה דולג.",
            recent_projects=[],
            culture_values=[],
            strategic_focus=""
        )
    else:
        research = research_company(
            company_name=job_posting.company,
            job_context=job_posting.description[:500],
            tavily_key=config.get("tavily_api_key")
        )

    # 5. Step 3: ATS & Requirements Analysis (Gemini)
    print_step(3, "ניתוח דרישות סף וחישוב ציון התאמת ATS")
    analysis = analyze_job_match(
        job=job_posting,
        base_profile=base_profile,
        gemini_key=gemini_key
    )

    # Print Visual Scorecard
    print_ats_scorecard(analysis)

    # Interactive Clarification Check
    user_clarifications: List[str] = []
    if not args.non_interactive and analysis.clarification_questions:
        user_clarifications = collect_user_clarifications(analysis.clarification_questions)

    # 6. Step 4: Tailoring & Output Generation (Gemini)
    print_step(4, "ייצור קו״ח מותאמים, מכתב מקדים וטיפים לראיון")
    output_package = generate_tailored_package(
        job=job_posting,
        base_profile=base_profile,
        analysis=analysis,
        research=research,
        lang=args.lang,
        clarifications=user_clarifications,
        output_dir=args.output_dir,
        gemini_key=gemini_key
    )

    # 7. Step 5: Summary & Links
    print_step(5, "סיכום וקישורים לתוצרים")
    print(f"\n{Colors.BOLD}{Colors.GREEN}[SUCCESS] תהליך ההתאמה הושלם בהצלחה!{Colors.END}")
    print(f"{Colors.BOLD}[FILES] קבצים שנוצרו ונשמרו:{Colors.END}")
    for file_path in output_package.saved_files:
        print(f"  * {file_path}")

    print(f"\n{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}             נוסח קורות החיים המותאם             {Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}\n")
    print(output_package.cv_markdown)

    print(f"\n{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}               נוסח המכתב המקדים (Cover Letter)        {Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}\n")
    print(output_package.cover_letter_markdown)

    print(f"\n{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}          [3 POINTS] 3 דגשים לראיון סינון טלפוני         {Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}======================================================{Colors.END}\n")
    for pt in output_package.interview_talking_points:
        print(f"- {pt}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}[DONE] סיום מוצלח.{Colors.END}\n")

if __name__ == "__main__":
    main()
