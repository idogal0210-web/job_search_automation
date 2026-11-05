# -*- coding: utf-8 -*-
"""
Unit & Integration tests for Career Studio Redesign:
- Split-Pane layout structure and compact top step bar
- Pydantic schemas (StarInterviewEvaluation, CvTailoredBullet, AtsSemanticMatch)
- Local Python Bridge endpoints and offline fallback resilience
- Interview Practice History persistence in LocalStorage
"""
import json
import os
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

from src.gemini_runtime import (
    AtsSemanticMatch,
    CvTailoredBullet,
    StarInterviewEvaluation,
)
from scripts.studio_bridge import (
    fallback_ats_match,
    fallback_interview_evaluate,
    fallback_writer_tailor,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_HTML_PATH = ROOT_DIR / "frontend" / "templates" / "index.html"
DASHBOARD_CSS_PATH = ROOT_DIR / "frontend" / "css" / "dashboard.css"
DASHBOARD_JS_PATH = ROOT_DIR / "frontend" / "js" / "dashboard.js"


class TestCareerStudioSplitPaneAndBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "html.parser")
        cls.css = DASHBOARD_CSS_PATH.read_text(encoding="utf-8")
        cls.js = DASHBOARD_JS_PATH.read_text(encoding="utf-8")

    def test_split_pane_markup_and_compact_top_stepbar(self):
        # Verify compact stepbar and active CV top pill
        self.assertIsNotNone(self.soup.find(class_="studio-compact-stepbar-wrap"))
        self.assertIsNotNone(self.soup.find(class_="studio-cv-top-pill"))
        # Verify split-pane grid in ATS module
        ats_grid = self.soup.find(id="atsModuleContent")
        self.assertIsNotNone(ats_grid)
        self.assertIn("studio-split-pane-grid", ats_grid.get("class", []))
        self.assertIsNotNone(self.soup.find(class_="studio-input-pane"))
        self.assertIsNotNone(self.soup.find(class_="studio-output-pane"))
        # Verify AI thinking banner and interview history section
        self.assertIsNotNone(self.soup.find(id="studioAiThinkingBanner"))
        self.assertIsNotNone(self.soup.find(id="interviewHistorySection"))
        self.assertIsNotNone(self.soup.find(id="interviewHistoryList"))

    def test_css_split_pane_and_mobile_touch_targets(self):
        self.assertIn(".studio-split-pane-grid", self.css)
        self.assertIn("minmax(0, 45fr) minmax(0, 55fr)", self.css)
        self.assertIn("min-block-size: 44px", self.css)
        self.assertIn("flex-direction: column", self.css)

    def test_pydantic_schemas_strict_validation(self):
        star = StarInterviewEvaluation(
            situation_score=24,
            task_score=23,
            action_score=25,
            result_score=24,
            total_score=96,
            situation_feedback="זירת משמרת לילה הוגדרה היטב",
            task_feedback="יעד בטיחות ברור",
            action_feedback="הפעלת מגוף ESD ובידוד קו",
            result_feedback="0 תאונות LTI",
            strengths=["סמכות שטח"],
            improvements=["פירוט נוסף על נתג״ז"],
            improved_answer="תשובת STAR מלאה ומדויקת.",
        )
        self.assertEqual(star.total_score, 96)

        bullet = CvTailoredBullet(
            transformed_bullet="ניטרתי לחצים במערכת SCADA לאורך משמרות 24/7 עם 100% רציפות תפקודית.",
            tone_mode="technical",
            quality_score=95,
            has_active_verb=True,
            has_metric=True,
            has_scope=True,
            suggestions=["שילוב מדד כמותי"],
        )
        self.assertEqual(bullet.tone_mode, "technical")

        ats = AtsSemanticMatch(
            semantic_score=88,
            summary="התאמה גבוהה לתפקיד בקר גז טבעי.",
            matched_strengths=["SCADA", "AVEVA"],
            critical_gaps=[],
            tailoring_tips=["הדגש ניסיון במשמרות 24/7"],
        )
        self.assertEqual(ats.semantic_score, 88)

    def test_local_bridge_fallbacks_offline_resilience(self):
        res_int = fallback_interview_evaluate({
            "question": "תרחיש דליפת גז ב-PRMS",
            "answer": "במשמרת לילה ב-PRMS זיהיתי דליפה ב-SCADA, הפעלתי נוהל פינוי וסגרתי ESD תוך 5 דקות עם Zero LTI."
        })
        self.assertEqual(res_int["source"], "fallback_local")
        self.assertGreaterEqual(res_int["total_score"], 85)

        res_writer = fallback_writer_tailor({
            "raw_bullet": "עבדתי בחדר בקרה במשמרות לילה",
            "tone_mode": "operational"
        })
        self.assertEqual(res_writer["source"], "fallback_local")
        self.assertEqual(res_writer["tone_mode"], "operational")
        self.assertTrue(len(res_writer["transformed_bullet"]) > 20)

        res_ats = fallback_ats_match({
            "job_text": "דרוש מהנדס מכונות B.Sc בלבד"
        })
        self.assertEqual(res_ats["source"], "fallback_local")
        self.assertLessEqual(res_ats["semantic_score"], 60)

    def test_client_js_exposes_bridge_and_history_functions(self):
        self.assertIn("async function callStudioAi", self.js)
        self.assertIn("window.callStudioAi = callStudioAi", self.js)
        self.assertIn("INTERVIEW_HISTORY_STORAGE_KEY", self.js)
        self.assertIn("saveInterviewPracticeEntry", self.js)


if __name__ == "__main__":
    unittest.main()
