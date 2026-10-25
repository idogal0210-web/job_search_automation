# -*- coding: utf-8 -*-
"""
Specification and E2E Tests for Career Studio Milestones 4, 5, and 6:
- Milestone 4: Visual Simulator, 6-Second Heatmap, Auto-Fit A4 Engine, Mobile Viewport
- Milestone 5: Multi-Version CV Hub & Interactive Kanban Application Tracker
- Milestone 6: Voice Interview Simulator, STAR Analysis, LinkedIn Alignment, Skill Gap Engine & Anonymizer
"""

import os
import unittest
from bs4 import BeautifulSoup
from scripts.validate_zero_emoji import check_text

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_TEMPLATE_PATH = os.path.join(REPO_ROOT, "frontend", "templates", "index.html")
DOCS_INDEX_PATH = os.path.join(REPO_ROOT, "docs", "index.html")
DASHBOARD_JS_PATH = os.path.join(REPO_ROOT, "frontend", "js", "dashboard.js")
DASHBOARD_CSS_PATH = os.path.join(REPO_ROOT, "frontend", "css", "dashboard.css")
CV_DIR = os.path.join(REPO_ROOT, "frontend", "data", "cv")
DOCS_CV_DIR = os.path.join(REPO_ROOT, "docs", "career", "cv")


class TestCareerStudioMilestones456(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INDEX_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            cls.template_html = f.read()
        cls.soup = BeautifulSoup(cls.template_html, "html.parser")

        with open(DASHBOARD_JS_PATH, "r", encoding="utf-8") as f:
            cls.dashboard_js = f.read()

        with open(DASHBOARD_CSS_PATH, "r", encoding="utf-8") as f:
            cls.dashboard_css = f.read()

    # -------------------------------------------------------------------------
    # Milestone 4 Tests: Visual Simulator, Heatmap, Auto-Fit & Mobile
    # -------------------------------------------------------------------------
    def test_m4_01_visual_module_container_exists(self):
        panel = self.soup.find(id="studioModuleVisual")
        self.assertIsNotNone(panel, "studioModuleVisual must exist")
        self.assertEqual(panel.get("role"), "tabpanel")
        self.assertEqual(panel.get("aria-labelledby"), "studioTabVisual")

    def test_m4_02_visual_controls_toolbar(self):
        self.assertIsNotNone(self.soup.find(id="visualCvVersionSelect"))
        self.assertIsNotNone(self.soup.find(id="btnToggleHeatmap"))
        self.assertIsNotNone(self.soup.find(id="btnAutoFitA4"))
        self.assertIsNotNone(self.soup.find(id="btnToggleMobilePreview"))
        self.assertIsNotNone(self.soup.find(id="btnPrintVisualCv"))

    def test_m4_03_heatmap_overlay_hotspots(self):
        overlay = self.soup.find(id="heatmapOverlayLayer")
        self.assertIsNotNone(overlay)
        hotspots = overlay.find_all(class_="heatmap-hotspot")
        self.assertGreaterEqual(len(hotspots), 4, "Must have at least 4 F-pattern focal hotspots")
        classes = " ".join([" ".join(h.get("class", [])) for h in hotspots])
        self.assertIn("spot-header", classes)
        self.assertIn("spot-summary", classes)
        self.assertIn("spot-experience", classes)
        self.assertIn("spot-skills", classes)

    def test_m4_04_cv_html_files_exist_in_frontend_and_docs(self):
        required_files = [
            "cv_gas_he.html",
            "cv_solar_he.html",
            "cv_drones_he.html",
            "cv_base_en.html"
        ]
        for fname in required_files:
            fe_path = os.path.join(CV_DIR, fname)
            docs_path = os.path.join(DOCS_CV_DIR, fname)
            self.assertTrue(os.path.exists(fe_path), f"File {fe_path} must exist")
            self.assertTrue(os.path.exists(docs_path), f"File {docs_path} must exist in docs")
            # Verify file has content and no emojis
            with open(fe_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertGreater(len(content), 1000)
                self.assertEqual(len(check_text(content)), 0)

    def test_m4_05_visual_js_functions_exposed(self):
        self.assertIn("function initVisualModule", self.dashboard_js)
        self.assertIn("function changeVisualCvVersion", self.dashboard_js)
        self.assertIn("function toggleHeatmapOverlay", self.dashboard_js)
        self.assertIn("function applyA4AutoFit", self.dashboard_js)
        self.assertIn("function toggleMobilePreview", self.dashboard_js)
        self.assertIn("window.changeVisualCvVersion =", self.dashboard_js)

    # -------------------------------------------------------------------------
    # Milestone 5 Tests: Multi-Version CV Hub & Kanban Tracker
    # -------------------------------------------------------------------------
    def test_m5_01_kanban_module_container_exists(self):
        panel = self.soup.find(id="studioModuleKanban")
        self.assertIsNotNone(panel, "studioModuleKanban must exist")
        self.assertEqual(panel.get("role"), "tabpanel")
        self.assertEqual(panel.get("aria-labelledby"), "studioTabKanban")

    def test_m5_02_kanban_subtabs_exist(self):
        self.assertIsNotNone(self.soup.find(id="subtabKanbanBoardBtn"))
        self.assertIsNotNone(self.soup.find(id="subtabCvHubBtn"))
        self.assertIsNotNone(self.soup.find(id="kanbanBoardView"))
        self.assertIsNotNone(self.soup.find(id="kanbanCvHubView"))

    def test_m5_03_kanban_all_six_columns_exist(self):
        statuses = ["saved", "applied", "screening", "interview", "offer", "rejected"]
        for st in statuses:
            col = self.soup.find(id="kanbanCol_" + st)
            self.assertIsNotNone(col, f"Kanban column for status '{st}' must exist")
            cards_container = self.soup.find(id="cards_" + st)
            self.assertIsNotNone(cards_container, f"Cards container for '{st}' must exist")
            count_badge = self.soup.find(id="count_" + st)
            self.assertIsNotNone(count_badge, f"Count badge for '{st}' must exist")

    def test_m5_04_cv_hub_four_cards_exist(self):
        cards = self.soup.find_all(class_="cv-hub-card")
        self.assertEqual(len(cards), 4, "Must have exactly 4 tailored CV cards in Hub")
        titles = [c.find(class_="cv-hub-title").get_text() for c in cards]
        self.assertTrue(any("גז טבעי" in t for t in titles))
        self.assertTrue(any("סולארי" in t or "PV" in t for t in titles))
        self.assertTrue(any("כטב״ם" in t or "רחפנים" in t for t in titles))
        self.assertTrue(any("Mechanical" in t or "Gas" in t for t in titles))

    def test_m5_05_kanban_modal_exists(self):
        modal = self.soup.find(id="addKanbanModal")
        self.assertIsNotNone(modal)
        self.assertIsNotNone(self.soup.find(id="kanbanCompanyInput"))
        self.assertIsNotNone(self.soup.find(id="kanbanRoleInput"))
        self.assertIsNotNone(self.soup.find(id="kanbanStatusSelect"))
        self.assertIsNotNone(self.soup.find(id="kanbanVersionSelect"))

    def test_m5_06_kanban_js_functions_exposed(self):
        self.assertIn("function initKanbanModule", self.dashboard_js)
        self.assertIn("function switchKanbanSubtab", self.dashboard_js)
        self.assertIn("function moveKanbanCard", self.dashboard_js)
        self.assertIn("function deleteKanbanCard", self.dashboard_js)
        self.assertIn("window.initKanbanModule =", self.dashboard_js)

    # -------------------------------------------------------------------------
    # Milestone 6 Tests: Interview, STAR, LinkedIn, Skill Gaps & Anonymizer
    # -------------------------------------------------------------------------
    def test_m6_01_interview_module_container_exists(self):
        panel = self.soup.find(id="studioModuleInterview")
        self.assertIsNotNone(panel, "studioModuleInterview must exist")
        self.assertEqual(panel.get("role"), "tabpanel")
        self.assertEqual(panel.get("aria-labelledby"), "studioTabInterview")

    def test_m6_02_voice_and_star_elements_exist(self):
        self.assertIsNotNone(self.soup.find(id="btnRecordVoice"))
        self.assertIsNotNone(self.soup.find(id="voiceRecTimer"))
        self.assertIsNotNone(self.soup.find(id="voiceWaveCanvas"))
        self.assertIsNotNone(self.soup.find(id="interviewAnswerInput"))
        self.assertIsNotNone(self.soup.find(id="starFeedbackBox"))
        self.assertIsNotNone(self.soup.find(id="starTotalScore"))
        self.assertIsNotNone(self.soup.find(id="starSituationText"))
        self.assertIsNotNone(self.soup.find(id="starTaskText"))
        self.assertIsNotNone(self.soup.find(id="starActionText"))
        self.assertIsNotNone(self.soup.find(id="starResultText"))

    def test_m6_03_linkedin_alignment_rows_exist(self):
        rows = self.soup.find_all(class_="linkedin-check-row")
        self.assertGreaterEqual(len(rows), 3, "Must have at least 3 LinkedIn check comparisons")
        row_titles = [r.find(class_="check-title").get_text() for r in rows]
        self.assertTrue(any("Headline" in t or "כותרת" in t for t in row_titles))
        self.assertTrue(any("Licenses" in t or "הסמכות" in t for t in row_titles))
        self.assertTrue(any("תפקיד" in t or "תעסוקתי" in t for t in row_titles))

    def test_m6_04_skills_and_anonymizer_container_exists(self):
        panel = self.soup.find(id="studioModuleSkills")
        self.assertIsNotNone(panel, "studioModuleSkills must exist")
        self.assertEqual(panel.get("role"), "tabpanel")
        self.assertEqual(panel.get("aria-labelledby"), "studioTabSkills")

    def test_m6_05_skill_gap_cards_exist(self):
        skill_cards = self.soup.find_all(class_="skill-rec-card")
        self.assertGreaterEqual(len(skill_cards), 4, "Must offer at least 4 in-demand skill recommendations")
        titles = [c.find(class_="skill-title").get_text() for c in skill_cards]
        self.assertTrue(any("PMP" in t for t in titles))
        self.assertTrue(any("PLC" in t or "SCADA" in t for t in titles))
        self.assertTrue(any("BMS" in t or "CEM" in t for t in titles))
        self.assertTrue(any("Six Sigma" in t for t in titles))

    def test_m6_06_anonymizer_elements_exist(self):
        self.assertIsNotNone(self.soup.find(id="anonToggleCheckbox"))
        self.assertIsNotNone(self.soup.find(id="anonymizedPreviewArea"))
        rules = self.soup.find_all(class_="anon-rule-row")
        self.assertGreaterEqual(len(rules), 3)

    def test_m6_07_interview_and_skills_js_exposed(self):
        self.assertIn("function initInterviewModule", self.dashboard_js)
        self.assertIn("function toggleVoiceRecording", self.dashboard_js)
        self.assertIn("function evaluateStarAnswer", self.dashboard_js)
        self.assertIn("function copyLinkedInOptimizedBio", self.dashboard_js)
        self.assertIn("function initSkillsModule", self.dashboard_js)
        self.assertIn("function toggleAnonymizerMode", self.dashboard_js)
        self.assertIn("function copyAnonymizedCv", self.dashboard_js)

    # -------------------------------------------------------------------------
    # Zero-Emoji and Iconography Policy Verification
    # -------------------------------------------------------------------------
    def test_zero_emoji_across_all_templates(self):
        violations = check_text(self.template_html)
        self.assertEqual(len(violations), 0, f"Found emoji in index.html: {violations}")

    def test_zero_emoji_across_dashboard_js(self):
        violations = check_text(self.dashboard_js)
        self.assertEqual(len(violations), 0, f"Found emoji in dashboard.js: {violations}")

    def test_zero_emoji_across_dashboard_css(self):
        violations = check_text(self.dashboard_css)
        self.assertEqual(len(violations), 0, f"Found emoji in dashboard.css: {violations}")


if __name__ == "__main__":
    unittest.main()
