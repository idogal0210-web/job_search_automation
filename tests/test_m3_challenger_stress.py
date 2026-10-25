#!/usr/bin/env python3
"""
tests/test_m3_challenger_stress.py

Empirical Challenger Stress Test Suite for Milestone 3: AI Writer & Tone Switcher Engine
Role: Milestone 3 Transformation & Formula Stress Challenger (challenger_m3_1)

Validates:
1. Extreme Inputs & Boundary Conditions:
   - Empty string and whitespace-only inputs (returns empty string gracefully, no exception).
   - Single word (Hebrew and English).
   - Long paragraph (3,000+ characters).
   - Special punctuation, symbols, and SQL/code injection strings.
   - HTML injection and script tags (<script>, <img>, <b>).
   - English bullets (passive, active, technical).
   - Hebrew bullets (passive, active, technical).
2. Core Invariants:
   - For every text-bearing input, the returned string is non-empty.
   - For every text-bearing input, the returned string starts with an active action verb.
   - For every text-bearing input, the returned string contains industrial domain context.
3. Rapid Mode Switching Stress:
   - 120+ simulated inputs rapidly switching between Technical, Operational, and Strategic modes.
4. Exception Freedom:
   - Zero uncaught JavaScript exceptions across all test runs in JavaScriptCore.
5. Zero-Emoji Compliance:
   - Strictly 0 emojis in all test code and generated artifacts.
"""

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone3ChallengerStress(unittest.TestCase):
    """Adversarial stress and boundary tests for Milestone 3 Bullet Transformation Engine."""

    @classmethod
    def setUpClass(cls):
        cls.js_file = PROJECT_ROOT / "frontend" / "js" / "dashboard.js"
        if not cls.js_file.exists():
            raise FileNotFoundError(f"dashboard.js not found at {cls.js_file}")

    def run_jsc_script(self, script_code: str) -> str:
        """Helper to run JavaScript code inside JSC with dashboard.js loaded."""
        dom_setup = """
        var window = globalThis;
        if (!globalThis.console) {
          globalThis.console = { log: print, warn: print, error: print, info: print };
        }
        window.addEventListener = function() {};
        window.removeEventListener = function() {};
        window.location = { hash: '#studio' };
        window.localStorage = {
          getItem: function() { return null; },
          setItem: function() {},
          removeItem: function() {}
        };
        var localStorage = window.localStorage;
        var document = {
          addEventListener: function() {},
          removeEventListener: function() {},
          getElementById: function(id) { return null; },
          querySelector: function(sel) { return null; },
          querySelectorAll: function(sel) { return []; }
        };
        """
        with open(self.js_file, "r", encoding="utf-8") as f:
            js_src = f.read()

        runner = dom_setup + "\n" + js_src + "\n" + script_code
        proc = subprocess.run(
            [JSC_BIN, "-e", runner],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"JSC Execution Failed (code {proc.returncode}):\n{proc.stderr}\nOutput:\n{proc.stdout}")
        return proc.stdout.strip()

    # --- 1. Extreme & Boundary Inputs ---

    def test_stress_01_empty_and_whitespace_inputs(self):
        """TC-STRESS-01: Empty string, whitespace, and tabs return empty string without exceptions."""
        out = self.run_jsc_script("""
            var inputs = ["", "   ", "\\t\\n  \\r", "     "];
            var modes = ["technical", "operational", "strategic"];
            var res = [];
            inputs.forEach(function(inp) {
                modes.forEach(function(m) {
                    var r = window.transformBulletTone(inp, m);
                    res.push({ inp: inp, mode: m, out: r, len: r.length });
                });
            });
            print(JSON.stringify(res));
        """)
        results = json.loads(out)
        self.assertEqual(len(results), 12)
        for r in results:
            self.assertEqual(r["out"], "", f"Expected empty string for input {r['inp']!r} in mode {r['mode']}")
            self.assertEqual(r["len"], 0)

    def test_stress_02_single_word_inputs(self):
        """TC-STRESS-02: Single word inputs in Hebrew and English yield non-empty, active verb outputs."""
        out = self.run_jsc_script("""
            var inputs = ["משמרות", "נומינציות", "גז", "סולארי", "pumps", "turbines", "scada", "operations"];
            var modes = ["technical", "operational", "strategic"];
            var res = [];
            inputs.forEach(function(inp) {
                modes.forEach(function(m) {
                    var r = window.transformBulletTone(inp, m);
                    var v = window.validateBulletGrammar(r);
                    res.push({
                        inp: inp,
                        mode: m,
                        out: r,
                        nonEmpty: r.length > 0,
                        hasActiveVerb: v.hasActiveVerb,
                        score: v.score
                    });
                });
            });
            print(JSON.stringify(res));
        """)
        results = json.loads(out)
        self.assertEqual(len(results), 24)
        for r in results:
            self.assertTrue(r["nonEmpty"], f"Result was empty for {r['inp']}")
            self.assertTrue(r["hasActiveVerb"], f"Missing active verb for {r['inp']} in mode {r['mode']}: {r['out']}")
            self.assertGreaterEqual(r["score"], 80)

    def test_stress_03_long_paragraph_inputs(self):
        """TC-STRESS-03: Long paragraphs (3,000+ chars) transform safely without truncation crash."""
        out = self.run_jsc_script("""
            var longHe = "עבדתי במשמרות לילה רבות וניהלתי תחנות גז במערך נתג״ז ואסדת כריש ".repeat(50);
            var longEn = "I was responsible for monitoring gas pressures and SCADA telemetry systems ".repeat(50);

            var rHeTech = window.transformBulletTone(longHe, "technical");
            var rHeOper = window.transformBulletTone(longHe, "operational");
            var rEnTech = window.transformBulletTone(longEn, "technical");
            var rEnStrat = window.transformBulletTone(longEn, "strategic");

            print(JSON.stringify({
                heTechLen: rHeTech.length,
                heOperLen: rHeOper.length,
                enTechLen: rEnTech.length,
                enStratLen: rEnStrat.length,
                heTechVerb: window.validateBulletGrammar(rHeTech).hasActiveVerb,
                enTechVerb: window.validateBulletGrammar(rEnTech).hasActiveVerb
            }));
        """)
        res = json.loads(out)
        self.assertGreater(res["heTechLen"], 2000)
        self.assertGreater(res["enTechLen"], 2000)
        self.assertTrue(res["heTechVerb"])
        self.assertTrue(res["enTechVerb"])

    def test_stress_04_special_punctuation_and_injection(self):
        """TC-STRESS-04: Extreme punctuation, unicode, SQL and template injections transform safely."""
        out = self.run_jsc_script("""
            var inputs = [
                "!@#$%^&*()_+~|}{[]:;?><,./-=",
                "SELECT * FROM users WHERE '1'='1'; DROP TABLE logs; --",
                "{{template_var}} ${process.env.SECRET} <%= code %>",
                "He said \\"hello\\" and used \\\\path\\\\to\\\\file",
                "Special \\u0000 null byte and \\u202E RTL override"
            ];
            var modes = ["technical", "operational", "strategic"];
            var res = [];
            inputs.forEach(function(inp) {
                modes.forEach(function(m) {
                    var r = window.transformBulletTone(inp, m);
                    var v = window.validateBulletGrammar(r);
                    res.push({
                        inp: inp,
                        mode: m,
                        nonEmpty: r.length > 0,
                        hasActiveVerb: v.hasActiveVerb,
                        hasMetric: v.hasMetric,
                        score: v.score
                    });
                });
            });
            print(JSON.stringify(res));
        """)
        results = json.loads(out)
        self.assertEqual(len(results), 15)
        for r in results:
            self.assertTrue(r["nonEmpty"])
            self.assertTrue(r["hasActiveVerb"])
            self.assertTrue(r["hasMetric"])
            self.assertGreaterEqual(r["score"], 80)

    def test_stress_05_html_injection_resilience(self):
        """TC-STRESS-05: Raw HTML tags (<script>, <img>, <b>) are transformed safely without DOM mutation."""
        out = self.run_jsc_script("""
            var htmlInput = '<script>alert("XSS")</script><img src=x onerror=alert(1)><b>bold</b>';
            var modes = ["technical", "operational", "strategic"];
            var res = modes.map(function(m) {
                var r = window.transformBulletTone(htmlInput, m);
                var v = window.validateBulletGrammar(r);
                return {
                    mode: m,
                    out: r,
                    nonEmpty: r.length > 0,
                    hasActiveVerb: v.hasActiveVerb,
                    hasMetric: v.hasMetric
                };
            });
            print(JSON.stringify(res));
        """)
        results = json.loads(out)
        for r in results:
            self.assertTrue(r["nonEmpty"])
            self.assertTrue(r["hasActiveVerb"])
            self.assertTrue(r["hasMetric"])
            self.assertIn("<script>", r["out"])

    def test_stress_06_english_and_hebrew_bullets(self):
        """TC-STRESS-06: Authoritative English and Hebrew bullets across all 3 modes."""
        out = self.run_jsc_script("""
            var heBullet = "הייתי אחראי על ניטור לחצי גז באסדת כריש ותחנות הפחתת לחץ";
            var enBullet = "I was responsible for offshore gas operations and SCADA monitoring";

            var res = {
                he_tech: window.transformBulletTone(heBullet, "technical"),
                he_oper: window.transformBulletTone(heBullet, "operational"),
                he_strat: window.transformBulletTone(heBullet, "strategic"),
                en_tech: window.transformBulletTone(enBullet, "technical"),
                en_oper: window.transformBulletTone(enBullet, "operational"),
                en_strat: window.transformBulletTone(enBullet, "strategic")
            };

            var analyses = {};
            Object.keys(res).forEach(function(k) {
                analyses[k] = window.validateBulletGrammar(res[k]);
            });

            print(JSON.stringify({ res: res, analyses: analyses }));
        """)
        data = json.loads(out)
        for k, v in data["analyses"].items():
            self.assertTrue(v["hasActiveVerb"], f"Missing active verb in {k}: {data['res'][k]}")
            self.assertTrue(v["hasMetric"], f"Missing metric in {k}: {data['res'][k]}")
            self.assertGreaterEqual(v["score"], 80, f"Score too low for {k}: {v['score']}")

    # --- 2. Rapid Mode Switching Stress (120+ Inputs) ---

    def test_stress_07_rapid_mode_switching_120_inputs(self):
        """TC-STRESS-07: Rapid switching across 120+ inputs between technical, operational, and strategic."""
        out = self.run_jsc_script("""
            var sampleKeywords = [
                "gas PRMS", "turbines", "SCADA 24/7", "solar panels", "Bifacial PV", "high voltage", "low voltage",
                "offshore FPSO", "INGL", "nominations", "valves", "pumps", "pressure monitoring", "safety officer",
                "emergency shutdown ESD", "modbus PLC", "Siemens TIA", "control room", "inverters", "grid connection",
                "ניטור גז", "תחנות PRMS", "אסדת כריש", "לוחות מתח גבוה", "בקרת לחץ", "נומינציות יומיות", "פאנלים סולאריים",
                "ממירי מתח", "שנאים", "משאבות סחרור", "מגופי חירום", "בקר מתוכנת PLC", "השבתת מתקן", "משמרת לילה",
                "נוהל נעילה ותיוג LOTO", "בטיחות אש", "רציפות אספקה", "קריאת מדים", "ספיקת קו", "איטום צנרת"
            ];

            var prefixes = [
                "", "הייתי אחראי על ", "עבדתי ב-", "עשיתי ", "טיפלתי ב", "ביצעתי ", "אחראי ל", "דאגתי ל",
                "I was responsible for ", "worked on ", "handled ", "assisted with ", "participated in "
            ];

            var modes = ["technical", "operational", "strategic"];
            var simulated = [];

            for (var i = 0; i < 120; i++) {
                var pfx = prefixes[i % prefixes.length];
                var kw = sampleKeywords[i % sampleKeywords.length];
                var mode = modes[i % modes.length];
                simulated.push({ text: pfx + kw, mode: mode });
            }

            var failures = [];
            var successCount = 0;

            simulated.forEach(function(item, idx) {
                try {
                    var r = window.transformBulletTone(item.text, item.mode);
                    var v = window.validateBulletGrammar(r);

                    if (!r || r.length === 0) {
                        failures.push({ idx: idx, error: "Empty string returned" });
                        return;
                    }

                    if (!v.hasActiveVerb) {
                        failures.push({ idx: idx, error: "Missing active verb: " + r.substring(0, 30) });
                        return;
                    }

                    // Must contain quantified metric or statutory/HSE context
                    if (!v.hasMetric && !v.hasScope) {
                        failures.push({ idx: idx, error: "Missing domain context: " + r });
                        return;
                    }

                    successCount++;
                } catch (e) {
                    failures.push({ idx: idx, error: e.toString() });
                }
            });

            print(JSON.stringify({
                total: simulated.length,
                successCount: successCount,
                failures: failures
            }));
        """)
        res = json.loads(out)
        self.assertEqual(res["total"], 120)
        self.assertEqual(res["successCount"], 120, f"Failures encountered: {res['failures']}")
        self.assertEqual(len(res["failures"]), 0)

    # --- 3. Exception Freedom & Edge Handling ---

    def test_stress_08_null_and_undefined_handling(self):
        """TC-STRESS-08: Passing null, undefined, or missing mode does not throw uncaught exceptions."""
        out = self.run_jsc_script("""
            var r1 = window.transformBulletTone(null, "technical");
            var r2 = window.transformBulletTone(undefined, "operational");
            var r3 = window.transformBulletTone("משמרות", null);
            var r4 = window.transformBulletTone("משמרות", undefined);
            var r5 = window.transformBulletTone("משמרות", "UNKNOWN_MODE");

            print(JSON.stringify({
                r1: r1,
                r2: r2,
                r3_nonEmpty: r3.length > 0,
                r4_nonEmpty: r4.length > 0,
                r5_nonEmpty: r5.length > 0
            }));
        """)
        res = json.loads(out)
        self.assertEqual(res["r1"], "")
        self.assertEqual(res["r2"], "")
        self.assertTrue(res["r3_nonEmpty"])
        self.assertTrue(res["r4_nonEmpty"])
        self.assertTrue(res["r5_nonEmpty"])

    # --- 4. Adversarial Audit & Findings ---

    def test_stress_09_audit_preset_metric_coverage(self):
        """TC-STRESS-09: Adversarial audit verifying which presets score 100 vs 70 due to metric omission."""
        out = self.run_jsc_script("""
            var presets = [
                { name: "Gas Monitor", text: "עבדתי במשמרות בניטור גז" },
                { name: "Night Shift", text: "משמרת בלילה ב-Energean" },
                { name: "Nomination", text: "עשיתי נומינציות ודיברתי עם חברת החשמל ונתג״ז" },
                { name: "Solar PV", text: "טיפלתי במערכות סולאריות" },
                { name: "En Night Shift", text: "responsible for night shifts and monitored gas pressures" }
            ];
            var modes = ["technical", "operational", "strategic"];
            var audit = [];

            presets.forEach(function(p) {
                modes.forEach(function(m) {
                    var transformed = window.transformBulletTone(p.text, m);
                    var v = window.validateBulletGrammar(transformed);
                    audit.push({
                        preset: p.name,
                        mode: m,
                        score: v.score,
                        hasActiveVerb: v.hasActiveVerb,
                        hasMetric: v.hasMetric,
                        hasScope: v.hasScope
                    });
                });
            });
            print(JSON.stringify(audit));
        """)
        audit = json.loads(out)
        # Verify that all 15 preset combinations start with an active verb
        for a in audit:
            self.assertTrue(a["hasActiveVerb"], f"Missing active verb in {a['preset']} {a['mode']}")
            self.assertGreaterEqual(a["score"], 70)

        # Confirm empirical finding: Gas Monitor strategic and Solar PV strategic score 70 due to missing metric
        gas_strat = next(x for x in audit if x["preset"] == "Gas Monitor" and x["mode"] == "strategic")
        solar_strat = next(x for x in audit if x["preset"] == "Solar PV" and x["mode"] == "strategic")
        self.assertEqual(gas_strat["score"], 70)
        self.assertFalse(gas_strat["hasMetric"])
        self.assertEqual(solar_strat["score"], 70)
        self.assertFalse(solar_strat["hasMetric"])

    # --- 5. Zero-Emoji Compliance ---

    def test_stress_10_zero_emoji_in_test_file(self):
        """TC-STRESS-10: Verify this test file contains strictly 0 Unicode emojis."""
        current_file = Path(__file__).resolve()
        with open(current_file, "r", encoding="utf-8") as f:
            content = f.read()

        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"
            r"\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF"
            r"\U0001F1E0-\U0001F1FF"
            r"\U0001F900-\U0001F9FF"
            r"\U0001FA70-\U0001FAFF"
            r"\U00002702-\U000027B0"
            r"\U000024C2-\U0001F251]"
        )
        matches = emoji_pattern.findall(content)
        self.assertEqual(len(matches), 0, f"Found emojis in stress test file: {matches}")


if __name__ == "__main__":
    unittest.main()
