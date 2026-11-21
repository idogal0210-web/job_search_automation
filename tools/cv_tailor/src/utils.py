import os
import sys
import html as html_lib
import importlib.util
import json
import re
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Ensure environment is loaded from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
BASE_PROFILE_PATH = os.path.join(BASE_DIR, "base_profile.md")
CAREER_STUDIO_PROFILE_PATH = os.path.join(PROJECT_ROOT, "frontend", "data", "career_studio_profile.json")
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "output")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_banner():
    banner = f"""{Colors.CYAN}{Colors.BOLD}
======================================================================
     [ENGINE] מנוע התאמת קורות חיים למשרה — CV Tailoring Engine
          עידו גל (Ido Gal) │ גרסה 1.1.0 │ Zero-Hallucination
======================================================================{Colors.END}"""
    print(banner)

def print_step(step_num: int, title: str):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}[שלב {step_num}] {title}{Colors.END}")
    print(f"{Colors.YELLOW}{'-' * (len(title) + 12)}{Colors.END}")

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK] {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}[INFO] {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}[WARN] {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}[ERR] {msg}{Colors.END}")

def load_config():
    """Load API keys and configuration."""
    config = {
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "tavily_api_key": os.getenv("TAVILY_API_KEY", "").strip(),
        "firecrawl_api_key": os.getenv("FIRECRAWL_API_KEY", "").strip(),
        "base_profile_path": BASE_PROFILE_PATH,
        "output_dir": DEFAULT_OUTPUT_DIR
    }
    return config

def format_profile_json_to_markdown(data: Dict[str, Any]) -> str:
    """Format structured candidate profile JSON into canonical base profile markdown."""
    cand = data.get("candidate", {})
    name_he = cand.get("name_he", "")
    name_en = cand.get("name_en", "")
    name_str = f"{name_he} ({name_en})" if name_en and name_he != name_en else name_he

    sections = [
        f"# פרופיל בסיס – {name_str}",
        "",
        "## פרטים אישיים",
        f"* **שם:** {name_str}",
        f"* **כותרת מקצועית (עברית):** {cand.get('title_he', '')}",
        f"* **כותרת מקצועית (אנגלית):** {cand.get('title_en', '')}",
        f"* **מגורים:** {cand.get('location', '')}",
        f"* **טלפון:** {cand.get('phone', '')}",
        f"* **אימייל:** {cand.get('email', '')}",
        f"* **לינקדאין:** [{cand.get('linkedin_url', '')}]({cand.get('linkedin_url', '')})",
        "",
        "---",
        "",
        "## תמצית מקצועית (Professional Summary)",
        "",
        "### עברית",
        cand.get("summary_he", ""),
        "",
        "### English",
        cand.get("summary_en", ""),
        "",
        "---",
        "",
        "## ניסיון מקצועי (Professional Experience)",
        "",
    ]

    for i, exp in enumerate(data.get("experience", []), 1):
        role_he = exp.get("role_he", "")
        company = exp.get("company", "")
        period = exp.get("period", "")
        role_en = exp.get("role_en", "")
        heading = f"### {i}. {role_he} | {company} | {period}"
        sections.append(heading)
        if role_en:
            sections.append(f"*({company.upper()} – {role_en} | {period})*")
        for b in exp.get("bullets", []):
            sections.append(f"* {b}")
        sections.append("")

    sections.extend([
        "---",
        "",
        "## מערכות וכלים טכנולוגיים (Technical Tools and Systems)",
    ])
    tech = data.get("technical_skills", {})
    if tech.get("control_and_operations"):
        sections.append(f"* **בקרה ומערכות ארגוניות:** {', '.join(tech['control_and_operations'])}.")
    if tech.get("digital_and_ai"):
        sections.append(f"* **ניתוח נתונים ויישומי משרד:** {', '.join(tech['digital_and_ai'])}.")
    if tech.get("energy_and_gas"):
        sections.append(f"* **אנרגיה וגז:** {', '.join(tech['energy_and_gas'])}.")
    if tech.get("drone_and_uav"):
        sections.append(f"* **רחפנים ו-UAV:** {', '.join(tech['drone_and_uav'])}.")

    sections.extend([
        "",
        "---",
        "",
        "## השכלה והכשרה מקצועית (Education and Certifications)",
    ])
    for edu in data.get("education", []):
        deg = edu.get("degree", "")
        inst = edu.get("institution", "")
        yr = edu.get("year", "")
        sections.append(f"* **{deg}** | {inst} | {yr}")
        if edu.get("final_project"):
            sections.append(f"  * פרויקט גמר: {edu['final_project']}")

    sections.extend([
        "",
        "---",
        "",
        "## שירות צבאי (Military Service)",
    ])
    for exp in data.get("experience", []):
        if "סיירת נח" in exp.get("company", "") or exp.get("id") == "exp_nahal_military":
            sections.append(f"* **{exp.get('company')}** | {exp.get('role_he')} | {exp.get('period')}")
            for b in exp.get("bullets", []):
                sections.append(f"  * {b}")

    sections.extend([
        "",
        "---",
        "",
        "## שפות (Languages)",
        "* **עברית:** שפת אם (Native).",
        "* **אנגלית:** שליטה מקצועית מלאה (Full Professional Proficiency).",
        "",
    ])
    return "\n".join(sections).strip() + "\n"


def load_base_profile(path: str = None) -> str:
    """Read the base candidate profile from career_studio_profile.json, base_profile.md, or template fallback."""
    if path:
        target_path = path
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Base profile file not found at: {target_path}")
        if target_path.endswith(".json"):
            with open(target_path, "r", encoding="utf-8") as f:
                return format_profile_json_to_markdown(json.load(f))
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()

    # Primary Single Source of Truth: career_studio_profile.json
    if os.path.exists(CAREER_STUDIO_PROFILE_PATH):
        try:
            with open(CAREER_STUDIO_PROFILE_PATH, "r", encoding="utf-8") as f:
                return format_profile_json_to_markdown(json.load(f))
        except Exception:
            pass

    # Secondary fallback: base_profile.md
    if os.path.exists(BASE_PROFILE_PATH):
        with open(BASE_PROFILE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    # Final fallback: template
    template_path = os.path.join(BASE_DIR, "base_profile.template.md")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError(f"Base profile file not found at: {BASE_PROFILE_PATH}")

def ensure_dir(dir_path: str):
    """Ensure directory exists."""
    os.makedirs(dir_path, exist_ok=True)

def load_prompt_template(filename: str) -> str:
    """Load prompt template from project-level prompts directory."""
    project_root = os.path.dirname(os.path.dirname(BASE_DIR))
    p = os.path.join(project_root, "prompts", filename)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    raise FileNotFoundError(f"Prompt not found: {p}")

def get_gemini_runtime_module():
    """Load root src/gemini_runtime.py module dynamically for shared pool and Pydantic schemas."""
    project_root = os.path.dirname(os.path.dirname(BASE_DIR))
    runtime_path = os.path.join(project_root, "src", "gemini_runtime.py")
    spec = importlib.util.spec_from_file_location("root_gemini_runtime", runtime_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_gemini_pool():
    """Load GeminiPool dynamically from project root src/gemini_runtime.py."""
    return get_gemini_runtime_module().GeminiPool()


def _get_company_matcher_module():
    """Load root src/company_matcher.py module dynamically."""
    project_root = os.path.dirname(os.path.dirname(BASE_DIR))
    matcher_path = os.path.join(project_root, "src", "company_matcher.py")
    spec = importlib.util.spec_from_file_location("root_company_matcher", matcher_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_excluded_employers() -> List[str]:
    """Load canonical excluded employers list from root src.config with normalized deduplication."""
    defaults = ["energean", "אנרג'יאן", "ingl", "נתג\"ז", "chevron", "שברון"]
    project_root = os.path.dirname(os.path.dirname(BASE_DIR))
    config_path = os.path.join(project_root, "src", "config.py")
    items: List[str] = []
    if os.path.exists(config_path):
        try:
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            spec = importlib.util.spec_from_file_location("root_config_mod", config_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "get_excluded_employers"):
                items = [str(x).strip() for x in (mod.get_excluded_employers() or []) if str(x).strip()]
        except Exception:
            items = []
    matcher = _get_company_matcher_module()
    return matcher.deduplicate_employer_list([*items, *defaults])


def check_employer_blacklist(company_name: str, job_text: str = "") -> Tuple[bool, str]:
    """Check whether a target employer matches the mandatory CV tailoring exclusion list."""
    matcher = _get_company_matcher_module()
    return matcher.match_excluded_employer(
        company_name=company_name,
        job_text=job_text,
        excluded_employers=load_excluded_employers(),
    )


def load_candidate_profile_data(path: Optional[str] = None) -> Dict[str, Any]:
    """Parse candidate profile into structured JSON-ready data from career_studio_profile.json or base_profile.md."""
    if path:
        target_path = path
    elif os.path.exists(CAREER_STUDIO_PROFILE_PATH):
        target_path = CAREER_STUDIO_PROFILE_PATH
    elif os.path.exists(BASE_PROFILE_PATH):
        target_path = BASE_PROFILE_PATH
    else:
        target_path = os.path.join(BASE_DIR, "base_profile.template.md")

    # Primary Single Source of Truth branch: career_studio_profile.json
    if target_path.endswith(".json") and os.path.exists(target_path):
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cand = data.get("candidate", {})
        name_he = cand.get("name_he", "עידו גל")
        name_en = cand.get("name_en", "Ido Gal")
        name = f"{name_he} ({name_en})" if name_en and name_he != name_en else name_he
        title_he = cand.get("title_he", "")
        title_en = cand.get("title_en", "")
        location = cand.get("location", "")
        raw_phone = cand.get("phone", "")
        raw_email = cand.get("email", "")
        linkedin_url = cand.get("linkedin_url", "")
        summary_he = cand.get("summary_he", "")
        summary_en = cand.get("summary_en", "")

        edu_lines = []
        for e in data.get("education", []):
            deg = e.get("degree", "")
            inst = e.get("institution", "")
            yr = e.get("year", "")
            edu_lines.append(f"{deg} | {inst} | {yr}".strip(" |"))
            if e.get("final_project"):
                edu_lines.append(f"פרויקט גמר: {e['final_project']}")

        exp_headings = []
        exp_bullets = []
        mil_lines = []
        for exp in data.get("experience", []):
            r = exp.get("role_he", "")
            c = exp.get("company", "")
            p = exp.get("period", "")
            exp_headings.append(f"{r} | {c} | {p}".strip(" |"))
            for b in exp.get("bullets", []):
                exp_bullets.append(b)
                if "סיירת נח" in c or exp.get("id") == "exp_nahal_military":
                    mil_lines.append(b)

        tools_lines = []
        for cat, sk_list in data.get("technical_skills", {}).items():
            if isinstance(sk_list, list):
                tools_lines.append(f"{cat}: {', '.join(sk_list)}")

        header_line = f"{name} — {title_he}" if title_he else name
        contact_line = " | ".join([x for x in (location, raw_phone, raw_email, linkedin_url) if x])
        baseline_summary_he = "\n".join([
            header_line,
            contact_line,
            summary_he,
            *[f"ניסיון: {h}" for h in exp_headings[:2]],
            *[f"השכלה: {e}" for e in edu_lines[:2]],
        ]).strip()

        anonymized_text = baseline_summary_he
        name_variants = [name, name_he, name_en]
        for nv in dict.fromkeys(v for v in name_variants if v):
            anonymized_text = anonymized_text.replace(nv, "[מועמד מנוסה]")

        for phone_tok in re.split(r"\s*/\s*", raw_phone or ""):
            tok = phone_tok.strip()
            if tok:
                anonymized_text = anonymized_text.replace(tok, "05X-XXXXXXX")
        if raw_phone:
            anonymized_text = anonymized_text.replace(raw_phone, "05X-XXXXXXX")

        if raw_email:
            anonymized_text = anonymized_text.replace(raw_email, "candidate@confidential.il")
        if linkedin_url:
            anonymized_text = anonymized_text.replace(linkedin_url, "[LinkedIn הוסתר]")

        for employer_mask, label in [
            ("Energean Israel Ltd.", "[חברת תשתיות ואנרגיה מובילה]"),
            ("Energean", "[חברת אנרגיה מובילה]"),
        ]:
            anonymized_text = anonymized_text.replace(employer_mask, label)

        raw_md = format_profile_json_to_markdown(data)

        return {
            "source": "career_studio_profile",
            "source_path": os.path.relpath(target_path, PROJECT_ROOT) if target_path.startswith(PROJECT_ROOT) else target_path,
            "name": name,
            "name_he": name_he,
            "name_en": name_en,
            "title_he": title_he,
            "title_en": title_en,
            "location": location,
            "contact": {
                "phone": raw_phone,
                "email": raw_email,
                "linkedin": linkedin_url,
                "location": location,
            },
            "summary_he": summary_he,
            "summary_en": summary_en,
            "education": edu_lines,
            "experience_titles": exp_headings,
            "experience_highlights": exp_bullets,
            "military": mil_lines,
            "tools": tools_lines,
            "technical_skills": data.get("technical_skills", {}),
            "star_stories": data.get("star_stories_catalog", []),
            "baseline_summary_he": baseline_summary_he,
            "anonymized_summary_he": anonymized_text,
            "excluded_employers": load_excluded_employers(),
            "raw_markdown": raw_md,
        }

    # Markdown parsing branch (fallback or custom path)
    using_template = (not os.path.exists(target_path)) or "template" in target_path
    markdown = load_base_profile(target_path)

    def _extract_field(label: str, default: str = "") -> str:
        m = re.search(rf"\*\*{re.escape(label)}:\*\*\s*(.+)", markdown)
        return m.group(1).strip() if m else default

    def _section_lines(prefix: str) -> List[str]:
        m = re.search(rf"^##\s+[^\n]*{re.escape(prefix)}[^\n]*\n([\s\S]*?)(?=^##\s+|\Z)", markdown, re.MULTILINE)
        if not m:
            return []
        return [ln.strip() for ln in m.group(1).splitlines() if ln.strip() and ln.strip() != "---"]

    def _sub_summary(lang_heading: str) -> str:
        m = re.search(rf"^###\s+{re.escape(lang_heading)}\s*\n([\s\S]*?)(?=^###\s+|^##\s+|\Z)", markdown, re.MULTILINE)
        if not m:
            return ""
        lines = [ln.strip() for ln in m.group(1).splitlines() if ln.strip() and ln.strip() != "---"]
        return " ".join(lines)

    raw_email = _extract_field("אימייל", "")
    raw_phone = _extract_field("טלפון", "")
    raw_linkedin = _extract_field("לינקדאין", "")
    li_match = re.search(r"\((https?://[^)]+)\)", raw_linkedin)
    linkedin_url = li_match.group(1) if li_match else raw_linkedin
    summary_he = _sub_summary("עברית")
    if not summary_he:
        plain_summary = [ln for ln in _section_lines("תמצית מקצועית") if not ln.startswith("#")]
        summary_he = " ".join(plain_summary)
    summary_en = _sub_summary("English")
    edu_lines = [re.sub(r"^\*\s*", "", ln).replace("**", "") for ln in _section_lines("השכלה והכשרה מקצועית")]
    exp_headings = [re.sub(r"^###\s+\d+\.\s*", "", ln) for ln in _section_lines("ניסיון מקצועי") if ln.startswith("### ")]
    exp_bullets = [re.sub(r"^\*\s*", "", ln) for ln in _section_lines("ניסיון מקצועי") if ln.startswith("* ")]
    mil_lines = [re.sub(r"^\*\s*", "", ln).replace("**", "") for ln in _section_lines("שירות צבאי")]
    tools_lines = [re.sub(r"^\*\s*", "", ln).replace("**", "") for ln in _section_lines("מערכות וכלים טכנולוגיים")]

    title_he = _extract_field("כותרת מקצועית (עברית)", "") or _extract_field("כותרת מקצועית", "")
    title_en = _extract_field("כותרת מקצועית (אנגלית)", "")
    name = _extract_field("שם", "Candidate")
    location = _extract_field("מגורים", "")

    header_line = f"{name} — {title_he}" if title_he else name
    contact_line = " | ".join([x for x in (location, raw_phone, raw_email, linkedin_url) if x])
    baseline_summary_he = "\n".join([
        header_line,
        contact_line,
        summary_he,
        *[f"ניסיון: {h}" for h in exp_headings[:2]],
        *[f"השכלה: {e}" for e in edu_lines[:2]],
    ]).strip()

    anonymized_text = baseline_summary_he
    name_variants = [name]
    paren_match = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", name)
    if paren_match:
        name_variants.extend([paren_match.group(1).strip(), paren_match.group(2).strip()])
    for nv in dict.fromkeys(v for v in name_variants if v):
        anonymized_text = anonymized_text.replace(nv, "[מועמד מנוסה]")

    for phone_tok in re.split(r"\s*/\s*", raw_phone or ""):
        tok = phone_tok.strip()
        if tok:
            anonymized_text = anonymized_text.replace(tok, "05X-XXXXXXX")
    if raw_phone:
        anonymized_text = anonymized_text.replace(raw_phone, "05X-XXXXXXX")

    if raw_email:
        anonymized_text = anonymized_text.replace(raw_email, "candidate@confidential.il")
    if linkedin_url:
        anonymized_text = anonymized_text.replace(linkedin_url, "[LinkedIn הוסתר]")

    for employer_mask, label in [
        ("Energean Israel Ltd.", "[חברת תשתיות ואנרגיה מובילה]"),
        ("Energean", "[חברת אנרגיה מובילה]"),
    ]:
        anonymized_text = anonymized_text.replace(employer_mask, label)

    return {
        "source": "template" if using_template else "base_profile",
        "source_path": "tools/cv_tailor/base_profile.template.md" if using_template else "tools/cv_tailor/base_profile.md",
        "name": name,
        "name_he": name.split("(")[0].strip() if "(" in name else name,
        "name_en": name.split("(")[1].replace(")", "").strip() if "(" in name else "",
        "title_he": title_he,
        "title_en": title_en,
        "location": location,
        "contact": {
            "phone": raw_phone,
            "email": raw_email,
            "linkedin": linkedin_url,
            "location": location,
        },
        "summary_he": summary_he,
        "summary_en": summary_en,
        "education": edu_lines,
        "experience_titles": exp_headings,
        "experience_highlights": exp_bullets,
        "military": mil_lines,
        "tools": tools_lines,
        "technical_skills": {},
        "star_stories": [],
        "baseline_summary_he": baseline_summary_he,
        "anonymized_summary_he": anonymized_text,
        "excluded_employers": load_excluded_employers(),
        "raw_markdown": markdown,
    }

def save_file(content: str, filename: str, output_dir: str = None) -> str:
    """Save content atomically to output directory and return full path."""
    target_dir = output_dir or DEFAULT_OUTPUT_DIR
    ensure_dir(target_dir)
    safe_name = os.path.basename(filename)
    file_path = os.path.join(target_dir, safe_name)
    tmp_path = f"{file_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, file_path)
    return file_path


def _format_inline_markdown_safe(text: str) -> str:
    """Escape raw HTML and render safe bold markers and verified web/email links."""
    escaped = html_lib.escape(text, quote=True)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

    def _safe_link(match: re.Match) -> str:
        label = match.group(1)
        href = html_lib.unescape(match.group(2)).strip()
        if re.match(r"^(?:https?://|mailto:)", href, re.IGNORECASE):
            safe_href = html_lib.escape(href, quote=True)
            return f'<a href="{safe_href}" target="_blank" rel="noopener noreferrer">{label}</a>'
        return label

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _safe_link, escaped)


def create_html_wrapper(title: str, body_markdown: str, lang: str = "he") -> str:
    """Wrap markdown content into a clean printable HTML document optimized to fit on exactly 1 single A4 page."""
    is_rtl = (lang.lower() == "he")
    dir_attr = "rtl" if is_rtl else "ltr"
    lang_attr = "he" if is_rtl else "en"
    align_style = "right" if is_rtl else "left"
    safe_title = html_lib.escape(title or "CV", quote=True)

    html_lines = []
    in_list = False

    for line in (body_markdown or "").splitlines():
        line_str = line.strip()
        if not line_str:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        if line_str.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1 class='main-title'>{_format_inline_markdown_safe(line_str[2:])}</h1>")
        elif line_str.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2 class='section-title'>{_format_inline_markdown_safe(line_str[3:])}</h2>")
        elif line_str.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3 class='item-title'>{_format_inline_markdown_safe(line_str[4:])}</h3>")
        elif line_str.startswith("* ") or line_str.startswith("- "):
            if not in_list:
                html_lines.append("<ul class='cv-list'>")
                in_list = True
            html_lines.append(f"<li>{_format_inline_markdown_safe(line_str[2:])}</li>")
        elif line_str.startswith("---"):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("<hr class='divider'>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p class='paragraph'>{_format_inline_markdown_safe(line_str)}</p>")

    if in_list:
        html_lines.append("</ul>")

    body_content = "\n".join(html_lines)

    html = f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="{dir_attr}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{safe_title}</title>
    <style>
        :root {{
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --text-main: #0f172a;
            --text-muted: #334155;
            --border-color: #cbd5e1;
            --bg-page: #f1f5f9;
            --bg-card: #ffffff;
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            direction: {dir_attr};
            text-align: {align_style};
            background-color: var(--bg-page);
            color: var(--text-main);
            padding: 20px 0;
            line-height: 1.32;
            font-size: 10.2pt;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }}
        
        .page-container {{
            width: 210mm;
            min-height: 297mm;
            margin: 0 auto;
            background: var(--bg-card);
            padding: 9mm 12mm;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
        }}
        
        .main-title {{
            font-size: 18pt;
            color: #0f172a;
            margin-bottom: 2px;
            font-weight: 800;
            line-height: 1.1;
        }}
        
        .section-title {{
            font-size: 11pt;
            color: var(--primary-dark);
            margin-top: 6px;
            margin-bottom: 3px;
            font-weight: 700;
            border-bottom: 1.5px solid var(--primary);
            padding-bottom: 1px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }}
        
        .item-title {{
            font-size: 10.2pt;
            color: #0f172a;
            margin-top: 4px;
            margin-bottom: 1px;
            font-weight: 700;
        }}
        
        .paragraph {{
            margin: 2px 0;
            font-size: 9.8pt;
            color: var(--text-main);
            line-height: 1.32;
        }}
        
        .cv-list {{
            margin: 2px 0 3px 0;
            padding-right: {"16px" if is_rtl else "0"};
            padding-left: {"0" if is_rtl else "16px"};
        }}
        
        .cv-list li {{
            margin-bottom: 1.8px;
            font-size: 9.6pt;
            color: var(--text-main);
            line-height: 1.3;
        }}
        
        strong {{
            color: #0f172a;
            font-weight: 700;
        }}
        
        .divider {{
            border: 0;
            border-top: 1px solid var(--border-color);
            margin: 4px 0;
        }}
        
        a {{
            color: var(--primary);
            text-decoration: none;
        }}

        @media print {{
            @page {{
                size: A4 portrait;
                margin: 0;
            }}
            body {{
                background-color: #ffffff;
                padding: 0;
                margin: 0;
            }}
            .page-container {{
                box-shadow: none;
                padding: 8mm 11mm;
                width: 100%;
                max-width: 100%;
                min-height: auto;
                height: 100%;
            }}
            .section-title {{
                break-after: avoid;
            }}
            .item-title, .cv-list li {{
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-container">
        {body_content}
    </div>
</body>
</html>"""
    return html