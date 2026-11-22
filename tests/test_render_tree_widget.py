#!/usr/bin/env python3
"""
test_render_tree_widget.py
Unit tests for scripts/render_tree_widget.py.
Verifies git status parsing, tree data extraction, HTML generation, and error resilience.
Strictly zero emojis.
"""

import tempfile
import unittest
from pathlib import Path

from scripts.render_tree_widget import (
    build_tree_data,
    generate_html_widget,
    get_git_status,
)


class TestRenderTreeWidget(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.root_path = Path(self.test_dir.name)

        # Create mock file structure
        (self.root_path / "src").mkdir()
        (self.root_path / "src" / "app.py").write_text("print('test')", encoding="utf-8")
        (self.root_path / "docs").mkdir()
        (self.root_path / "docs" / "index.html").write_text("<h1>test</h1>", encoding="utf-8")
        (self.root_path / "README.md").write_text("# Readme", encoding="utf-8")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_build_tree_data(self):
        data = build_tree_data(self.root_path, max_depth=2)
        self.assertTrue(data["is_dir"])
        names = [c["name"] for c in data["children"]]
        self.assertIn("src", names)
        self.assertIn("docs", names)
        self.assertIn("README.md", names)

    def test_generate_html_widget(self):
        tree_data = build_tree_data(self.root_path, max_depth=2)
        status_map = {"src/app.py": "modified", "README.md": "new"}
        html_out = generate_html_widget(
            tree_data=tree_data,
            status_map=status_map,
            mod_count=1,
            add_count=1,
            del_count=0,
            task_title="Test Task Title",
        )
        self.assertIn("Test Task Title", html_out)
        self.assertIn("badge-modified", html_out)
        self.assertIn("badge-new", html_out)
        self.assertIn("tailwindcss.min.js", html_out)
        self.assertIn('dir="rtl"', html_out)

    def test_git_status_fallback(self):
        status_map, mod_count, add_count, del_count = get_git_status(self.root_path)
        self.assertIsInstance(status_map, dict)
        self.assertIsInstance(mod_count, int)
        self.assertIsInstance(add_count, int)
        self.assertIsInstance(del_count, int)


if __name__ == "__main__":
    unittest.main()
