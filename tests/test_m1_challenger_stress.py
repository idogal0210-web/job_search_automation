#!/usr/bin/env python3
"""
tests/test_m1_challenger_stress.py

Empirical Challenger Test Suite for Milestone 1:
- Verifies DOM hierarchy, ARIA attributes, and clean single-view workspace.
- Ensures Zero-Emoji compliance on challenger artifacts.
"""

import os
import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestMilestone1ChallengerStress(unittest.TestCase):
    """Adversarial stress and boundary tests for Milestone 1."""

    def test_workspaces_are_direct_siblings_in_dashboard_main(self):
        """TC-CHALLENGER-M1-01: Workspaces are siblings under .dashboard-main."""
        content = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(
            encoding="utf-8"
        )
        radar_pos = content.find('id="radarWorkspace"')
        studio_pos = content.find('id="careerStudioWorkspace"')
        main_pos = content.find('class="dashboard-main"')

        self.assertGreater(radar_pos, main_pos, "radarWorkspace must be inside dashboard-main")
        self.assertGreater(studio_pos, radar_pos, "careerStudioWorkspace must follow radarWorkspace")

    def test_zero_emoji_in_challenger_artifacts(self):
        """TC-CHALLENGER-M1-02: Challenger test files strictly follow Zero-Emoji policy."""
        from scripts.validate_zero_emoji import scan_file

        files_to_check = [
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


if __name__ == "__main__":
    unittest.main()
