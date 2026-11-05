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
        pairs = [
            ("frontend/js/dashboard.js", "docs/dashboard.js"),
            ("frontend/css/dashboard.css", "docs/dashboard.css"),
            ("frontend/js/app.js", "docs/js/app.js"),
            ("frontend/data/cv/cv_he.html", "docs/career/cv/cv_he.html"),
            ("frontend/data/cv/cv_en.html", "docs/career/cv/cv_en.html"),
        ]
        modules_dir = ROOT / "frontend/js/modules"
        if modules_dir.exists():
            for mod_file in modules_dir.glob("*.js"):
                rel_src = f"frontend/js/modules/{mod_file.name}"
                rel_dst = f"docs/js/modules/{mod_file.name}"
                pairs.append((rel_src, rel_dst))

        for rel_src, rel_dst in pairs:
            src_p = ROOT / rel_src
            dst_p = ROOT / rel_dst
            if src_p.exists() or dst_p.exists():
                self.assertTrue(src_p.exists(), f"Source must exist: {rel_src}")
                self.assertTrue(dst_p.exists(), f"Destination must exist: {rel_dst}")
                self.assertEqual(src_p.read_bytes(), dst_p.read_bytes(), f"Drift detected between {rel_src} and {rel_dst}")


if __name__ == "__main__":
    unittest.main()
