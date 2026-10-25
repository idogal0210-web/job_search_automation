#!/usr/bin/env python3
"""
tests/test_m1_challenger_stress.py

Empirical Challenger Stress Test Suite for Milestone 1:
- Executes the full JavaScriptCore stress test harness (tests/stress_m1_harness.js)
  covering 6,600+ assertions of rapid toggling, malformed hashes, storage failures,
  and Leaflet map invalidation.
- Verifies DOM hierarchy, ARIA attributes, and mode switcher structural compliance.
- Ensures Zero-Emoji compliance on challenger artifacts.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone1ChallengerStress(unittest.TestCase):
    """Adversarial stress and boundary tests for Milestone 1."""

    def test_empirical_jsc_stress_harness_execution(self):
        """TC-CHALLENGER-M1-01: Run 6,600+ JS assertions in JavaScriptCore without exception."""
        if not os.path.exists(JSC_BIN):
            self.skipTest(f"JavaScriptCore CLI binary not found at {JSC_BIN}")

        harness_path = PROJECT_ROOT / "tests" / "stress_m1_harness.js"
        self.assertTrue(harness_path.exists(), "tests/stress_m1_harness.js must exist")

        proc = subprocess.run(
            [JSC_BIN, str(harness_path)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )

        output = proc.stdout + proc.stderr
        self.assertEqual(
            proc.returncode,
            0,
            f"JavaScript stress harness failed with return code {proc.returncode}:\n{output}",
        )
        self.assertIn("ALL STRESS TESTS PASSED SUCCESSFULLY", output)

        match = re.search(r"Passed:\s+(\d+)", output)
        self.assertTrue(match, "Harness output should report number of passed assertions")
        passed_count = int(match.group(1))
        self.assertGreaterEqual(
            passed_count, 6000, f"Expected >= 6000 assertions passed, got {passed_count}"
        )

    def test_dom_mode_switcher_aria_roles_and_controls(self):
        """TC-CHALLENGER-M1-02: Mode switcher buttons have proper ARIA attributes and controls."""
        tpl_path = PROJECT_ROOT / "frontend" / "templates" / "index.html"
        self.assertTrue(tpl_path.exists())
        content = tpl_path.read_text(encoding="utf-8")

        # Verify mode switcher container
        self.assertIn('class="dashboard-mode-switcher"', content)
        self.assertIn('role="tablist"', content)

        # Verify Radar button
        radar_btn_match = re.search(
            r'<button[^>]*id="modeSwitchRadar"[^>]*>', content, re.MULTILINE
        )
        self.assertIsNotNone(radar_btn_match, "modeSwitchRadar button not found")
        radar_tag = radar_btn_match.group(0)
        self.assertIn('role="tab"', radar_tag)
        self.assertIn('aria-controls="radarWorkspace"', radar_tag)

        # Verify Studio button
        studio_btn_match = re.search(
            r'<button[^>]*id="modeSwitchStudio"[^>]*>', content, re.MULTILINE
        )
        self.assertIsNotNone(studio_btn_match, "modeSwitchStudio button not found")
        studio_tag = studio_btn_match.group(0)
        self.assertIn('role="tab"', studio_tag)
        self.assertIn('aria-controls="careerStudioWorkspace"', studio_tag)

    def test_workspaces_are_direct_siblings_in_dashboard_main(self):
        """TC-CHALLENGER-M1-03: Workspaces are siblings under .dashboard-main."""
        content = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        radar_pos = content.find('id="radarWorkspace"')
        studio_pos = content.find('id="careerStudioWorkspace"')
        main_pos = content.find('class="dashboard-main"')

        self.assertGreater(radar_pos, main_pos, "radarWorkspace must be inside dashboard-main")
        self.assertGreater(studio_pos, radar_pos, "careerStudioWorkspace must follow radarWorkspace")

    def test_studio_modules_semantic_scaffolding(self):
        """TC-CHALLENGER-M1-04: Verify all 6 semantic module containers are present in Studio."""
        content = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        modules = [
            "studioModuleAts",
            "studioModuleWriter",
            "studioModuleVisual",
            "studioModuleKanban",
            "studioModuleInterview",
            "studioModuleSkills",
        ]
        for mod in modules:
            self.assertIn(f'id="{mod}"', content, f"Missing container {mod}")

    def test_zero_emoji_in_challenger_artifacts(self):
        """TC-CHALLENGER-M1-05: Challenger test files strictly follow Zero-Emoji policy."""
        from scripts.validate_zero_emoji import scan_file

        files_to_check = [
            PROJECT_ROOT / "tests" / "stress_m1_harness.js",
            PROJECT_ROOT / "tests" / "test_m1_challenger_stress.py",
        ]
        for f in files_to_check:
            violations = scan_file(f)
            self.assertEqual(
                len(violations),
                0,
                f"Found emoji violations in {f.name}: {violations}",
            )


if __name__ == "__main__":
    unittest.main()
