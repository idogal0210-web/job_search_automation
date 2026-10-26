"""
tests/test_cv_tailor.py

Unit tests for the integrated CV Tailoring Engine (tools/cv_tailor).
Tests base profile loading, fallback handling, keyword taxonomy, and module integrity.
"""

import os
import sys
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        from tools.cv_tailor.src.analyzer import ATSAnalysis
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


if __name__ == "__main__":
    unittest.main()
