# -*- coding: utf-8 -*-
"""
Specification and E2E Tests for Career Studio Milestones 4, 5, and 6:
- Milestone 4/5: CV files and Multi-Version CV Hub (visual simulator and Kanban removed)
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
    # Removed modules, CV hub inside writer stage, numbered step flow
    # -------------------------------------------------------------------------
    def test_removed_visual_and_kanban_modules_absent(self):
        for ident in ("studioModuleVisual", "studioTabVisual", "studioModuleKanban",
                      "studioTabKanban", "addKanbanModal", "heatmapOverlayLayer"):
            self.assertIsNone(self.soup.find(id=ident), ident)
        for token in ("initVisualModule", "initKanbanModule", "toggleHeatmapOverlay",
                      "applyA4AutoFit", "moveKanbanCard"):
            self.assertNotIn(token, self.dashboard_js)
        for token in ("kanban-", "heatmap-", "visual-toolbar"):
            self.assertNotIn(token, self.dashboard_css)

    def test_studio_has_exactly_three_core_tools(self):
        tabs = [t for t in self.soup.find_all(id=True) if t["id"].startswith("studioTab")]
        self.assertEqual(len(tabs), 3)
        badge_nums = [int(t.find(class_="step-num-badge").get_text().strip()) for t in tabs]
        self.assertEqual(badge_nums, [1, 2, 3])
        panels = [t for t in self.soup.find_all("section", id=True) if t["id"].startswith("studioModule")]
        self.assertEqual(len(panels), 3)
        self.assertIsNone(self.soup.find(id="studioModuleSkills"))

    def test_a11y_main_landmark_h1_and_live_job_check_exposed(self):
        mains = self.soup.find_all("main")
        self.assertEqual(len(mains), 1, "Document must have exactly one <main> landmark")
        self.assertIn("dashboard-main", mains[0].get("class", []))
        h1s = self.soup.find_all("h1")
        self.assertEqual(len(h1s), 1, "Document must have a top-level <h1>")
        self.assertIn("function runLiveJobCheck", self.dashboard_js)
        self.assertIn("function computeInactiveState", self.dashboard_js)
        self.assertIn("window.runLiveJobCheck =", self.dashboard_js)

    def test_studio_v3_flat_architecture_without_nested_step_outlines(self):
        self.assertIsNone(self.soup.find(class_="studio-step-outline"))
        self.assertIsNone(self.soup.find(class_="studio-pipeline-sidebar"))
        self.assertIsNotNone(self.soup.find(class_="studio-context-bar"))
        self.assertIsNotNone(self.soup.find(id="atsStep1Panel"))
        self.assertIsNotNone(self.soup.find(id="studioJobDetailsAccordion"))

    def test_m4_04_cv_html_files_exist_in_frontend_and_docs(self):
        required_files = [
            "cv_he.html",
            "cv_en.html"
        ]
        removed_files = [
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
        for old_name in removed_files:
            self.assertFalse(os.path.exists(os.path.join(CV_DIR, old_name)))
            self.assertFalse(os.path.exists(os.path.join(DOCS_CV_DIR, old_name)))

    def test_m5_04_cv_hub_cards_exist_inside_writer_step(self):
        writer = self.soup.find(id="studioModuleWriter")
        self.assertIsNotNone(writer)
        cards = writer.find_all(class_="cv-hub-card")
        self.assertEqual(len(cards), 2, "Must have exactly 2 updated CV cards (HE and EN) in Hub")
        titles = [c.find(class_="cv-hub-title").get_text() for c in cards]
        self.assertTrue(any("בקרת גז טבעי" in t for t in titles))
        self.assertTrue(any("Practical Mechanical Engineer" in t for t in titles))


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

    def test_m6_04_linkedin_seo_optimizer_elements_exist(self):
        self.assertIsNotNone(self.soup.find(id="linkedinSeoScoreBadge"))
        self.assertIsNotNone(self.soup.find(id="linkedinHeadlineOutput"))
        self.assertIsNotNone(self.soup.find(id="btnCopyLinkedInHeadline"))
        self.assertIsNotNone(self.soup.find(id="linkedinAboutOutput"))
        self.assertIsNotNone(self.soup.find(id="linkedinSkillsChips"))

    def test_m6_05_bullet_impact_auditor_and_job_bridge_exist(self):
        self.assertIsNotNone(self.soup.find(id="writerBulletAuditList"))
        self.assertIn("function openJobInCareerStudio", self.dashboard_js)
        self.assertIn("function injectKeywordToWriter", self.dashboard_js)
        self.assertIn("function renderBulletImpactAuditor", self.dashboard_js)
        self.assertIn("function renderLinkedInOptimizer", self.dashboard_js)

    def test_m6_06_role_fit_interview_category_exists(self):
        self.assertIn("role_fit:", self.dashboard_js)
        self.assertIn("setInterviewCategory('role_fit'", self.template_html)

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
