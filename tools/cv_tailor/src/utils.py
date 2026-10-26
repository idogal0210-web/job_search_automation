import os
import sys
import json
import re
import warnings
from datetime import datetime
from dotenv import load_dotenv

warnings.filterwarnings("ignore")

# Ensure environment is loaded from .env
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_PROFILE_PATH = os.path.join(BASE_DIR, "base_profile.md")
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

def load_base_profile(path: str = None) -> str:
    """Read the base candidate profile from base_profile.md (or template fallback)."""
    target_path = path or BASE_PROFILE_PATH
    if not os.path.exists(target_path):
        template_path = os.path.join(BASE_DIR, "base_profile.template.md")
        if os.path.exists(template_path):
            target_path = template_path
        else:
            raise FileNotFoundError(f"Base profile file not found at: {target_path}")
    with open(target_path, "r", encoding="utf-8") as f:
        return f.read()

def ensure_dir(dir_path: str):
    """Ensure directory exists."""
    os.makedirs(dir_path, exist_ok=True)

def save_file(content: str, filename: str, output_dir: str = None) -> str:
    """Save content to output directory and return full path."""
    target_dir = output_dir or DEFAULT_OUTPUT_DIR
    ensure_dir(target_dir)
    file_path = os.path.join(target_dir, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

def create_html_wrapper(title: str, body_markdown: str, lang: str = "he") -> str:
    """Wrap markdown content into a clean printable HTML document optimized to fit on exactly 1 single A4 page."""
    is_rtl = (lang.lower() == "he")
    dir_attr = "rtl" if is_rtl else "ltr"
    lang_attr = "he" if is_rtl else "en"
    align_style = "right" if is_rtl else "left"

    html_lines = []
    in_list = False
    
    for line in body_markdown.splitlines():
        line_str = line.strip()
        if not line_str:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
            
        if line_str.startswith("# "):
            if in_list: html_lines.append("</ul>"); in_list = False
            header_text = line_str[2:]
            html_lines.append(f"<h1 class='main-title'>{header_text}</h1>")
        elif line_str.startswith("## "):
            if in_list: html_lines.append("</ul>"); in_list = False
            header_text = line_str[3:]
            html_lines.append(f"<h2 class='section-title'>{header_text}</h2>")
        elif line_str.startswith("### "):
            if in_list: html_lines.append("</ul>"); in_list = False
            header_text = line_str[4:]
            html_lines.append(f"<h3 class='item-title'>{header_text}</h3>")
        elif line_str.startswith("* ") or line_str.startswith("- "):
            if not in_list:
                html_lines.append("<ul class='cv-list'>")
                in_list = True
            item_text = line_str[2:]
            html_lines.append(f"<li>{item_text}</li>")
        elif line_str.startswith("---"):
            if in_list: html_lines.append("</ul>"); in_list = False
            html_lines.append("<hr class='divider'>")
        else:
            if in_list: html_lines.append("</ul>"); in_list = False
            html_lines.append(f"<p class='paragraph'>{line_str}</p>")
            
    if in_list:
        html_lines.append("</ul>")

    body_content = "\n".join(html_lines)
    body_content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", body_content)
    body_content = re.sub(r"\[(.*?)\]\((.*?)\)", r"<a href=\"\2\" target=\"_blank\">\1</a>", body_content)

    html = f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="{dir_attr}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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