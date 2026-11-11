import os
import json
import re
import shutil
from datetime import datetime, timedelta
from src.state_manager import save_state_atomic, load_state
from src.job_policy import extract_curated_tags
from src.url_utils import stable_job_id, content_job_hash

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
        "base_match_score": j.get("base_match_score", j.get("match_score", 0)),
        "priority_bonus": j.get("priority_bonus", 0),
        "evaluation_complete": j.get("evaluation_complete"),
        "evidence_status": j.get("evidence_status", "legacy"),
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
        "logo": j.get("company_logo_url") or j.get("logo"),
        "company_logo_url": j.get("company_logo_url") or j.get("logo"),
        "snippet": j.get("snippet", ""),
        "stable_job_id": stable_job_id(j),
        "content_hash": content_job_hash(j),
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
    html = html.replace("__TOTAL_STARRED_JOBS__", "0")
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
    js_modules_src = os.path.join(frontend_dir, "js", "modules")
    if os.path.exists(js_modules_src):
        shutil.copytree(js_modules_src, os.path.join(docs_dir, "js", "modules"), dirs_exist_ok=True)
    app_js_src = os.path.join(frontend_dir, "js", "app.js")
    if os.path.exists(app_js_src):
        os.makedirs(os.path.join(docs_dir, "js"), exist_ok=True)
        shutil.copy2(app_js_src, os.path.join(docs_dir, "js", "app.js"))
    assets_src = os.path.join(frontend_dir, "assets")
    if os.path.exists(assets_src):
        shutil.copytree(assets_src, os.path.join(docs_dir, "assets"), dirs_exist_ok=True)
    cv_src = os.path.join(frontend_dir, "data", "cv")
    if os.path.exists(cv_src):
        os.makedirs(os.path.join(docs_dir, "career", "cv"), exist_ok=True)
        shutil.copytree(cv_src, os.path.join(docs_dir, "career", "cv"), dirs_exist_ok=True)
    sync_studio_profile_json(project_root)

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
        catalog_data = load_state(catalog_path, {}, strict=True)
        if not isinstance(catalog_data, dict):
            raise ValueError("Invalid historical catalog; refusing to publish empty history")

    compact_catalog = {link: compact_job_for_ui(j) for link, j in catalog_data.items()}
    save_state_atomic(os.path.join(data_dir, "historical_catalog.json"), compact_catalog)

    # 3. Triage state is synchronized via Supabase only; it is never published under docs/.
    sync_state_path = os.path.join(project_root, "data", "sync_state.json")
    sync_state = {}
    if os.path.exists(sync_state_path):
        sync_state = load_state(sync_state_path, {}, strict=False) or {}

    starred_set = set(sync_state.get("starred", []))
    saved_set = set(sync_state.get("saved", []))
    purged_set = set(sync_state.get("purged", []))
    rejected_set_s = set(sync_state.get("rejected", []))

    saved_count = len([s for s in sync_state.get("saved", []) if s not in starred_set])
    starred_count = len(sync_state.get("starred", []))
    rejected_count = len(sync_state.get("rejected", []))
    total_new = len([j for j in compact_jobs if j.get("link") not in starred_set and j.get("link") not in saved_set and j.get("link") not in rejected_set_s and j.get("link") not in purged_set])

    # 4. Output docs/index.html
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
    html_out = html_out.replace("__TOTAL_NEW_JOBS__", str(total_new if total_new > 0 else len(compact_jobs)))
    html_out = html_out.replace("__TOTAL_SAVED_JOBS__", str(saved_count))
    html_out = html_out.replace("__TOTAL_STARRED_JOBS__", str(starred_count))
    html_out = html_out.replace("__TOTAL_REJECTED_JOBS__", str(rejected_count))

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"[+] Successfully generated separated GitHub Pages web app at: {out_file}")
    return out_file


def update_weekly_archive(new_jobs, archive_file_path, rejected_set=None):
    """Maintains a rolling weekly view and preserves the complete historical catalog."""
    archive = load_state(archive_file_path, [], strict=True)
    if not isinstance(archive, list) or any(not isinstance(job, dict) for job in archive):
        raise ValueError("Invalid weekly archive; refusing to reset history")
    project_root = os.path.dirname(os.path.dirname(archive_file_path))
    catalog_path = os.path.join(project_root, "data", "historical_catalog.json")
    catalog = load_state(catalog_path, {}, strict=True)
    if not isinstance(catalog, dict) or any(not isinstance(job, dict) for job in catalog.values()):
        raise ValueError("Invalid historical catalog; refusing to reset history")

    from src.url_utils import canonical_job_url, job_identity, stable_job_id, content_job_hash

    # Reconcile user overrides: load purged and rejected links from sync_state.json
    all_rejected = set(rejected_set or [])
    sync_state_path = os.path.join(project_root, "data", "sync_state.json")
    sync_state = {}
    if os.path.exists(sync_state_path):
        sync_state = load_state(sync_state_path, {}, strict=False) or {}
        all_rejected.update(sync_state.get("purged", []))
        all_rejected.update(sync_state.get("rejected", []))

    rejected_canonical = {canonical_job_url(l) for l in all_rejected if l}
    rejected_stable_ids = {stable_job_id(l) for l in all_rejected if l}
    rejected_content_hashes = set()

    # Build content hashes and stable ids from existing catalog and archive records
    archive_by_link = {j.get("link"): j for j in archive if isinstance(j, dict) and j.get("link")}
    for l in all_rejected:
        job_rec = catalog.get(l) or archive_by_link.get(l)
        if isinstance(job_rec, dict):
            ch = content_job_hash(job_rec)
            if ch:
                rejected_content_hashes.add(ch)
            sid = stable_job_id(job_rec)
            if sid:
                rejected_stable_ids.add(sid)

    # Reconcile purged set: remove permanently purged jobs from catalog
    purged_links = set(sync_state.get("purged", []))
    purged_canonical = {canonical_job_url(l) for l in purged_links if l}
    purged_stable_ids = {stable_job_id(l) for l in purged_links if l}
    purged_content_hashes = set()
    for l in purged_links:
        job_rec = catalog.get(l) or archive_by_link.get(l)
        if isinstance(job_rec, dict):
            ch = content_job_hash(job_rec)
            if ch:
                purged_content_hashes.add(ch)
            sid = stable_job_id(job_rec)
            if sid:
                purged_stable_ids.add(sid)

    def _is_purged(j):
        if not isinstance(j, dict):
            return False
        link = j.get("link", "")
        if link and link in purged_links:
            return True
        c_link = canonical_job_url(link)
        if c_link and c_link in purged_canonical:
            return True
        s_id = stable_job_id(j)
        if s_id and s_id in purged_stable_ids:
            return True
        ch = content_job_hash(j)
        if ch and ch in purged_content_hashes:
            return True
        return False

    def _is_rejected(j):
        if not isinstance(j, dict):
            return True
        link = j.get("link", "")
        if not link:
            return True
        if link in all_rejected:
            return True
        c_link = canonical_job_url(link)
        if c_link and c_link in rejected_canonical:
            return True
        s_id = stable_job_id(j)
        if s_id and s_id in rejected_stable_ids:
            return True
        ch = content_job_hash(j)
        if ch and ch in rejected_content_hashes:
            return True
        return False

    # Purge permanently from catalog
    catalog = {k: v for k, v in catalog.items() if not _is_purged(v) and k not in purged_links}

    for j in archive:
        link = j.get("link")
        if link and link not in catalog and not _is_rejected(j):
            catalog[link] = j

    cutoff_date = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
    archive = [j for j in archive if j.get("date", "") >= cutoff_date]
    archive = [j for j in archive if not _is_rejected(j)]

    seen_links = {j.get("link") for j in archive}
    seen_canonical = {canonical_job_url(j.get("link")) for j in archive if j.get("link")}
    seen_identities = {job_identity(j) for j in archive if isinstance(j, dict)}
    seen_stable_ids = {stable_job_id(j) for j in archive if isinstance(j, dict)}
    seen_content_hashes = {content_job_hash(j) for j in archive if isinstance(j, dict) and content_job_hash(j)}
    today_str = datetime.now().strftime("%Y-%m-%d")

    if new_jobs:
        for job in new_jobs:
            link = job.get("link")
            if not link or _is_rejected(job):
                continue
            c_link = canonical_job_url(link)
            ident = job_identity(job)
            s_id = stable_job_id(job)
            c_hash = content_job_hash(job)

            if link in seen_links or (c_link and c_link in seen_canonical) or ident in seen_identities or (s_id and s_id in seen_stable_ids) or (c_hash and c_hash in seen_content_hashes):
                continue

            seen_links.add(link)
            if c_link:
                seen_canonical.add(c_link)
            seen_identities.add(ident)
            if s_id:
                seen_stable_ids.add(s_id)
            if c_hash:
                seen_content_hashes.add(c_hash)

            job_copy = dict(job)
            job_copy["date"] = today_str
            archive.append(job_copy)
            if link not in catalog:
                catalog[link] = job_copy

    # Persist the full history before replacing its rolling weekly view.
    # Failure must propagate: never claim a successful dashboard after data loss.
    save_state_atomic(catalog_path, catalog)
    save_state_atomic(archive_file_path, archive)
    return archive


def sync_studio_profile_json(project_root=ROOT_DIR):
    """Build deterministic non-PII studio_profile.json from tracked exclusions config for Career Studio UI."""
    from tools.cv_tailor.src.utils import load_excluded_employers

    ui_payload = {
        "source": "policy_config",
        "excluded_employers": load_excluded_employers(),
    }
    docs_target = os.path.join(project_root, "docs", "career", "studio_profile.json")
    os.makedirs(os.path.dirname(docs_target), exist_ok=True)
    save_state_atomic(docs_target, ui_payload)

    fe_data_dir = os.path.join(project_root, "frontend", "data")
    if os.path.isdir(os.path.join(project_root, "frontend")):
        os.makedirs(fe_data_dir, exist_ok=True)
        save_state_atomic(os.path.join(fe_data_dir, "studio_profile.json"), ui_payload)
    return ui_payload


def sync_frontend_to_docs(project_root=ROOT_DIR):
    """Synchronize modular frontend/ templates, assets, and studio profile to docs/ without overwriting data/*.json."""
    frontend_dir = os.path.join(project_root, "frontend")
    docs_dir = os.path.join(project_root, "docs")
    os.makedirs(docs_dir, exist_ok=True)

    pairs = [
        (os.path.join(frontend_dir, "css", "dashboard.css"), os.path.join(docs_dir, "dashboard.css")),
        (os.path.join(frontend_dir, "js", "dashboard.js"), os.path.join(docs_dir, "dashboard.js")),
        (os.path.join(frontend_dir, "js", "app.js"), os.path.join(docs_dir, "js", "app.js")),
    ]
    for src_p, dst_p in pairs:
        if os.path.exists(src_p):
            os.makedirs(os.path.dirname(dst_p), exist_ok=True)
            shutil.copy2(src_p, dst_p)

    js_modules_src = os.path.join(frontend_dir, "js", "modules")
    if os.path.exists(js_modules_src):
        shutil.copytree(js_modules_src, os.path.join(docs_dir, "js", "modules"), dirs_exist_ok=True)

    cv_src = os.path.join(frontend_dir, "data", "cv")
    if os.path.exists(cv_src):
        os.makedirs(os.path.join(docs_dir, "career", "cv"), exist_ok=True)
        shutil.copytree(cv_src, os.path.join(docs_dir, "career", "cv"), dirs_exist_ok=True)

    sync_studio_profile_json(project_root)

    # Read current docs/data/jobs.json + data/sync_state.json for non-destructive shell rendering
    jobs_json_path = os.path.join(docs_dir, "data", "jobs.json")
    compact_jobs = []
    if os.path.exists(jobs_json_path):
        payload = load_state(jobs_json_path, {}, strict=False) or {}
        compact_jobs = payload.get("jobs", []) if isinstance(payload, dict) else []

    sync_state_path = os.path.join(project_root, "data", "sync_state.json")
    sync_state = load_state(sync_state_path, {}, strict=False) or {} if os.path.exists(sync_state_path) else {}
    starred_set = set(sync_state.get("starred", []))
    saved_set = set(sync_state.get("saved", []))
    purged_set = set(sync_state.get("purged", []))
    rejected_set_s = set(sync_state.get("rejected", []))

    saved_count = len([s for s in sync_state.get("saved", []) if s not in starred_set])
    starred_count = len(sync_state.get("starred", []))
    rejected_count = len(sync_state.get("rejected", []))
    total_new = len([
        j for j in compact_jobs
        if j.get("link") not in starred_set
        and j.get("link") not in saved_set
        and j.get("link") not in rejected_set_s
        and j.get("link") not in purged_set
    ])

    tpl_src = os.path.join(frontend_dir, "templates", "index.html")
    with open(tpl_src, "r", encoding="utf-8") as f:
        html_out = f.read()

    build_id = datetime.now().strftime("%Y%m%d%H%M%S")
    now_str = datetime.now().strftime("%d.%m.%Y")
    html_out = html_out.replace("__TITLE__", "לוח משרות טכנולוגיות — עידו גל")
    html_out = html_out.replace("__REPORT_TYPE_LABEL__", "סריקה יומית")
    html_out = html_out.replace("__NOW_STR__", now_str)
    html_out = html_out.replace("__BUILD_ID__", build_id)
    html_out = html_out.replace("__TOTAL_JOBS__", str(len(compact_jobs)))
    html_out = html_out.replace("__TOTAL_NEW_JOBS__", str(total_new if total_new > 0 else len(compact_jobs)))
    html_out = html_out.replace("__TOTAL_SAVED_JOBS__", str(saved_count))
    html_out = html_out.replace("__TOTAL_STARRED_JOBS__", str(starred_count))
    html_out = html_out.replace("__TOTAL_REJECTED_JOBS__", str(rejected_count))

    out_file = os.path.join(docs_dir, "index.html")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html_out)
    return out_file
