"""
Unit and Empirical Tests for Milestone 2: ATS & Hard Gates Engine
Validates:
- STATUTORY_HARD_GATES: 7 statutory engineering gates
- KEYWORD_TAXONOMY: 4-category competency taxonomy
- ATS_STRUCTURAL_RULES: Single-column, standard fonts, zero-emoji, contact parseability
- runAtsJobMatching, evaluateHardGates, extractMissingKeywords, checkAtsStructuralCompliance
- Execution via JavaScriptCore engine and DOM template integrity
"""

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone2AtsSpec(unittest.TestCase):
    """Specification tests for Career Studio Milestone 2 (ATS & Hard Gates)."""

    @classmethod
    def setUpClass(cls):
        cls.js_file = PROJECT_ROOT / "frontend" / "js" / "dashboard.js"
        cls.html_file = PROJECT_ROOT / "frontend" / "templates" / "index.html"
        cls.css_file = PROJECT_ROOT / "frontend" / "css" / "dashboard.css"
        cls.docs_html = PROJECT_ROOT / "docs" / "index.html"
        cls.docs_js = PROJECT_ROOT / "docs" / "dashboard.js"
        cls.docs_css = PROJECT_ROOT / "docs" / "dashboard.css"

    def run_jsc_script(self, script_code: str) -> str:
        """Helper to run JavaScript code inside JSC with dashboard.js loaded."""
        full_script = f"""
        var window = globalThis;
        if (!globalThis.console) {{
          globalThis.console = {{ log: print, warn: print, error: print, info: print }};
        }}
        window.addEventListener = function() {{}};
        window.removeEventListener = function() {{}};
        window.location = {{ hash: '' }};
        window.localStorage = {{
          getItem: function() {{ return null; }},
          setItem: function() {{}},
          removeItem: function() {{}}
        }};
        var localStorage = window.localStorage;
        var document = {{
          addEventListener: function() {{}},
          removeEventListener: function() {{}},
          getElementById: function(id) {{ return null; }},
          querySelector: function(sel) {{ return null; }},
          querySelectorAll: function(sel) {{ return []; }}
        }};
        """
        # Read dashboard.js
        with open(self.js_file, "r", encoding="utf-8") as f:
            js_src = f.read()

        runner = full_script + "\n" + js_src + "\n" + script_code
        proc = subprocess.run(
            [JSC_BIN, "-e", runner],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"JSC Execution Failed (code {proc.returncode}):\n{proc.stderr}\nOutput:\n{proc.stdout}")
        return proc.stdout.strip()

    # --- 1. Statutory Hard Gates Verification ---

    def test_m2_01_all_seven_hard_gates_defined_in_js(self):
        """TC-M2-01: Exactly 7 statutory engineering hard gates defined in JS."""
        out = self.run_jsc_script("print(JSON.stringify(window.STATUTORY_HARD_GATES.map(g => g.id)));")
        gate_ids = json.loads(out)
        expected = [
            "gate_practical_mech_eng",
            "gate_certified_electrician",
            "gate_degree_bsc_engineer",
            "gate_safety_officer",
            "gate_working_at_heights",
            "gate_hazmat_permit",
            "gate_asme_iso_standards"
        ]
        self.assertEqual(gate_ids, expected)

    def test_m2_02_hard_gates_evaluation_practical_mech_eng_pass(self):
        """TC-M2-02: evaluateHardGates detects practical mech engineer with PASS status."""
        out = self.run_jsc_script("""
            var res = window.evaluateHardGates("דרוש הנדסאי מכונות למתקן תעשייתי");
            print(JSON.stringify(res));
        """)
        gates = json.loads(out)
        self.assertEqual(len(gates), 1)
        self.assertEqual(gates[0]["id"], "gate_practical_mech_eng")
        self.assertEqual(gates[0]["status"], "PASS")

    def test_m2_03_hard_gates_evaluation_electrician_in_progress(self):
        """TC-M2-03: evaluateHardGates detects certified electrician with IN_PROGRESS status."""
        out = self.run_jsc_script("""
            var res = window.evaluateHardGates("חובה רישיון חשמלאי מוסמך בתוקף");
            print(JSON.stringify(res));
        """)
        gates = json.loads(out)
        self.assertEqual(len(gates), 1)
        self.assertEqual(gates[0]["id"], "gate_certified_electrician")
        self.assertEqual(gates[0]["status"], "IN_PROGRESS")

    def test_m2_04_hard_gates_evaluation_bsc_engineer_gap(self):
        """TC-M2-04: evaluateHardGates detects B.Sc degree requirement with GAP status."""
        out = self.run_jsc_script("""
            var res = window.evaluateHardGates("דרוש תואר ראשון בהנדסת מכונות B.Sc");
            print(JSON.stringify(res));
        """)
        gates = json.loads(out)
        self.assertEqual(len(gates), 1)
        self.assertEqual(gates[0]["id"], "gate_degree_bsc_engineer")
        self.assertEqual(gates[0]["status"], "GAP")

    def test_m2_05_hard_gates_empty_input_returns_empty_array(self):
        """TC-M2-05: evaluateHardGates returns empty array on empty or null input."""
        out = self.run_jsc_script("""
            var r1 = window.evaluateHardGates("");
            var r2 = window.evaluateHardGates(null);
            var r3 = window.evaluateHardGates("   ");
            print(JSON.stringify([r1.length, r2.length, r3.length]));
        """)
        lengths = json.loads(out)
        self.assertEqual(lengths, [0, 0, 0])

    # --- 2. Keyword Taxonomy Classification ---

    def test_m2_06_keyword_taxonomy_has_four_buckets(self):
        """TC-M2-06: KEYWORD_TAXONOMY contains methodologies, financials, systems, and energy."""
        out = self.run_jsc_script("print(JSON.stringify(Object.keys(window.KEYWORD_TAXONOMY)));")
        cats = json.loads(out)
        self.assertEqual(cats, ["methodologies", "financials", "systems", "energy"])

    def test_m2_07_extract_missing_keywords_categorizes_correctly(self):
        """TC-M2-07: extractMissingKeywords segregates missing terms into 4 categories."""
        out = self.run_jsc_script("""
            var posting = "דרוש ידע ב-Lean, Six Sigma, תקציבי CAPEX, מערכות PLC וסוללות BESS";
            var res = window.extractMissingKeywords(posting, window.CANONICAL_CV_PROFILE);
            print(JSON.stringify({
                methodologies: res.methodologies,
                financials: res.financials,
                systems: res.systems,
                energy: res.energy
            }));
        """)
        res = json.loads(out)
        self.assertIn("Lean", res["methodologies"])
        self.assertIn("Six Sigma", res["methodologies"])
        self.assertIn("CAPEX", res["financials"])
        self.assertIn("PLC", res["systems"])
        self.assertIn("BESS", res["energy"])

    def test_m2_08_candidate_strengths_classified_as_matched(self):
        """TC-M2-08: Candidate held skills (SCADA, PRMS, FPSO) are classified as matched, not missing."""
        out = self.run_jsc_script("""
            var posting = "דרוש ניסיון במערכות SCADA, תחנות PRMS ואסדת FPSO";
            var res = window.extractMissingKeywords(posting, window.CANONICAL_CV_PROFILE);
            print(JSON.stringify({
                missingSystems: res.systems,
                matchedSystems: res.matched.systems,
                missingEnergy: res.energy,
                matchedEnergy: res.matched.energy
            }));
        """)
        res = json.loads(out)
        self.assertNotIn("SCADA", res["missingSystems"])
        self.assertIn("SCADA", res["matchedSystems"])
        self.assertNotIn("PRMS", res["missingSystems"])
        self.assertIn("PRMS", res["matchedSystems"])
        self.assertIn("FPSO", res["matchedEnergy"])

    # --- 3. ATS Structural Compliance ---

    def test_m2_09_ats_structural_rules_defined(self):
        """TC-M2-09: ATS_STRUCTURAL_RULES defines 4 core rules with severities."""
        out = self.run_jsc_script("print(JSON.stringify(window.ATS_STRUCTURAL_RULES.map(r => r.rule_id)));")
        rule_ids = json.loads(out)
        expected = ["ats_single_column", "ats_standard_fonts", "ats_zero_emojis", "ats_contact_parseability"]
        self.assertEqual(rule_ids, expected)

    def test_m2_10_ats_structural_compliance_default_passes(self):
        """TC-M2-10: checkAtsStructuralCompliance passes for candidate profile."""
        out = self.run_jsc_script("""
            var res = window.checkAtsStructuralCompliance();
            print(JSON.stringify({ passed: res.passed, score: res.score, issuesCount: res.issues.length }));
        """)
        res = json.loads(out)
        self.assertTrue(res["passed"])
        self.assertEqual(res["score"], 100)
        self.assertEqual(res["issuesCount"], 0)

    # --- 4. runAtsJobMatching Full Pipeline ---

    def test_m2_11_run_ats_job_matching_high_match_score(self):
        """TC-M2-11: runAtsJobMatching returns high score (>80) on matching gas controller role."""
        out = self.run_jsc_script("""
            var text = "דרוש בקר גז טבעי ותפעול מתקני אנרגיה 24/7. דרישות: הנדסאי מכונות, ידע ב-SCADA, PRMS, ונומינציות.";
            var res = window.runAtsJobMatching(text);
            print(JSON.stringify({ score: res.matchScore, gates: res.hardGates.length }));
        """)
        res = json.loads(out)
        self.assertGreaterEqual(res["score"], 80)
        self.assertLessEqual(res["score"], 100)
        self.assertGreaterEqual(res["gates"], 1)

    def test_m2_12_run_ats_job_matching_gap_caps_score(self):
        """TC-M2-12: runAtsJobMatching caps score (<=55) when mandatory B.Sc gate is missing."""
        out = self.run_jsc_script("""
            var text = "דרוש תואר ראשון בהנדסת מכונות B.Sc חובה למשרת פיתוח";
            var res = window.runAtsJobMatching(text);
            print(JSON.stringify({ score: res.matchScore }));
        """)
        res = json.loads(out)
        self.assertLessEqual(res["score"], 55)

    def test_m2_13_run_ats_job_matching_empty_returns_zero(self):
        """TC-M2-13: runAtsJobMatching returns 0 score on empty text."""
        out = self.run_jsc_script("""
            var res = window.runAtsJobMatching("");
            print(JSON.stringify({ score: res.matchScore }));
        """)
        res = json.loads(out)
        self.assertEqual(res["score"], 0)

    # --- 5. Template & UI Mounting Integrity ---

    def test_m2_14_index_template_has_ats_components(self):
        """TC-M2-14: index.html has complete interactive ATS module components."""
        html = self.html_file.read_text(encoding="utf-8")
        self.assertIn('id="studioModuleAts"', html)
        self.assertIn('id="atsJobSelector"', html)
        self.assertIn('id="atsJobInput"', html)
        self.assertIn('id="atsScoreValue"', html)
        self.assertIn('id="atsGaugeProgress"', html)
        self.assertIn('id="atsHardGatesList"', html)
        self.assertIn('id="atsKeywordsMethodologies"', html)
        self.assertIn('id="atsKeywordsFinancials"', html)
        self.assertIn('id="atsKeywordsSystems"', html)
        self.assertIn('id="atsKeywordsEnergy"', html)
        self.assertIn('id="atsRulesChecklist"', html)

    def test_m2_15_css_has_ats_glassmorphism_rules(self):
        """TC-M2-15: dashboard.css defines all required ATS styling classes."""
        css = self.css_file.read_text(encoding="utf-8")
        self.assertIn('.ats-workspace-content', css)
        self.assertIn('.ats-gauge-val', css)
        self.assertIn('.badge-pass', css)
        self.assertIn('.badge-in-progress', css)
        self.assertIn('.badge-gap', css)
        self.assertIn('.badge-notice', css)
        self.assertIn('.ats-keyword-tag', css)

    def test_m2_16_docs_synchronized_with_frontend(self):
        """TC-M2-16: docs/index.html and docs/dashboard.js contain latest ATS implementation."""
        docs_html_txt = self.docs_html.read_text(encoding="utf-8")
        docs_js_txt = self.docs_js.read_text(encoding="utf-8")
        self.assertIn('id="atsJobSelector"', docs_html_txt)
        self.assertIn('runAtsJobMatching', docs_js_txt)
        self.assertIn('STATUTORY_HARD_GATES', docs_js_txt)


if __name__ == "__main__":
    unittest.main()
