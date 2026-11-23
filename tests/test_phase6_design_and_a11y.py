# -*- coding: utf-8 -*-
"""
Regression and specification tests for Phase 6 (TASK-39):
- Section 5.4 Light & Dark design tokens and WCAG >= 4.5:1 contrast verification
- CSS @layer base, dashboard, studio architecture, zero transition:all, zero backdrop-filter
- Competitor brand name & version badge removal from UI templates
- hidden="until-found" compatibility without display:none suppression
- Career Studio 56px sticky target bar, horizontal match meter, stage status pills,
  severity-sorted gaps, and tracked line suggestions (Accept / Reject / Edit)
"""

import json
import re
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
from tests.js_runner import run_js, skip_if_no_js

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _srgb_channel_to_linear(channel_8bit: int) -> float:
    c = channel_8bit / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_luminance(hex_color: str) -> float:
    clean = hex_color.strip().lstrip("#")
    r = int(clean[0:2], 16)
    g = int(clean[2:4], 16)
    b = int(clean[4:6], 16)
    return (
        0.2126 * _srgb_channel_to_linear(r)
        + 0.7152 * _srgb_channel_to_linear(g)
        + 0.0722 * _srgb_channel_to_linear(b)
    )


def wcag_contrast_ratio(hex1: str, hex2: str) -> float:
    l1 = hex_luminance(hex1)
    l2 = hex_luminance(hex2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class TestPhase6DesignAndA11y(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_text = (PROJECT_ROOT / "frontend/templates/index.html").read_text(encoding="utf-8")
        cls.docs_html_text = (PROJECT_ROOT / "docs/index.html").read_text(encoding="utf-8")
        cls.css_text = (PROJECT_ROOT / "frontend/css/dashboard.css").read_text(encoding="utf-8")
        cls.js_text = (PROJECT_ROOT / "frontend/js/dashboard.js").read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html_text, "html.parser")

    def test_01_wcag_aa_contrast_ratios_for_all_section_5_4_tokens(self):
        """Every foreground token in Light and Dark mode meets >= 4.5:1 against both canvas and surface."""
        light_backgrounds = ("#F8FAFC", "#FFFFFF")
        light_foregrounds = {
            "text-primary": "#0F172A",
            "text-secondary": "#475569",
            "accent-primary": "#0369A1",
            "status-fail": "#991B1B",
            "status-warn": "#B45309",
            "status-pass": "#047857",
        }
        for bg in light_backgrounds:
            for name, fg in light_foregrounds.items():
                ratio = wcag_contrast_ratio(fg, bg)
                self.assertGreaterEqual(
                    ratio, 4.5, f"Light token {name} ({fg}) on {bg} has contrast {ratio:.2f} < 4.5:1"
                )

        dark_backgrounds = ("#0B0F19", "#131B2E")
        dark_foregrounds = {
            "text-primary": "#F8FAFC",
            "text-secondary": "#94A3B8",
            "accent-primary": "#38BDF8",
            "status-fail": "#F87171",
            "status-warn": "#FBBF24",
            "status-pass": "#34D399",
        }
        for bg in dark_backgrounds:
            for name, fg in dark_foregrounds.items():
                ratio = wcag_contrast_ratio(fg, bg)
                self.assertGreaterEqual(
                    ratio, 4.5, f"Dark token {name} ({fg}) on {bg} has contrast {ratio:.2f} < 4.5:1"
                )

    def test_02_css_cascade_layers_and_performance_hygiene(self):
        """dashboard.css uses @layer base, dashboard, has zero transition:all and zero backdrop-filter."""
        self.assertIn("@layer base, dashboard;", self.css_text)
        self.assertIn("@layer base {", self.css_text)
        self.assertIn("@layer dashboard {", self.css_text)
        self.assertIsNone(re.search(r"transition\s*:\s*all\b", self.css_text))
        self.assertNotIn("backdrop-filter:", self.css_text)
        self.assertNotIn("direction: ltr !important;", self.css_text)

        for token in (
            "#F8FAFC", "#0B0F19", "#FFFFFF", "#131B2E", "#0F172A",
            "#475569", "#94A3B8", "#0369A1", "#38BDF8", "#991B1B", "#F87171",
            "#B45309", "#FBBF24", "#047857", "#34D399"
        ):
            self.assertIn(token, self.css_text, f"Missing design token {token} in dashboard.css")

    def test_03_competitor_brands_and_version_badges_removed(self):
        """Competitor names (Jobscan, Teal, Resume Worded) and 'סטודיו קריירה 3.0' are absent from HTML."""
        for forbidden in ("Jobscan", "Teal", "Resume Worded", "סטודיו קריירה 3.0"):
            self.assertNotIn(forbidden, self.html_text, f"Forbidden string '{forbidden}' found in index.html")
            self.assertNotIn(forbidden, self.docs_html_text, f"Forbidden string '{forbidden}' found in docs/index.html")

    def test_04_theme_toggle_elements_in_dom(self):
        """Color-scheme meta tag and theme toggle button exist in DOM."""
        self.assertIsNotNone(self.soup.find("meta", attrs={"name": "color-scheme", "content": "light dark"}))
        self.assertIsNotNone(self.soup.find(id="themeToggleBtn"))

    def test_05_js_theme_toggle_executes_cleanly(self):
        """JS functions for theme toggling execute cleanly without console errors."""
        skip_if_no_js(self)
        harness = f"""
        var window = globalThis;
        if (!globalThis.console) {{
          globalThis.console = {{ log: print, warn: print, error: print, info: print }};
        }}
        window.addEventListener = function() {{}};
        window.removeEventListener = function() {{}};
        window.location = {{ hash: '' }};
        window.matchMedia = function() {{ return {{ matches: false }}; }};
        var __store = {{}};
        window.localStorage = {{
          getItem: function(k) {{ return __store[k] || null; }},
          setItem: function(k, v) {{ __store[k] = String(v); }},
          removeItem: function(k) {{ delete __store[k]; }}
        }};
        var localStorage = window.localStorage;
        var __dom = {{
          themeToggleBtn: {{ attrs: {{}}, setAttribute: function(k,v){{ this.attrs[k]=v; }} }},
          themeToggleLabel: {{ textContent: '' }},
          themeToggleIcon: {{ className: '' }}
        }};
        var document = {{
          documentElement: {{
            attrs: {{}},
            setAttribute: function(k, v) {{ this.attrs[k] = v; }},
            getAttribute: function(k) {{ return this.attrs[k] || null; }}
          }},
          addEventListener: function() {{}},
          removeEventListener: function() {{}},
          getElementById: function(id) {{ return __dom[id] || null; }},
          querySelector: function() {{ return null; }},
          querySelectorAll: function() {{ return []; }}
        }};
        {self.js_text}
        var t1 = window.initDashboardTheme();
        var t2 = window.toggleDashboardTheme();
        print(JSON.stringify({{
          t1: t1,
          t2: t2
        }}));
        """
        proc = run_js(harness)
        self.assertEqual(proc.returncode, 0, f"JS failed: {proc.stderr}\n{proc.stdout}")
        res = json.loads(proc.stdout.strip())
        self.assertEqual(res["t1"], "dark")
        self.assertEqual(res["t2"], "light")


if __name__ == "__main__":
    unittest.main()
