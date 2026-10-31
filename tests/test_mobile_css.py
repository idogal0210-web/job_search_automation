import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS_PATHS = [ROOT / "frontend/css/dashboard.css", ROOT / "docs/dashboard.css"]


class MobileCssPhaseATests(unittest.TestCase):
    def setUp(self):
        self.css = CSS_PATHS[0].read_text(encoding="utf-8")

    def test_frontend_and_docs_css_identical(self):
        self.assertEqual(CSS_PATHS[0].read_bytes(), CSS_PATHS[1].read_bytes())

    def test_all_hover_rules_gated_behind_hover_media(self):
        css = self.css
        for match in re.finditer(r":hover", css):
            start = css.rfind("@media (hover: hover)", 0, match.start())
            self.assertNotEqual(start, -1, "ungated :hover near %d" % match.start())
            segment = css[start:match.start()]
            self.assertGreater(segment.count("{"), segment.count("}"))

    def test_mobile_input_font_size_prevents_ios_zoom(self):
        self.assertRegex(self.css, r"font-size:\s*max\(16px,\s*1em\)\s*!important")

    def test_safe_area_and_dvh_present(self):
        for token in (
            "safe-area-inset-top",
            "safe-area-inset-bottom",
            "@supports (height: 100dvh)",
            "overscroll-behavior: contain",
            "prefers-reduced-motion",
        ):
            self.assertIn(token, self.css)


if __name__ == "__main__":
    unittest.main()
