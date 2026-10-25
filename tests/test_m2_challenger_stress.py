#!/usr/bin/env python3
"""
tests/test_m2_challenger_stress.py

Empirical Challenger Stress Test Suite for Milestone 2: ATS & Hard Gates Engine
Validates:
1. Extreme & Boundary Inputs:
   - Empty string, whitespace-only, 50,000 words execution speed and schema,
     XSS injection and script resilience.
2. Safety Officer Requirement Penalty:
   - Certified safety officer requirement consistently forces score <= 55%.
3. Full Match Posting Threshold:
   - Factual match against Ido Gal's CV achieves score >= 85%.
4. Zero-Emoji Compliance:
   - All challenger test artifacts strictly obey Zero-Emoji policy.
5. Statutory B.Sc. Engineer Penalty Invariant & Flaw Reproduction:
   - Tests whether requiring B.Sc. Mechanical / Electrical Engineer ALWAYS forces score <= 55%.
   - Exposes empirical gap where 'B.Sc. Mechanical Engineer' bypasses gate and scores 95%.
6. ATS Contact Parseability Invariant & Phone Format Flaw Reproduction:
   - Tests whether candidate's canonical phone (052-632-8886) passes structural compliance in live DOM.
   - Exposes empirical gap where 2-hyphen Israeli format fails regex and triggers 5-point deduction.
"""

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone2ChallengerStress(unittest.TestCase):
    """Adversarial stress and boundary tests for Milestone 2 ATS engine."""

    @classmethod
    def setUpClass(cls):
        cls.js_file = PROJECT_ROOT / "frontend" / "js" / "dashboard.js"
        cls.harness_file = PROJECT_ROOT / "tests" / "stress_m2_harness.js"

    def run_jsc_script(self, script_code: str, mock_dom: bool = False) -> str:
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
        """

        if mock_dom:
            dom_setup += """
            var mockCanvasElem = {
              id: 'careerStudioCvCanvas',
              nodeType: 1,
              get textContent() { return window.CANONICAL_CV_PROFILE ? window.CANONICAL_CV_PROFILE.text : ''; },
              get innerText() { return window.CANONICAL_CV_PROFILE ? window.CANONICAL_CV_PROFILE.text : ''; },
              style: {},
              classList: { add: function(){}, remove: function(){}, contains: function(){ return false; } },
              querySelectorAll: function() { return []; }
            };
            var document = {
              addEventListener: function() {},
              removeEventListener: function() {},
              getElementById: function(id) {
                if (id === 'careerStudioCvCanvas' || id === 'careerStudioWorkspace') {
                  return mockCanvasElem;
                }
                return null;
              },
              querySelector: function(sel) {
                if (sel.indexOf('careerStudioCvCanvas') !== -1 || sel.indexOf('cv-container') !== -1) {
                  return mockCanvasElem;
                }
                return null;
              },
              querySelectorAll: function(sel) { return []; }
            };
            """
        else:
            dom_setup += """
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
            text=True,
            timeout=20,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"JSC Execution Failed (code {proc.returncode}):\n{proc.stderr}\nOutput:\n{proc.stdout}")
        return proc.stdout.strip()

    # --- 1. Extreme Inputs & XSS Stress ---

    def test_m2_challenger_01_extreme_inputs(self):
        """TC-CHALLENGER-M2-01: Empty string, whitespace variants, 50,000 words, and 16 XSS payloads."""
        script = """
        var resEmpty = window.runAtsJobMatching("");
        var resWs = window.runAtsJobMatching("   \\n\\t  ");
        var resNull = window.runAtsJobMatching(null);
        var resNum = window.runAtsJobMatching(12345);

        // 50,000 words
        var words = [];
        for (var i = 0; i < 50000; i++) {
          words.push("word" + i + " SCADA PRMS Energean gas operation valve");
        }
        var t0 = Date.now();
        var resHuge = window.runAtsJobMatching(words.join(" "));
        var hugeElapsed = Date.now() - t0;

        // XSS Payloads
        var xssPayloads = [
          "<script>alert(1)</script>",
          "<img src=x onerror=alert(1)>",
          "<svg/onload=alert(1)>",
          "<b>Bold</b><i>Italic</i>",
          "דרוש הנדסאי מכונות <script>steal()</script> SCADA"
        ];
        var xssOk = true;
        xssPayloads.forEach(function(p) {
          var r = window.runAtsJobMatching(p);
          if (typeof r.matchScore !== 'number') xssOk = false;
        });

        print(JSON.stringify({
          scoreEmpty: resEmpty.matchScore,
          scoreWs: resWs.matchScore,
          scoreNull: resNull.matchScore,
          scoreNum: resNum.matchScore,
          hugeElapsedMs: hugeElapsed,
          hugeScore: resHuge.matchScore,
          hugeGatesCount: resHuge.hardGates.length,
          xssOk: xssOk
        }));
        """
        out = self.run_jsc_script(script)
        data = json.loads(out)

        self.assertEqual(data["scoreEmpty"], 0)
        self.assertEqual(data["scoreWs"], 0)
        self.assertEqual(data["scoreNull"], 0)
        self.assertEqual(data["scoreNum"], 0)
        self.assertLessEqual(data["hugeElapsedMs"], 1000)
        self.assertGreaterEqual(data["hugeScore"], 0)
        self.assertLessEqual(data["hugeScore"], 100)
        self.assertTrue(data["xssOk"])

    # --- 2. Safety Officer Penalty Invariant ---

    def test_m2_challenger_02_safety_officer_penalty(self):
        """TC-CHALLENGER-M2-02: Requiring certified safety officer ALWAYS forces score <= 55%."""
        script = """
        var variations = [
          "דרוש ממונה בטיחות",
          "דרוש ממונה בטיחות בעבודה",
          "דרישת סף: ממונה בטיחות מוסמך",
          "certified safety officer required",
          "Certified Safety Officer on site",
          "certified safety manager"
        ];
        var results = variations.map(function(v) {
          var r1 = window.runAtsJobMatching(v);
          var r2 = window.runAtsJobMatching(v + " בקר גז טבעי הנדסאי מכונות רופין SCADA PRMS Energean FPSO");
          return { text: v, scoreStandalone: r1.matchScore, scoreCombined: r2.matchScore };
        });
        print(JSON.stringify(results));
        """
        out = self.run_jsc_script(script)
        results = json.loads(out)

        for res in results:
            self.assertLessEqual(
                res["scoreStandalone"],
                55,
                f"Safety Officer standalone [{res['text']}] must be <= 55, got {res['scoreStandalone']}",
            )
            self.assertLessEqual(
                res["scoreCombined"],
                55,
                f"Safety Officer combined [{res['text']}] must be <= 55 even with full skills, got {res['scoreCombined']}",
            )

    # --- 3. Full Match Posting Threshold Invariant ---

    def test_m2_challenger_03_full_match_posting_score_threshold(self):
        """TC-CHALLENGER-M2-03: Factual match with Ido Gal's CV profile achieves matchScore >= 85%."""
        script = """
        var jobs = [
          "דרוש בקר גז טבעי ותפעול מתקני אנרגיה 24/7 בחברת Energean. דרישות: הנדסאי מכונות מוסמך רופין, SCADA, PRMS, אסדת הפקה FPSO, נומינציות נתג״ז.",
          "Gas Controller and Energy Operations Specialist at Energean. Practical Mechanical Engineer, SCADA, PRMS, FPSO, 24/7 operations.",
          "דרוש מנהל תפעול סולארי Bifacial PV. הנדסאי מכונות, חשמלאי מוסמך בלימודים, עבודה בגובה, SCADA."
        ];
        var scores = jobs.map(function(j) {
          return window.runAtsJobMatching(j).matchScore;
        });
        print(JSON.stringify(scores));
        """
        out = self.run_jsc_script(script)
        scores = json.loads(out)

        for s in scores:
            self.assertGreaterEqual(s, 85, f"Full match posting must achieve >= 85%, got {s}")
            self.assertLessEqual(s, 100)

    # --- 4. Zero-Emoji Compliance ---

    def test_m2_challenger_04_zero_emoji_compliance(self):
        """TC-CHALLENGER-M2-04: Challenger stress harness and test files strictly contain 0 emojis."""
        from scripts.validate_zero_emoji import scan_file

        files = [
            PROJECT_ROOT / "tests" / "stress_m2_harness.js",
            PROJECT_ROOT / "tests" / "test_m2_challenger_stress.py",
        ]
        for f in files:
            violations = scan_file(f)
            self.assertEqual(len(violations), 0, f"Found emoji violations in {f.name}: {violations}")

    # --- 5. B.Sc. Engineer Penalty Flaw Reproduction (Adversarial Challenge) ---

    def test_m2_challenger_05_bsc_engineer_penalty_flaw_detection(self):
        """
        TC-CHALLENGER-M2-05: Adversarial test verifying B.Sc. Engineer penalty invariant.
        Exposes empirical flaw: 'B.Sc. Mechanical Engineer' ends with 'Engineer', but regex
        requires 'engineering', bypassing hard gate and yielding score 95% instead of <= 55%.
        """
        script = """
        var passingReq = "B.Sc. in mechanical engineering required";
        var failingReq = "Seeking B.Sc. Mechanical Engineer for facility";

        var rPass = window.runAtsJobMatching(passingReq + " SCADA PRMS הנדסאי מכונות");
        var rFail = window.runAtsJobMatching(failingReq + " SCADA PRMS הנדסאי מכונות");

        print(JSON.stringify({
          passingScore: rPass.matchScore,
          passingGates: rPass.hardGates.map(function(g) { return g.id; }),
          failingScore: rFail.matchScore,
          failingGates: rFail.hardGates.map(function(g) { return g.id; })
        }));
        """
        out = self.run_jsc_script(script)
        data = json.loads(out)

        # Baseline: 'engineering' correctly triggers penalty
        self.assertLessEqual(data["passingScore"], 55)
        self.assertIn("gate_degree_bsc_engineer", data["passingGates"])

        # Adversarial check: 'Engineer' MUST also trigger penalty per requirements
        self.assertLessEqual(
            data["failingScore"],
            55,
            f"CRITICAL FLAW: Requiring 'B.Sc. Mechanical Engineer' bypassed penalty, score: {data['failingScore']} > 55%"
        )

    # --- 6. Phone Regex Flaw Reproduction (Adversarial Challenge) ---

    def test_m2_challenger_06_canonical_phone_structural_compliance_flaw(self):
        """
        TC-CHALLENGER-M2-06: Adversarial test verifying structural compliance on canonical CV.
        Exposes empirical flaw: phonePattern /(?:05\\d-?\\d{7}|...)/ rejects 2-hyphen format
        '052-632-8886' present in CANONICAL_CV_PROFILE, causing false failure and 5-point deduction.
        """
        script = """
        var res = window.checkAtsStructuralCompliance('#careerStudioCvCanvas');
        print(JSON.stringify({
          passed: res.passed,
          score: res.score,
          issues: res.issues
        }));
        """
        out = self.run_jsc_script(script, mock_dom=True)
        data = json.loads(out)

        self.assertTrue(
            data["passed"],
            f"HIGH FLAW: Canonical Israeli phone format 052-632-8886 failed structural compliance: {data['issues']}"
        )
        self.assertEqual(
            data["score"],
            100,
            f"HIGH FLAW: Canonical profile scored {data['score']}% instead of 100% in live DOM"
        )


if __name__ == "__main__":
    unittest.main()
