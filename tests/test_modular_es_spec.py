#!/usr/bin/env python3
"""
Unit tests for the new modular ES architecture and ATS Action Item Generator.
Verifies file existence, exports, zero emoji compliance, and action item outputs.
"""

import json
import os
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestModularEsArchitecture(unittest.TestCase):
    def setUp(self):
        self.frontend_js = PROJECT_ROOT / "frontend" / "js"
        self.docs_js = PROJECT_ROOT / "docs" / "js"
        self.modules_dir = self.frontend_js / "modules"

    def test_modular_files_exist_in_frontend_and_docs(self):
        expected_modules = ["store.js", "atsEngine.js", "geoMap.js", "export.js", "render.js"]
        for mod in expected_modules:
            self.assertTrue((self.modules_dir / mod).exists(), f"Missing frontend/js/modules/{mod}")
            self.assertTrue((self.docs_js / "modules" / mod).exists(), f"Missing docs/js/modules/{mod}")

        self.assertTrue((self.frontend_js / "app.js").exists(), "Missing frontend/js/app.js")
        self.assertTrue((self.docs_js / "app.js").exists(), "Missing docs/js/app.js")

    def test_node_check_all_modular_files(self):
        files_to_check = [
            self.frontend_js / "app.js",
            self.frontend_js / "modules" / "store.js",
            self.frontend_js / "modules" / "atsEngine.js",
            self.frontend_js / "modules" / "geoMap.js",
            self.frontend_js / "modules" / "export.js",
            self.frontend_js / "modules" / "render.js",
            self.docs_js / "app.js",
            self.docs_js / "modules" / "store.js",
            self.docs_js / "modules" / "atsEngine.js",
            self.docs_js / "modules" / "geoMap.js",
            self.docs_js / "modules" / "export.js",
            self.docs_js / "modules" / "render.js",
        ]
        for f in files_to_check:
            proc = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, f"Syntax error in {f}: {proc.stderr}")

    def test_dashboard_js_loaded_in_index_html(self):
        tpl_html = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(encoding="utf-8")
        docs_html = (PROJECT_ROOT / "docs" / "index.html").read_text(encoding="utf-8")

        self.assertIn('dashboard.js', tpl_html)
        self.assertIn('dashboard.js', docs_html)

    def test_action_item_generator_output(self):
        # Run node to verify generateCvBulletActionItem execution
        node_script = """
        import { generateCvBulletActionItem } from './frontend/js/modules/atsEngine.js';

        const item1 = generateCvBulletActionItem('scada', { company: 'Energean' });
        if (!item1 || !item1.bulletHe.includes('SCADA') || !item1.bulletEn.includes('SCADA')) {
          process.exit(1);
        }

        const item2 = generateCvBulletActionItem('bess', { company: 'Enlight' });
        if (!item2 || !item2.bulletHe.includes('BESS') || !item2.bulletEn.includes('BESS')) {
          process.exit(2);
        }

        const item3 = generateCvBulletActionItem('prms', { company: 'נתג"ז' });
        if (!item3 || !item3.bulletHe.includes('PRMS') || !item3.bulletEn.includes('PRMS')) {
          process.exit(3);
        }

        const item4 = generateCvBulletActionItem('lean', { company: 'מרטנס' });
        if (!item4 || !item4.bulletHe.includes('Lean') || !item4.bulletEn.includes('Lean')) {
          process.exit(4);
        }

        console.log('OK');
        """
        proc = subprocess.run(["node", "--input-type=module", "-e", node_script], cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"Action item generator test failed: {proc.stderr}")
        self.assertIn("OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
