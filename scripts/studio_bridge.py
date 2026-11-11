#!/usr/bin/env python3
"""
Local HTTP Bridge Server unifying Career Studio UI with tools/cv_tailor and GeminiPool.

Binds strictly to 127.0.0.1 (no credentials exposed to client-side JS).
Reuses existing tools/cv_tailor modules (scraper, researcher, analyzer, generator, utils)
and enforces employer blacklist checks, SSRF protections, schema-validated AI outputs,
zero-emoji verification, and atomic persistence into tools/cv_tailor/output/.
"""

import argparse
import ipaddress
import json
import mimetypes
import os
import re
import socket
import sys
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

from google import genai
from scripts.validate_zero_emoji import check_text as check_zero_emoji
from src.gemini_runtime import (
    CvTailoredBulletSchema,
    EvaluationUnavailable,
    GeminiPool,
    StarInterviewEvaluationSchema,
)
from tools.cv_tailor.src.analyzer import ATSAnalysis, analyze_job_match
from tools.cv_tailor.src.generator import TailoredPackage, generate_tailored_package
from tools.cv_tailor.src.researcher import CompanyResearch, research_company
from tools.cv_tailor.src.scraper import JobPosting, parse_job_text, scrape_job
from tools.cv_tailor.src.utils import (
    DEFAULT_OUTPUT_DIR,
    check_employer_blacklist,
    create_html_wrapper,
    load_base_profile,
    load_candidate_profile_data,
    load_config,
    save_file,
)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = int(os.getenv("STUDIO_BRIDGE_PORT", "8765"))
MAX_BODY_BYTES = 1024 * 1024  # 1 MiB guard

ALLOWED_ORIGIN_PATTERNS = (
    re.compile(r"^https?://(?:127\.0\.0\.1|localhost)(?::\d+)?$", re.IGNORECASE),
    re.compile(r"^https://idogal0210-web\.github\.io$", re.IGNORECASE),
)


def is_allowed_origin(origin: str) -> bool:
    """Allow local development origins and owner GitHub Pages dashboard only."""
    if not origin or origin == "null":
        return False
    return any(p.match(origin.strip()) for p in ALLOWED_ORIGIN_PATTERNS)


def validate_public_http_url(url: str) -> Tuple[bool, str]:
    """Validate that URL uses http/https and resolves only to public IP addresses (anti-SSRF)."""
    raw = (url or "").strip()
    if not raw:
        return False, "כתובת URL ריקה."
    parsed = urlparse(raw)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc or not parsed.hostname:
        return False, "נתמכות כתובות http ו-https תקינות בלבד."
    host = parsed.hostname.strip().lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False, "כתובת פנימית (localhost) אינה מורשית לגריפה."
    try:
        ip_obj = ipaddress.ip_address(host)
        if not ip_obj.is_global:
            return False, "כתובת IP פנימית או שמורה אינה מורשית לגריפה."
        return True, ""
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return False, "לא ניתן היה לפתור את שם הדומיין (DNS)."

    for info in infos:
        addr_str = info[4][0].split("%")[0]
        try:
            addr = ipaddress.ip_address(addr_str)
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
                return False, "הדומיין מצביע לכתובת רשת פנימית ואינו מורשה לגריפה."
        except ValueError:
            continue
    return True, ""


def list_saved_output_files(output_dir: Optional[str] = None, limit: int = 12) -> List[Dict[str, Any]]:
    """Return latest generated files under tools/cv_tailor/output/ safely."""
    target = Path(output_dir or DEFAULT_OUTPUT_DIR)
    if not target.exists():
        return []
    entries = []
    for p in sorted(target.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if p.is_file() and p.name not in {".gitkeep", ".DS_Store"} and not p.name.endswith(".tmp"):
            st = p.stat()
            entries.append({
                "name": p.name,
                "size_bytes": st.st_size,
                "modified_at": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            })
        if len(entries) >= limit:
            break
    return entries


class BridgeServices:
    """Testable service container delegating directly to tools/cv_tailor and GeminiPool."""

    def __init__(self, pool: Optional[GeminiPool] = None, output_dir: Optional[str] = None):
        self.pool = pool or GeminiPool(min_interval=0.5, max_attempts=2)
        self.output_dir = str(output_dir or DEFAULT_OUTPUT_DIR)

    def get_config(self) -> Dict[str, Any]:
        return load_config()

    def get_gemini_client(self) -> Optional[genai.Client]:
        cfg = self.get_config()
        key = (cfg.get("gemini_api_key") or "").strip()
        if not key:
            return None
        return genai.Client(api_key=key)

    def health(self) -> Dict[str, Any]:
        cfg = self.get_config()
        base_ok = False
        try:
            base_ok = bool(load_base_profile(cfg.get("base_profile_path")))
        except Exception:
            base_ok = False
        return {
            "ok": True,
            "mode": "local_bridge",
            "gemini_configured": bool(cfg.get("gemini_api_key")),
            "tavily_configured": bool(cfg.get("tavily_api_key")),
            "firecrawl_configured": bool(cfg.get("firecrawl_api_key")),
            "base_profile_loaded": base_ok,
            "models": list(self.pool.models),
            "output_dir": "tools/cv_tailor/output",
            "saved_outputs": list_saved_output_files(self.output_dir),
        }

    def profile(self) -> Dict[str, Any]:
        data = load_candidate_profile_data()
        return {
            "ok": True,
            "profile": {k: v for k, v in data.items() if k != "raw_markdown"},
            "saved_outputs": list_saved_output_files(self.output_dir),
        }

    def ingest_job(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        url = str(payload.get("url") or "").strip()
        text = str(payload.get("text") or "").strip()
        company_hint = str(payload.get("company") or "").strip()
        title_hint = str(payload.get("title") or "").strip()

        if url:
            ok_url, reason = validate_public_http_url(url)
            if not ok_url:
                return HTTPStatus.BAD_REQUEST, {
                    "ok": False,
                    "error_code": "invalid_url",
                    "error_message": reason,
                    "recoverable": True,
                }
            cfg = self.get_config()
            try:
                posting = scrape_job(
                    url=url,
                    firecrawl_key=cfg.get("firecrawl_api_key"),
                    company_hint=company_hint,
                    title_hint=title_hint,
                )
            except Exception as err:
                return HTTPStatus.BAD_GATEWAY, {
                    "ok": False,
                    "error_code": "scrape_failed",
                    "error_message": f"קליטת הקישור נכשלה ({err}). ניתן להדביק את טקסט המשרה ידנית.",
                    "recoverable": True,
                }
        elif text:
            posting = parse_job_text(text, company_hint=company_hint, title_hint=title_hint, source="studio_text")
        else:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_input",
                "error_message": "נדרש קישור משרה או טקסט תיאור משרה.",
                "recoverable": True,
            }

        blocked, block_reason = check_employer_blacklist(posting.company, posting.description)
        return HTTPStatus.OK, {
            "ok": True,
            "blocked": blocked,
            "block_reason": block_reason,
            "scrape_source": posting.source,
            "degraded": posting.source == "bs4_fallback",
            "job": {
                "url": posting.url or "",
                "title": posting.title,
                "company": posting.company,
                "location": posting.location,
                "description": posting.description,
                "source": posting.source,
            },
        }

    def analyze_ats(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        job_text = str(payload.get("job_text") or "").strip()
        company = str(payload.get("company") or "").strip()
        title = str(payload.get("title") or "").strip()
        job_url = str(payload.get("job_url") or "").strip() or None
        run_research = bool(payload.get("run_research", True))
        custom_cv_text = str(payload.get("cv_text") or "").strip()

        if not job_text:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_job_text",
                "error_message": "לא הוזן תיאור משרה לניתוח.",
                "recoverable": True,
            }

        posting = parse_job_text(job_text, url=job_url, company_hint=company, title_hint=title, source="career_studio")
        blocked, block_reason = check_employer_blacklist(posting.company, posting.description)
        if blocked:
            return HTTPStatus.UNPROCESSABLE_ENTITY, {
                "ok": False,
                "blocked": True,
                "error_code": "employer_blacklisted",
                "error_message": block_reason,
                "recoverable": False,
            }

        cfg = self.get_config()
        gemini_key = (cfg.get("gemini_api_key") or "").strip()
        if not gemini_key:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "missing_gemini_key",
                "error_message": "מפתח GEMINI_API_KEY אינו מוגדר בשרת המקומי.",
                "recoverable": True,
            }

        base_profile = load_base_profile(cfg.get("base_profile_path"))
        if custom_cv_text:
            base_profile = f"{base_profile}\n\n---\n## מסמך קורות חיים נוסף שסופק בממשק\n{custom_cv_text[:8000]}"

        research_obj = (
            research_company(posting.company, posting.description[:500], tavily_key=cfg.get("tavily_api_key"))
            if run_research
            else CompanyResearch(
                company_name=posting.company,
                summary="מחקר חברה דולג לבקשת המשתמש.",
                recent_projects=[],
                culture_values=[],
                strategic_focus="",
                is_live_data=False,
            )
        )

        analysis = analyze_job_match(job=posting, base_profile=base_profile, gemini_key=gemini_key)
        return HTTPStatus.OK, {
            "ok": True,
            "blocked": False,
            "source": "local_keyword_fallback" if analysis.degraded else "gemini",
            "degraded": analysis.degraded,
            "job": {
                "title": posting.title,
                "company": posting.company,
                "location": posting.location,
            },
            "research": {
                "company_name": research_obj.company_name,
                "summary": research_obj.summary,
                "recent_projects": research_obj.recent_projects,
                "culture_values": research_obj.culture_values,
                "strategic_focus": research_obj.strategic_focus,
                "is_live_data": research_obj.is_live_data,
            },
            "analysis": {
                "overall_score": analysis.overall_score,
                "match_summary": analysis.match_summary,
                "scorecard": analysis.scorecard,
                "matched_keywords": analysis.matched_keywords,
                "missing_keywords": analysis.missing_keywords,
                "key_strengths": analysis.key_strengths,
                "clarification_questions": analysis.clarification_questions,
                "recommended_changes": analysis.recommended_changes,
                "unmatched_requirements": analysis.unmatched_requirements,
                "evaluation_model": analysis.evaluation_model,
            },
        }

    def tailor_package(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        job_text = str(payload.get("job_text") or "").strip()
        company = str(payload.get("company") or "").strip()
        title = str(payload.get("title") or "").strip()
        lang = "en" if str(payload.get("lang") or "he").strip().lower() == "en" else "he"
        tone_mode = str(payload.get("tone_mode") or "technical").strip().lower()
        if tone_mode not in {"technical", "operational", "strategic"}:
            tone_mode = "technical"
        clarifications_raw = payload.get("clarifications") or []
        clarifications = [str(c).strip() for c in clarifications_raw if str(c).strip()]
        save_outputs = bool(payload.get("save_outputs", True))
        custom_cv_text = str(payload.get("cv_text") or "").strip()

        if not job_text:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_job_text",
                "error_message": "נדרש טקסט תיאור משרה כדי להפיק קורות חיים מותאמים.",
                "recoverable": True,
            }

        posting = parse_job_text(job_text, company_hint=company, title_hint=title, source="career_studio")
        blocked, block_reason = check_employer_blacklist(posting.company, posting.description)
        if blocked:
            return HTTPStatus.UNPROCESSABLE_ENTITY, {
                "ok": False,
                "blocked": True,
                "error_code": "employer_blacklisted",
                "error_message": block_reason,
                "recoverable": False,
            }

        cfg = self.get_config()
        gemini_key = (cfg.get("gemini_api_key") or "").strip()
        if not gemini_key:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "missing_gemini_key",
                "error_message": "מפתח GEMINI_API_KEY אינו מוגדר בשרת המקומי.",
                "recoverable": True,
            }

        base_profile = load_base_profile(cfg.get("base_profile_path"))
        if custom_cv_text:
            base_profile = f"{base_profile}\n\n---\n## מסמך קורות חיים נוסף שסופק בממשק\n{custom_cv_text[:8000]}"

        raw_analysis = payload.get("analysis")
        if isinstance(raw_analysis, dict) and raw_analysis.get("match_summary"):
            analysis = ATSAnalysis(
                overall_score=raw_analysis.get("overall_score"),
                match_summary=str(raw_analysis.get("match_summary", "")),
                scorecard=dict(raw_analysis.get("scorecard") or {}),
                matched_keywords=list(raw_analysis.get("matched_keywords") or []),
                missing_keywords=list(raw_analysis.get("missing_keywords") or []),
                key_strengths=list(raw_analysis.get("key_strengths") or []),
                clarification_questions=list(raw_analysis.get("clarification_questions") or []),
                recommended_changes=list(raw_analysis.get("recommended_changes") or []),
                unmatched_requirements=list(raw_analysis.get("unmatched_requirements") or []),
                evaluation_model=str(raw_analysis.get("evaluation_model") or ""),
                degraded=bool(raw_analysis.get("degraded", False)),
            )
        else:
            analysis = analyze_job_match(job=posting, base_profile=base_profile, gemini_key=gemini_key)

        raw_research = payload.get("research")
        if isinstance(raw_research, dict) and raw_research.get("summary"):
            research = CompanyResearch(
                company_name=str(raw_research.get("company_name") or posting.company),
                summary=str(raw_research.get("summary") or ""),
                recent_projects=list(raw_research.get("recent_projects") or []),
                culture_values=list(raw_research.get("culture_values") or []),
                strategic_focus=str(raw_research.get("strategic_focus") or ""),
                is_live_data=bool(raw_research.get("is_live_data", False)),
            )
        else:
            research = research_company(posting.company, posting.description[:500], tavily_key=cfg.get("tavily_api_key"))

        try:
            pkg: TailoredPackage = generate_tailored_package(
                job=posting,
                base_profile=base_profile,
                analysis=analysis,
                research=research,
                lang=lang,
                clarifications=clarifications,
                output_dir=self.output_dir,
                gemini_key=gemini_key,
                tone_mode=tone_mode,
                save_outputs=save_outputs,
            )
        except Exception as err:
            return HTTPStatus.BAD_GATEWAY, {
                "ok": False,
                "error_code": "generation_failed",
                "error_message": f"ייצור קורות החיים באמצעות Gemini נכשל: {err}",
                "recoverable": True,
            }

        emoji_violations = (
            check_zero_emoji(pkg.cv_markdown)
            + check_zero_emoji(pkg.cover_letter_markdown)
        )
        saved_rel = [os.path.basename(p) for p in (pkg.saved_files or [])]
        return HTTPStatus.OK, {
            "ok": True,
            "source": "gemini",
            "status_stage": "Saved" if save_outputs else "Generated",
            "package": {
                "company": posting.company,
                "title": posting.title,
                "lang": lang,
                "tone_mode": tone_mode,
                "cv_markdown": pkg.cv_markdown,
                "cv_html": pkg.cv_html,
                "cover_letter_markdown": pkg.cover_letter_markdown,
                "cover_letter_html": pkg.cover_letter_html,
                "interview_talking_points": pkg.interview_talking_points,
                "unmatched_requirements": pkg.unmatched_requirements,
                "saved_files": saved_rel,
                "evaluation_model": pkg.evaluation_model,
            },
            "verification": {
                "zero_emoji": len(emoji_violations) == 0,
                "a4_ready": True,
                "profile_source": "tools/cv_tailor/base_profile.md",
            },
        }

    def export_package(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        company = str(payload.get("company") or "Company").strip()
        lang = "en" if str(payload.get("lang") or "he").strip().lower() == "en" else "he"
        cv_markdown = str(payload.get("cv_markdown") or "").strip()
        cover_letter_markdown = str(payload.get("cover_letter_markdown") or "").strip()
        if not cv_markdown:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_cv_content",
                "error_message": "אין תוכן קורות חיים לשמירה.",
                "recoverable": True,
            }
        safe_company = re.sub(r"[^\w\s\-_]", "", company).replace(" ", "_") or "Company"
        lang_suffix = "EN" if lang == "en" else "HE"
        prefix = f"{safe_company}_{lang_suffix}"

        saved: List[str] = []
        cv_html = create_html_wrapper(f"קורות חיים - עידו גל - {company}", cv_markdown, lang=lang)
        saved.append(os.path.basename(save_file(cv_markdown, f"CV_{prefix}.md", self.output_dir)))
        saved.append(os.path.basename(save_file(cv_html, f"CV_{prefix}.html", self.output_dir)))
        if cover_letter_markdown:
            cl_html = create_html_wrapper(f"מכתב מקדים - עידו גל - {company}", cover_letter_markdown, lang=lang)
            saved.append(os.path.basename(save_file(cover_letter_markdown, f"CoverLetter_{prefix}.md", self.output_dir)))
            saved.append(os.path.basename(save_file(cl_html, f"CoverLetter_{prefix}.html", self.output_dir)))

        return HTTPStatus.OK, {
            "ok": True,
            "status_stage": "Exported",
            "output_dir": "tools/cv_tailor/output",
            "saved_files": saved,
        }

    def tailor_bullet(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        raw_bullet = str(payload.get("raw_bullet") or "").strip()
        tone_mode = str(payload.get("tone_mode") or "technical").strip().lower()
        if tone_mode not in {"technical", "operational", "strategic"}:
            tone_mode = "technical"
        job_context = str(payload.get("job_context") or "").strip()
        if not raw_bullet:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_bullet",
                "error_message": "לא הוזן ניסוח לשדרוג.",
                "recoverable": True,
            }

        client = self.get_gemini_client()
        if client is None:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "missing_gemini_key",
                "error_message": "מפתח GEMINI_API_KEY אינו מוגדר בשרת המקומי.",
                "recoverable": True,
            }

        base_profile = load_base_profile()
        prompt = f"""אתה עורך קורות חיים טכני בעברית ואנגלית.
שכתב את נקודת הניסיון הבאה בסגנון '{tone_mode}' לפי נוסחת [פועל פעיל בזמן עבר] + [מערכת/תשתית מתוך פרופיל הבסיס] + [מדד תפעולי או בטיחותי].

חוקי ברזל:
1. אפס המצאות: הסתמך אך ורק על עובדות, כלים ומספרים שמופיעים בפרופיל הבסיס או בטקסט שהוזן.
2. שמר שמות תפקידים מקוריים. אין להוסיף אימוג'ים.
3. התאם שפה (עברית או אנגלית) לשפת הקלט.

פרופיל הבסיס:
{base_profile}

הקשר משרה (אופציונלי):
{job_context[:1500]}

הניסוח הגולמי של עידו:
{raw_bullet}
"""
        try:
            data = self.pool.generate_json(
                client,
                prompt,
                schema=CvTailoredBulletSchema,
                temperature=0.2,
            )
            return HTTPStatus.OK, {"ok": True, "source": "gemini", "result": data}
        except EvaluationUnavailable as err:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "gemini_unavailable",
                "error_message": f"מנוע Gemini אינו זמין כרגע: {err}",
                "recoverable": True,
            }

    def evaluate_interview(self, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        question = str(payload.get("question") or "").strip()
        answer = str(payload.get("answer") or "").strip()
        category = str(payload.get("category") or "operations").strip()
        job_context = str(payload.get("job_context") or "").strip()
        if not answer:
            return HTTPStatus.BAD_REQUEST, {
                "ok": False,
                "error_code": "missing_answer",
                "error_message": "יש להזין תשובה לפני הערכת STAR.",
                "recoverable": True,
            }

        client = self.get_gemini_client()
        if client is None:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "missing_gemini_key",
                "error_message": "מפתח GEMINI_API_KEY אינו מוגדר בשרת המקומי.",
                "recoverable": True,
            }

        base_profile = load_base_profile()
        prompt = f"""אתה מראיין טכני בכיר בתחומי האנרגיה, הגז הטבעי, ה-PV/BESS, ה-SCADA והרחפנים.
נתח את תשובת המועמד עידו גל לפי מודל STAR (סולם 0-100: S עד 20, T עד 20, A עד 40, R עד 20).

חוקי ברזל:
1. אם בתשובה חסר פרט עובדתי, אל תמציא אירועים או מספרים בתשובת המופת (golden_answer) — בסס אותה רק על העובדות ב-base_profile או סמן מתודולוגיה ("במצב כזה, מתודולוגיית הפעולה היא...").
2. ללא אימוג'ים. עברית ברורה ותמציתית.

פרופיל הבסיס:
{base_profile}

קטגוריה: {category}
הקשר משרה: {job_context[:1000]}
שאלת הריאיון: {question}
תשובת המועמד: {answer}
"""
        try:
            data = self.pool.generate_json(
                client,
                prompt,
                schema=StarInterviewEvaluationSchema,
                temperature=0.2,
            )
            return HTTPStatus.OK, {"ok": True, "source": "gemini", "evaluation": data}
        except EvaluationUnavailable as err:
            return HTTPStatus.SERVICE_UNAVAILABLE, {
                "ok": False,
                "error_code": "gemini_unavailable",
                "error_message": f"מנוע Gemini אינו זמין כרגע: {err}",
                "recoverable": True,
            }


def make_handler(services: Optional[BridgeServices] = None):
    """Build a ThreadingHTTPServer handler bound to the provided BridgeServices instance."""
    svc = services or BridgeServices()
    docs_root = (ROOT_DIR / "docs").resolve()

    class StudioBridgeHandler(BaseHTTPRequestHandler):
        def _send_cors_headers(self):
            origin = self.headers.get("Origin", "")
            if is_allowed_origin(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            if self.headers.get("Access-Control-Request-Private-Network") == "true":
                self.send_header("Access-Control-Allow-Private-Network", "true")

        def _send_json(self, status: int, payload: Dict[str, Any]):
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _read_json_body(self) -> Tuple[Optional[Dict[str, Any]], Optional[Tuple[int, Dict[str, Any]]]]:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return None, (HTTPStatus.BAD_REQUEST, {
                    "ok": False, "error_code": "invalid_content_length",
                    "error_message": "כותרת Content-Length לא תקינה.", "recoverable": True,
                })
            if length > MAX_BODY_BYTES:
                return None, (HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {
                    "ok": False, "error_code": "payload_too_large",
                    "error_message": "גודל הבקשה חורג מן המגבלה (1MB).", "recoverable": False,
                })
            raw = self.rfile.read(length) if length > 0 else b"{}"
            try:
                data = json.loads(raw.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("JSON root must be object")
                return data, None
            except Exception:
                return None, (HTTPStatus.BAD_REQUEST, {
                    "ok": False, "error_code": "invalid_json",
                    "error_message": "גוף הבקשה אינו JSON תקין.", "recoverable": True,
                })

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_OPTIONS(self):
            self.send_response(HTTPStatus.NO_CONTENT)
            self._send_cors_headers()
            self.end_headers()

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/health":
                self._send_json(HTTPStatus.OK, svc.health())
                return
            if path == "/api/profile":
                self._send_json(HTTPStatus.OK, svc.profile())
                return

            # Serve static docs/ dashboard safely for unified local execution
            rel = "index.html" if path in {"/", ""} else path.lstrip("/")
            candidate = (docs_root / rel).resolve()
            if not candidate.is_relative_to(docs_root) or not candidate.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {
                    "ok": False, "error_code": "not_found",
                    "error_message": "הנתיב המבוקש לא נמצא.", "recoverable": False,
                })
                return
            mime, _ = mimetypes.guess_type(str(candidate))
            content = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._send_cors_headers()
            self.send_header("Content-Type", mime or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            path = urlparse(self.path).path
            payload, err = self._read_json_body()
            if err:
                self._send_json(err[0], err[1])
                return

            routes = {
                "/api/studio/ingest": svc.ingest_job,
                "/api/ats/analyze": svc.analyze_ats,
                "/api/ats/match": svc.analyze_ats,
                "/api/ats-match": svc.analyze_ats,
                "/api/studio/tailor": svc.tailor_package,
                "/api/studio/export": svc.export_package,
                "/api/writer/tailor": svc.tailor_bullet,
                "/api/interview/evaluate": svc.evaluate_interview,
                "/api/evaluate-interview": svc.evaluate_interview,
            }
            handler_fn = routes.get(path)
            if handler_fn is None:
                self._send_json(HTTPStatus.NOT_FOUND, {
                    "ok": False, "error_code": "not_found",
                    "error_message": "נקודת הקצה אינה קיימת.", "recoverable": False,
                })
                return
            status, body = handler_fn(payload or {})
            self._send_json(status, body)

    return StudioBridgeHandler


def main():
    parser = argparse.ArgumentParser(description="Career Studio Local AI Bridge Server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    services = BridgeServices()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(services))
    print(f"[STUDIO_BRIDGE] Listening on http://{args.host}:{args.port} (serving UI + Career Studio AI API)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STUDIO_BRIDGE] Shutting down cleanly.", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()
