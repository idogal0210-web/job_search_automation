import os
import json
import re
import shutil
from datetime import datetime, timedelta
from src.state_manager import save_state_atomic
from src.job_policy import extract_curated_tags

# Load HTML template from frontend/templates/index.html
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_PATH = os.path.join(ROOT_DIR, "frontend", "templates", "index.html")

if os.path.exists(TEMPLATE_PATH):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        HTML_TEMPLATE = f.read()
else:
    HTML_TEMPLATE = "<!DOCTYPE html><html lang='he' dir='rtl'><head><title>__TITLE__</title></head><body><h1>__TITLE__</h1></body></html>"


def compact_job_for_ui(j):
    """Filter out private/internal fields, keeping strictly UI-required metadata."""
    if not isinstance(j, dict):
        return {}
    tags_info = extract_curated_tags(j)
    return {
        "link": j.get("link", ""),
        "title": j.get("title", ""),
        "company": j.get("company", ""),
        "location": j.get("location", ""),
        "date": j.get("date", ""),
        "source": j.get("source", ""),
        "match_score": j.get("match_score", 0),
        "sector_key": j.get("sector_key", "energy"),
        "company_domain_product": j.get("company_domain_product", ""),
        "company_summary": j.get("company_summary", ""),
        "job_summary": j.get("job_summary", ""),
        "company_requirements": j.get("company_requirements", ""),
        "experience_strengths": j.get("experience_strengths", ""),
        "reasoning": j.get("reasoning", ""),
        "key_highlights": j.get("key_highlights", ""),
        "salary_range": j.get("salary_range", ""),
        "salary_source_type": j.get("salary_source_type", ""),
        "salary_source_label": j.get("salary_source_label", ""),
        "salary_evidence": j.get("salary_evidence", ""),
        "salary_source_url": j.get("salary_source_url", ""),
        "p25": j.get("p25"),
        "p75": j.get("p75"),
        "logo": j.get("logo"),
        "snippet": j.get("snippet", ""),
        "requirement_assessments": j.get("requirement_assessments", []),
        "fit_gaps": j.get("fit_gaps", ""),
        "is_direct_ats": j.get("is_direct_ats", False),
        "is_field_work": j.get("is_field_work", tags_info["is_field_work"]),
        "provides_company_car": j.get("provides_company_car", tags_info["provides_company_car"]),
        "is_shifts_24_7": j.get("is_shifts_24_7", tags_info["is_shifts_24_7"]),
        "is_junior_friendly": j.get("is_junior_friendly", tags_info["is_junior_friendly"]),
        "curated_tags": j.get("curated_tags") or tags_info["curated_tags"]
    }


def generate_interactive_html(jobs, rejected_links, is_weekly=False):
    """Generate standalone interactive HTML markup for the dashboard."""
    now_str = datetime.now().strftime("%d.%m.%Y")
    build_id = datetime.now().strftime("%Y%m%d%H%M%S")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"
    total_new = len(jobs)

    html = HTML_TEMPLATE
    html = html.replace("__TITLE__", "לוח משרות טכנולוגיות — עידו גל")
    html = html.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html = html.replace("__NOW_STR__", now_str)
    html = html.replace("__BUILD_ID__", build_id)
    html = html.replace("__TOTAL_JOBS__", str(total_new))
    html = html.replace("__TOTAL_NEW_JOBS__", str(total_new))
    html = html.replace("__TOTAL_SAVED_JOBS__", "0")
    html = html.replace("__TOTAL_STARRED_JOBS__", "7")
    html = html.replace("__TOTAL_REJECTED_JOBS__", "0")
    return html


def build_and_save_docs_app(jobs, rejected_links, project_root, is_weekly=False):
    """
    Builds the production-ready GitHub Pages dashboard application.
    Enforces separation of concerns:
    - HTML shell -> docs/index.html (~25KB)
    - CSS styles -> docs/dashboard.css
    - Client JS  -> docs/dashboard.js
    - Jobs data  -> docs/data/jobs.json (schema version 2.0.0)
    - Catalog    -> docs/data/historical_catalog.json (loaded on-demand)
    """
    docs_dir = os.path.join(project_root, "docs")
    data_dir = os.path.join(docs_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    out_file = os.path.join(docs_dir, "index.html")

    frontend_dir = os.path.join(ROOT_DIR, "frontend")
    css_src = os.path.join(frontend_dir, "css", "dashboard.css")
    js_src = os.path.join(frontend_dir, "js", "dashboard.js")
    tpl_src = os.path.join(frontend_dir, "templates", "index.html")

    # Copy frontend assets to docs
    if os.path.exists(css_src):
        shutil.copy2(css_src, os.path.join(docs_dir, "dashboard.css"))
    if os.path.exists(js_src):
        shutil.copy2(js_src, os.path.join(docs_dir, "dashboard.js"))

    build_id = datetime.now().strftime("%Y%m%d%H%M%S")
    now_str = datetime.now().strftime("%d.%m.%Y")
    report_type_label = "סיכום שבועי" if is_weekly else "סריקה יומית"

    # Pre-sort jobs by date descending (newest first), then by match_score descending
    def _sort_key(j):
        d = j.get("date", "") or "0000-00-00"
        try:
            s = int(j.get("match_score", 0) or 0)
        except Exception:
            s = 0
        return (d, s)

    sorted_jobs = sorted(jobs, key=_sort_key, reverse=True)
    compact_jobs = [compact_job_for_ui(j) for j in sorted_jobs]

    # 1. Output docs/data/jobs.json
    jobs_payload = {
        "schema_version": "2.0.0",
        "build_id": build_id,
        "generated_at": datetime.now().isoformat(),
        "total_jobs": len(compact_jobs),
        "jobs": compact_jobs
    }
    save_state_atomic(os.path.join(data_dir, "jobs.json"), jobs_payload)

    # 2. Output docs/data/historical_catalog.json
    catalog_path = os.path.join(project_root, "data", "historical_catalog.json")
    catalog_data = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
        except Exception:
            catalog_data = {}

    compact_catalog = {link: compact_job_for_ui(j) for link, j in catalog_data.items()}
    save_state_atomic(os.path.join(data_dir, "historical_catalog.json"), compact_catalog)

    # 3. Output docs/index.html
    html_tpl = HTML_TEMPLATE
    if os.path.exists(tpl_src):
        with open(tpl_src, "r", encoding="utf-8") as f:
            html_tpl = f.read()

    title = "לוח משרות טכנולוגיות — עידו גל"
    html_out = html_tpl.replace("__TITLE__", title)
    html_out = html_out.replace("__REPORT_TYPE_LABEL__", report_type_label)
    html_out = html_out.replace("__NOW_STR__", now_str)
    html_out = html_out.replace("__BUILD_ID__", build_id)
    html_out = html_out.replace("__TOTAL_JOBS__", str(len(compact_jobs)))
    html_out = html_out.replace("__TOTAL_NEW_JOBS__", str(len(compact_jobs)))
    html_out = html_out.replace("__TOTAL_SAVED_JOBS__", "0")
    html_out = html_out.replace("__TOTAL_STARRED_JOBS__", "7")
    html_out = html_out.replace("__TOTAL_REJECTED_JOBS__", "0")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[+] Successfully generated separated GitHub Pages web app at: {out_file}")
    return out_file


def update_weekly_archive(new_jobs, archive_file_path, rejected_set):
    """Maintains 7-day rolling window in weekly_archive.json and prunes historical catalog."""
    archive = []
    if os.path.exists(archive_file_path):
        try:
            with open(archive_file_path, "r", encoding="utf-8") as f:
                archive = json.load(f)
        except Exception:
            archive = []

    # Always keep historical catalog updated with all jobs before pruning
    project_root = os.path.dirname(os.path.dirname(archive_file_path))
    catalog_path = os.path.join(project_root, "data", "historical_catalog.json")
    catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            catalog = {}

    for j in archive:
        link = j.get("link")
        if link and link not in catalog:
            catalog[link] = j

    cutoff_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    archive = [j for j in archive if j.get("date", "") >= cutoff_date]
    archive = [j for j in archive if j.get("link") not in rejected_set]

    seen_links = {j.get("link") for j in archive}
    today_str = datetime.now().strftime("%Y-%m-%d")

    if new_jobs:
        for job in new_jobs:
            link = job.get("link")
            if link and link not in seen_links and link not in rejected_set:
                seen_links.add(link)
                job_copy = dict(job)
                job_copy["date"] = today_str
                archive.append(job_copy)
                if link not in catalog:
                    catalog[link] = job_copy

    save_state_atomic(archive_file_path, archive)

    try:
        # Retention policy: prune historical catalog to max 1500 items if needed, preserving newest
        if len(catalog) > 1500:
            sorted_items = sorted(catalog.items(), key=lambda kv: kv[1].get("date", ""), reverse=True)
            catalog = dict(sorted_items[:1500])
        save_state_atomic(catalog_path, catalog)
    except Exception as e:
        print(f"[WARN] Failed to atomically save historical catalog: {e}")

    return archive
