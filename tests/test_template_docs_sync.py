import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TemplateDocsSyncTests(unittest.TestCase):
    """The pipeline regenerates docs/index.html from the template.

    Any HTML edit made only in docs/index.html would be silently lost on the
    next build, so the two must differ only by build-time placeholder values.
    """

    def test_docs_index_matches_template_except_placeholders(self):
        template = (ROOT / "frontend/templates/index.html").read_text(encoding="utf-8")
        docs = (ROOT / "docs/index.html").read_text(encoding="utf-8")
        pattern = re.escape(template)
        pattern = re.sub(r"__[A-Z_]+__", "(.*?)", pattern.replace("\\_", "_"))
        self.assertIsNotNone(
            re.fullmatch(pattern, docs, re.S),
            "docs/index.html drifted from frontend/templates/index.html",
        )

    def test_js_and_css_copies_identical(self):
        for rel_src, rel_dst in (
            ("frontend/js/dashboard.js", "docs/dashboard.js"),
            ("frontend/css/dashboard.css", "docs/dashboard.css"),
        ):
            self.assertEqual((ROOT / rel_src).read_bytes(), (ROOT / rel_dst).read_bytes(), rel_dst)


if __name__ == "__main__":
    unittest.main()
