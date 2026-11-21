"""
tests/test_cv_tailor.py

Unit tests for the integrated CV Tailoring Engine (tools/cv_tailor).
Tests base profile loading, fallback handling, keyword taxonomy, and module integrity.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
CV_TAILOR_DIR = os.path.join(REPO_ROOT, "tools", "cv_tailor")
if CV_TAILOR_DIR not in sys.path:
    sys.path.insert(0, CV_TAILOR_DIR)

from tools.cv_tailor.src.utils import load_base_profile, load_config
from tools.cv_tailor.src.keywords import extract_keywords, tokenize


class TestCVTailorIntegration(unittest.TestCase):
    """Test suite for unified CV Tailor engine."""

    def test_load_base_profile_or_template(self):
        """Ensure base profile or template fallback loads successfully with non-empty content."""
        content = load_base_profile()
        self.assertIsInstance(content, str)
        self.assertGreater(len(content), 100)
        self.assertIn("פרופיל בסיס", content)

    def test_load_config_defaults(self):
        """Ensure default configuration loads correct output directory."""
        config = load_config()
        self.assertIn("output_dir", config)
        self.assertTrue(config["output_dir"].endswith("output"))

    def test_keyword_matching(self):
        """Ensure domain keyword extraction extracts relevant terms correctly."""
        sample_text = "דרוש בקר גז עם ניסיון במערכות SCADA, בקרת לחצים ו-Bifacial PV."
        keywords = extract_keywords(sample_text, top_n=5)
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)

    def test_modules_importability(self):
        """Ensure analyzer, generator, researcher, and scraper import cleanly."""
        from tools.cv_tailor.src.analyzer import ATSAnalysis, AtsCategorizedGap
        from tools.cv_tailor.src.generator import TailoredPackage
        from tools.cv_tailor.src.scraper import JobPosting

        posting = JobPosting(
            url="https://example.com/job/1",
            title="בקר גז",
            company="חברת אנרגיה",
            location="תל אביב",
            raw_text="תיאור משרה מלא",
            description="תיאור תפקיד",
            requirements="הנדסאי מכונות"
        )
        self.assertEqual(posting.title, "בקר גז")
        self.assertEqual(posting.company, "חברת אנרגיה")

        gap = AtsCategorizedGap(
            requirement="רישיון חשמלאי מוסמך פעיל",
            severity="blocking",
            explanation="המועמד בלימודים פעילים",
            bridgeable=False,
            bridge_strategy="שקיפות מלאה"
        )
        analysis = ATSAnalysis(
            overall_score=85,
            match_summary="התאמה טובה",
            scorecard={"השכלה": 90},
            matched_keywords=["SCADA"],
            missing_keywords=["BESS"],
            key_strengths=["הנדסאי מכונות"],
            clarification_questions=[],
            recommended_changes=[],
            unmatched_requirements=["חשמלאי מוסמך"],
            categorized_gaps=[gap.__dict__],
        )
        self.assertEqual(len(analysis.categorized_gaps), 1)
        self.assertEqual(analysis.categorized_gaps[0]["severity"], "blocking")

    def test_ats_schema_categorized_gaps_validation(self):
        """Ensure AtsStudioAnalysisSchema in src.gemini_runtime accepts categorized_gaps."""
        from tools.cv_tailor.src.utils import get_gemini_runtime_module
        runtime = get_gemini_runtime_module()
        AtsStudioAnalysisSchema = runtime.AtsStudioAnalysisSchema
        AtsCategorizedGap = runtime.AtsCategorizedGap

        schema_inst = AtsStudioAnalysisSchema(
            overall_score=85,
            match_summary="התאמה טובה",
            categorized_gaps=[
                AtsCategorizedGap(
                    requirement="רישיון חשמלאי מוסמך",
                    severity="blocking",
                    explanation="בלימודים פעילים",
                    bridgeable=False,
                    bridge_strategy="שקיפות"
                ),
                AtsCategorizedGap(
                    requirement="ניסיון ניהול קבלנים",
                    severity="important",
                    explanation="ניסיון תפעולי במקום בינוי",
                    bridgeable=True,
                    bridge_strategy="הבלטת ממשקים מסחריים ופיקוד בסיירת נח\"ל"
                )
            ]
        )
        dump = schema_inst.model_dump()
        self.assertEqual(len(dump["categorized_gaps"]), 2)
        self.assertEqual(dump["categorized_gaps"][0]["severity"], "blocking")
        self.assertEqual(dump["categorized_gaps"][1]["severity"], "important")

    def test_prompts_junior_pm_and_gap_severity_rules(self):
        """Ensure prompt templates include Junior PM instructions and 3-tier gap categorization."""
        from tools.cv_tailor.src.utils import load_prompt_template

        analysis_prompt = load_prompt_template("cv_analysis_v1.txt")
        self.assertIn("categorized_gaps", analysis_prompt)
        self.assertIn("blocking", analysis_prompt)
        self.assertIn("important", analysis_prompt)
        self.assertIn("nice_to_have", analysis_prompt)

        gen_prompt = load_prompt_template("cv_generation_v1.txt")
        self.assertIn("lang_instruction", gen_prompt)
        self.assertIn("Junior Project Manager", gen_prompt)
        self.assertIn("Coordinator", gen_prompt)
        self.assertIn("סיירת נח״ל", gen_prompt)


if __name__ == "__main__":
    unittest.main()
