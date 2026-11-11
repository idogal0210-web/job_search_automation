#!/usr/bin/env python3
"""
tests/test_studio_bridge.py

Unit and HTTP integration tests for unified Career Studio -> tools/cv_tailor -> GeminiPool pipeline.
Covers single-source profile parsing, employer blacklist gating, SSRF & CORS guards,
schema-validated Gemini calls, degraded fallback honesty (no fabricated scores),
generator happy-path persistence, HTML sanitization, and local bridge HTTP endpoints.
"""

import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from scripts.studio_bridge import (
    BridgeServices,
    is_allowed_origin,
    make_handler,
    validate_public_http_url,
)
from src.gemini_runtime import EvaluationUnavailable
from tools.cv_tailor.src.analyzer import analyze_job_match
from tools.cv_tailor.src.generator import generate_tailored_package
from tools.cv_tailor.src.researcher import CompanyResearch
from tools.cv_tailor.src.scraper import JobPosting
from tools.cv_tailor.src.utils import (
    check_employer_blacklist,
    create_html_wrapper,
    load_candidate_profile_data,
)


class _DummyGeminiClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key


class _SuccessMockPool:
    def __init__(self):
        self.models = ("gemini-3.8-flash", "gemini-3.5-flash")

    def generate_json(self, client, prompt, *, schema=None, temperature=None, health=None):
        name = schema.__name__ if schema is not None else ""
        if name == "AtsStudioAnalysisSchema":
            return {
                "overall_score": 88,
                "match_summary": "התאמה גבוהה לתפקיד מנהל אתר סולארי בזכות רקע הנדסאי מכונות והתקנות PV.",
                "scorecard": [
                    {"category": "השכלה והסמכות", "score": 90},
                    {"category": "ניסיון תפעולי", "score": 86},
                ],
                "matched_keywords": ["PV", "SCADA"],
                "missing_keywords": ["BESS"],
                "key_strengths": ["הנדסאי מכונות מוסמך", "ניסיון שטח סולארי ב-MER"],
                "clarification_questions": ["האם ניהלת קבלני משנה באתר PV מסחרי?"],
                "recommended_changes": ["להבליט ניהול ממשקי תקשורת ותהליכי בקרה"],
                "unmatched_requirements": ["רישיון חשמלאי מוסמך פעיל נדרש במודעה (בלימודים עד 2026)"],
                "evaluation_model": "gemini-3.8-flash",
            }
        if name == "TailoredCvPackageSchema":
            return {
                "cv_markdown": "# עידו גל\n**הנדסאי מכונות | בקרת גז טבעי ותפעול מערכות אנרגיה**\n* בקר גז — תפעול ומוצר | Energean Israel Ltd.",
                "cover_letter_markdown": "# מכתב מקדים\nשלום רב, אשמח להצטרף לצוות Enlight לשיחה קצרה.",
                "interview_talking_points": ["דגש 1: SCADA וניטור 24/7", "דגש 2: עבודה בגובה והתקנות MER"],
                "unmatched_requirements": ["חשמלאי מוסמך פעיל (צפי סיום דצמבר 2026)"],
                "evaluation_model": "gemini-3.8-flash",
            }
        if name == "CvTailoredBulletSchema":
            return {
                "rewritten_bullet": "ניטרתי באופן רציף לחצים וספיקות ב-10 תחנות PRMS תוך עמידה ב-Zero LTI.",
                "tone_mode": "technical",
                "active_verb": "ניטרתי",
                "system_scope": "PRMS",
                "metric_or_hse": "Zero LTI",
                "grounded_in_profile": True,
                "note_he": "מבוסס על ניסיון Energean",
                "evaluation_model": "gemini-3.8-flash",
            }
        if name == "StarInterviewEvaluationSchema":
            return {
                "total_score": 89,
                "situation_score": 18,
                "situation_feedback": "תיאור זירה תפעולית ברור.",
                "task_score": 18,
                "task_feedback": "המשימה הבטיחותית הוגדרה במדויק.",
                "action_score": 35,
                "action_feedback": "פעולות בידוד ב-SCADA והפעלת ESD מתוארות היטב.",
                "result_score": 18,
                "result_feedback": "תוצאה עם Zero LTI תוך 7 דקות.",
                "golden_answer": "במשמרת בקרה זיהיתי ירידת לחץ, הפעלתי נוהל חירום והבטחנו Zero LTI.",
                "improvement_tips": ["לציין מפורשות תיאום מול נתג״ז."],
                "evaluation_model": "gemini-3.8-flash",
            }
        return {}


class _FailingPool:
    def __init__(self):
        self.models = ("gemini-3.8-flash",)

    def generate_json(self, client, prompt, *, schema=None, temperature=None, health=None):
        raise EvaluationUnavailable({"gemini-3.8-flash": "unavailable"})


class TestCareerStudioBridgeAndEngine(unittest.TestCase):
    """End-to-end verification of Stage 1-5 Career Studio fixes."""

    def test_single_source_profile_parsing_and_anonymization(self):
        data = load_candidate_profile_data()
        self.assertIn("עידו גל", data["name"])
        self.assertIn("energean", data["excluded_employers"])
        self.assertIn("ingl", data["excluded_employers"])
        self.assertIn("0526328886", data["baseline_summary_he"])
        self.assertNotIn("0526328886", data["anonymized_summary_he"])
        self.assertNotIn("idogal0210@gmail.com", data["anonymized_summary_he"])
        self.assertNotIn("Energean", data["anonymized_summary_he"])

    def test_employer_blacklist_gate(self):
        blocked, reason = check_employer_blacklist("Energean Israel Ltd.", "בקר גז")
        self.assertTrue(blocked)
        self.assertIn("energean", reason.lower())

        ok_blocked, _ = check_employer_blacklist("Enlight Renewable Energy", "מנהל אתר סולארי PV")
        self.assertFalse(ok_blocked)

    def test_html_wrapper_sanitizes_xss_and_unsafe_links(self):
        raw_md = "# <script>alert(1)</script>\n* [Click](javascript:alert(2)) and [Site](https://example.com)"
        rendered = create_html_wrapper("Title <img src=x onerror=alert(1)>", raw_md, lang="he")
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("javascript:", rendered)
        self.assertNotIn("<img", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn('href="https://example.com"', rendered)

    def test_analyzer_degraded_never_fabricates_confident_score(self):
        posting = JobPosting(
            url=None,
            title="Solar Site Manager",
            company="Doral",
            location="Negev",
            raw_text="Solar PV site manager SCADA",
            description="Manage Solar PV and SCADA systems.",
            requirements="Practical Mechanical Engineer",
        )
        with patch("tools.cv_tailor.src.analyzer.genai.Client", _DummyGeminiClient), \
             patch("tools.cv_tailor.src.analyzer.get_gemini_pool", return_value=_FailingPool()):
            result = analyze_job_match(posting, "עידו גל הנדסאי מכונות", gemini_key="fake-key")
        self.assertTrue(result.degraded)
        self.assertIsNone(result.overall_score)

    def test_generator_happy_path_with_pool_and_output_files(self):
        posting = JobPosting(
            url="https://example.com/enlight-pv",
            title="Solar Operations",
            company="Enlight",
            location="Tel Aviv",
            raw_text="Solar PV operations",
            description="Operate solar PV sites.",
            requirements="Practical engineer",
        )
        analysis = analyze_job_match.__wrapped__(posting, "base", "k") if hasattr(analyze_job_match, "__wrapped__") else None
        if analysis is None:
            with patch("tools.cv_tailor.src.analyzer.genai.Client", _DummyGeminiClient), \
                 patch("tools.cv_tailor.src.analyzer.get_gemini_pool", return_value=_SuccessMockPool()):
                analysis = analyze_job_match(posting, "עידו גל", gemini_key="fake-key")
        research = CompanyResearch("Enlight", "חברת אנרגיה מתחדשת", ["PV"], [], "", is_live_data=True)
        with tempfile.TemporaryDirectory() as tmp_out:
            with patch("tools.cv_tailor.src.generator.genai.Client", _DummyGeminiClient), \
                 patch("tools.cv_tailor.src.generator.get_gemini_pool", return_value=_SuccessMockPool()):
                pkg = generate_tailored_package(
                    job=posting,
                    base_profile="עידו גל",
                    analysis=analysis,
                    research=research,
                    lang="he",
                    clarifications=["ניהלתי משמרות 24/7"],
                    output_dir=tmp_out,
                    gemini_key="fake-key",
                    tone_mode="operational",
                    save_outputs=True,
                )
            self.assertEqual(len(pkg.saved_files), 5)
            for path in pkg.saved_files:
                self.assertTrue(os.path.exists(path), f"Missing generated file {path}")
            self.assertIn("Energean Israel Ltd.", pkg.cv_markdown)
            self.assertIn("@page", pkg.cv_html)
            self.assertGreater(len(pkg.unmatched_requirements), 0)

    def test_ssrf_and_cors_origin_guards(self):
        for bad_url in (
            "http://127.0.0.1:8765/api/health",
            "http://localhost:8000",
            "http://169.254.169.254/latest/meta-data",
            "file:///etc/passwd",
        ):
            ok, _ = validate_public_http_url(bad_url)
            self.assertFalse(ok, f"Expected SSRF guard to reject {bad_url}")

        self.assertTrue(is_allowed_origin("http://127.0.0.1:8000"))
        self.assertTrue(is_allowed_origin("https://idogal0210-web.github.io"))
        self.assertFalse(is_allowed_origin("https://untrusted.example.com"))

    def test_http_bridge_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp_out:
            svc = BridgeServices(pool=_SuccessMockPool(), output_dir=tmp_out)
            cfg = {"gemini_api_key": "fake-key", "tavily_api_key": "", "firecrawl_api_key": ""}

            def _request(path: str, payload=None, method: str = "POST"):
                data = json.dumps(payload).encode("utf-8") if payload is not None else None
                headers = {"Origin": "http://127.0.0.1:8000"}
                if data is not None:
                    headers["Content-Type"] = "application/json"
                req = Request(f"http://127.0.0.1:{port}{path}", data=data, headers=headers, method=method)
                try:
                    with urlopen(req, timeout=5) as resp:
                        return resp.status, json.loads(resp.read().decode("utf-8"))
                except HTTPError as err:
                    body = err.read().decode("utf-8")
                    code = err.code
                    err.close()
                    return code, json.loads(body)

            server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(svc))
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with patch.object(svc, "get_config", return_value=cfg), \
                     patch("scripts.studio_bridge.genai.Client", _DummyGeminiClient), \
                     patch("tools.cv_tailor.src.analyzer.genai.Client", _DummyGeminiClient), \
                     patch("tools.cv_tailor.src.analyzer.get_gemini_pool", return_value=svc.pool), \
                     patch("tools.cv_tailor.src.generator.genai.Client", _DummyGeminiClient), \
                     patch("tools.cv_tailor.src.generator.get_gemini_pool", return_value=svc.pool):

                    st, health = _request("/api/health", method="GET")
                    self.assertEqual(st, 200)
                    self.assertTrue(health["gemini_configured"])
                    self.assertTrue(health["base_profile_loaded"])

                    st, blk = _request("/api/ats/analyze", {"job_text": "בקר גז", "company": "Energean"})
                    self.assertEqual(st, 422)
                    self.assertTrue(blk["blocked"])

                    st, ats = _request("/api/ats/analyze", {
                        "job_text": "דרוש הנדסאי מכונות עם ניסיון PV ב-SCADA",
                        "company": "Enlight",
                        "title": "Site Manager",
                        "run_research": False,
                    })
                    self.assertEqual(st, 200)
                    self.assertEqual(ats["analysis"]["overall_score"], 88)

                    st, pkg_res = _request("/api/studio/tailor", {
                        "job_text": "דרוש הנדסאי מכונות",
                        "company": "Enlight",
                        "title": "Site Manager",
                        "lang": "he",
                        "tone_mode": "technical",
                        "clarifications": ["ניסיון SCADA"],
                        "analysis": ats["analysis"],
                        "research": ats["research"],
                        "save_outputs": True,
                    })
                    self.assertEqual(st, 200)
                    self.assertTrue(pkg_res["verification"]["zero_emoji"])
                    self.assertEqual(len(pkg_res["package"]["saved_files"]), 5)
                    self.assertGreater(len(list(Path(tmp_out).glob("*.html"))), 0)

                    st, bullet_res = _request("/api/writer/tailor", {
                        "raw_bullet": "עבדתי בניטור גז",
                        "tone_mode": "technical",
                    })
                    self.assertEqual(st, 200)
                    self.assertEqual(bullet_res["result"]["tone_mode"], "technical")

                    st, iv_res = _request("/api/interview/evaluate", {
                        "question": "נפילת לחץ במתקן PRMS",
                        "category": "crisis",
                        "answer": "סגרתי ESD דרך SCADA ותוצאה Zero LTI תוך 7 דקות",
                    })
                    self.assertEqual(st, 200)
                    self.assertEqual(iv_res["evaluation"]["total_score"], 89)
                    self.assertIn("golden_answer", iv_res["evaluation"])
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
