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
        light_backgrounds = ("#F6F3EE", "#FFFFFF")
        light_foregrounds = {
            "text-primary": "#1B2330",
            "text-secondary": "#5B6472",
            "accent-primary": "#1F4E79",
            "status-fail": "#B42318",
            "status-warn": "#B54708",
            "status-pass": "#067647",
        }
        for bg in light_backgrounds:
            for name, fg in light_foregrounds.items():
                ratio = wcag_contrast_ratio(fg, bg)
                self.assertGreaterEqual(
                    ratio, 4.5, f"Light token {name} ({fg}) on {bg} has contrast {ratio:.2f} < 4.5:1"
                )

        dark_backgrounds = ("#12161C", "#1B212A")
        dark_foregrounds = {
            "text-primary": "#E8EBF0",
            "text-secondary": "#A3ACB9",
            "accent-primary": "#7FB2E5",
            "status-fail": "#F97066",
            "status-warn": "#FDB022",
            "status-pass": "#47CD89",
        }
        for bg in dark_backgrounds:
            for name, fg in dark_foregrounds.items():
                ratio = wcag_contrast_ratio(fg, bg)
                self.assertGreaterEqual(
                    ratio, 4.5, f"Dark token {name} ({fg}) on {bg} has contrast {ratio:.2f} < 4.5:1"
                )

    def test_02_css_cascade_layers_and_performance_hygiene(self):
        """dashboard.css uses @layer base, dashboard, studio, has zero transition:all and zero backdrop-filter."""
        self.assertIn("@layer base, dashboard, studio;", self.css_text)
        self.assertIn("@layer base {", self.css_text)
        self.assertIn("@layer dashboard {", self.css_text)
        self.assertIn("@layer studio {", self.css_text)
        self.assertIsNone(re.search(r"transition\s*:\s*all\b", self.css_text))
        self.assertNotIn("backdrop-filter:", self.css_text)
        self.assertNotIn("direction: ltr !important;", self.css_text)

        for token in (
            "#F6F3EE", "#12161C", "#FFFFFF", "#1B212A", "#1B2330", "#E8EBF0",
            "#5B6472", "#A3ACB9", "#1F4E79", "#7FB2E5", "#B42318", "#F97066",
            "#B54708", "#FDB022", "#067647", "#47CD89"
        ):
            self.assertIn(token, self.css_text, f"Missing design token {token} in dashboard.css")

    def test_03_competitor_brands_and_version_badges_removed(self):
        """Competitor names (Jobscan, Teal, Resume Worded) and 'סטודיו קריירה 3.0' are absent from HTML."""
        for forbidden in ("Jobscan", "Teal", "Resume Worded", "סטודיו קריירה 3.0"):
            self.assertNotIn(forbidden, self.html_text, f"Forbidden string '{forbidden}' found in index.html")
            self.assertNotIn(forbidden, self.docs_html_text, f"Forbidden string '{forbidden}' found in docs/index.html")

    def test_04_hidden_until_found_panels_not_suppressed_by_display_none(self):
        """studioModuleWriter and studioModuleInterview use hidden='until-found' without inline display:none."""
        for panel_id in ("studioModuleWriter", "studioModuleInterview"):
            panel = self.soup.find(id=panel_id)
            self.assertIsNotNone(panel)
            self.assertEqual(panel.get("hidden"), "until-found")
            style_attr = panel.get("style") or ""
            self.assertNotIn("display: none", style_attr)
        self.assertIn('[hidden]:not([hidden="until-found"])', self.css_text)

    def test_05_sticky_job_bar_horizontal_meter_and_stage_status_dom(self):
        """Top sticky bar, horizontal match progress bar, and stage status pills exist in DOM."""
        self.assertIsNotNone(self.soup.find("meta", attrs={"name": "color-scheme", "content": "light dark"}))
        self.assertIsNone(self.soup.find(id="themeToggleBtn"))
        self.assertIsNotNone(self.soup.find(id="studioStickyJobBar"))
        self.assertIsNotNone(self.soup.find(id="studioStickyMatchBar"))
        self.assertIsNotNone(self.soup.find(id="studioStickyMatchFill"))
        self.assertIsNotNone(self.soup.find(id="studioStickyMatchThreshold"))
        self.assertIsNotNone(self.soup.find(id="studioStageStatusAts"))
        self.assertIsNotNone(self.soup.find(id="studioStageStatusWriter"))
        self.assertIsNotNone(self.soup.find(id="studioStageStatusInterview"))
        self.assertIsNotNone(self.soup.find(id="atsSeveritySortedGapsCard"))
        self.assertIsNotNone(self.soup.find(id="atsSeveritySortedGapsList"))

    def test_06_js_theme_toggle_severity_gaps_and_tracked_bullet_suggestions(self):
        """JS functions for theme toggling, severity-sorted gaps, and tracked bullet diffs execute cleanly."""
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
          themeToggleIcon: {{ className: '' }},
          atsVerdictSummaryLine: {{ textContent: '' }},
          atsSeveritySortedGapsList: {{ innerHTML: '' }},
          studioStickyMatchValue: {{ textContent: '' }},
          studioStickyMatchBar: {{ attrs: {{}}, setAttribute: function(k,v){{ this.attrs[k]=v; }} }},
          studioStickyMatchFill: {{ style: {{ inlineSize: '0%' }}, classList: {{ remove: function(){{}}, add: function(){{}} }} }},
          studioStageStatusAts: {{ textContent: '', classList: {{ remove: function(){{}}, add: function(){{}} }} }},
          studioStageIssuesAts: {{ textContent: '' }},
          writerBulletAuditList: {{ innerHTML: '' }},
          writerAuditorSummaryBadge: {{ textContent: '' }}
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
        var report = window.runAtsJobMatching("דרוש תואר ראשון בהנדסת מכונות B.Sc וידע ב-Lean ו-BESS");
        window.renderSeveritySortedGaps(report, "דרוש תואר ראשון בהנדסת מכונות B.Sc וידע ב-Lean ו-BESS");
        window.updateStudioWorkbenchHeaderAndStages(report, "דרוש תואר ראשון בהנדסת מכונות B.Sc וידע ב-Lean ו-BESS");
        window.renderBulletImpactAuditor();
        print(JSON.stringify({{
          t1: t1,
          t2: t2,
          verdict: __dom.atsVerdictSummaryLine.textContent,
          hasInjectBtn: __dom.atsSeveritySortedGapsList.innerHTML.includes("הוסף לקו״ח"),
          stageAts: __dom.studioStageStatusAts.textContent,
          hasTrackedAccept: __dom.writerBulletAuditList.innerHTML.includes("acceptTrackedBulletSuggestion")
        }}));
        """
        proc = run_js(harness)
        self.assertEqual(proc.returncode, 0, f"JS failed: {proc.stderr}\n{proc.stdout}")
        res = json.loads(proc.stdout.strip())
        self.assertEqual(res["t1"], "dark")
        self.assertEqual(res["t2"], "dark")
        self.assertIn("B.Sc", res["verdict"])
        self.assertTrue(res["hasInjectBtn"])
        self.assertEqual(res["stageAts"], "חסום")
        self.assertTrue(res["hasTrackedAccept"])


if __name__ == "__main__":
    unittest.main()
