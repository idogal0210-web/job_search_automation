"""
Unit and Empirical Tests for Milestone 3: AI Writer, 3-Mode Tone Switcher & Industrial Terminology Engine
Validates:
- TONE_SWITCHER_PROFILES: 3 tone modes (technical, operational, strategic)
- Formula compliance: [Active Verb] + [Specific Scope/System] + [Quantified HSE / Operational Metric]
- transformBulletTone: passive-to-active transformation across all 3 modes
- validateBulletGrammar: grammar analysis, active verb detection, metric detection, score computation (0-100)
- ENERGY_DICTIONARY: bilingual dictionary with >= 18 essential terms and search/filter functions
- DOM Template & CSS Glassmorphism integrity
- Strict Zero-Emoji compliance
- Execution via JavaScriptCore engine
"""

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone3WriterSpec(unittest.TestCase):
    """Specification tests for Career Studio Milestone 3 (AI Writer & Tone Switcher)."""

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

    # --- 1. TONE_SWITCHER_PROFILES Verification ---

    def test_m3_01_all_three_tone_profiles_defined(self):
        """TC-M3-01: Exactly 3 tone modes defined (technical, operational, strategic)."""
        out = self.run_jsc_script("print(JSON.stringify(Object.keys(window.TONE_SWITCHER_PROFILES)));")
        profiles = json.loads(out)
        self.assertEqual(sorted(profiles), ["operational", "strategic", "technical"])

    def test_m3_02_tone_profiles_structure_and_verbs(self):
        """TC-M3-02: Each tone profile has complete metadata and active action verbs."""
        out = self.run_jsc_script("""
            var keys = Object.keys(window.TONE_SWITCHER_PROFILES);
            var res = keys.map(function(k) {
                var p = window.TONE_SWITCHER_PROFILES[k];
                return {
                    id: p.id,
                    hasLabel: !!p.label_he,
                    hasIcon: !!p.icon,
                    hasFormula: !!p.bullet_transformation_formula,
                    hasExampleBefore: !!p.example_before,
                    hasExampleAfter: !!p.example_after,
                    verbCount: (p.active_verbs || []).length
                };
            });
            print(JSON.stringify(res));
        """)
        profiles_meta = json.loads(out)
        for meta in profiles_meta:
            self.assertTrue(meta["hasLabel"], f"Missing label_he in {meta['id']}")
            self.assertTrue(meta["hasIcon"], f"Missing icon in {meta['id']}")
            self.assertTrue(meta["hasFormula"], f"Missing formula in {meta['id']}")
            self.assertTrue(meta["hasExampleBefore"], f"Missing example_before in {meta['id']}")
            self.assertTrue(meta["hasExampleAfter"], f"Missing example_after in {meta['id']}")
            self.assertGreaterEqual(meta["verbCount"], 5, f"Expected >= 5 active verbs in {meta['id']}")

    def test_m3_03_active_verbs_contain_required_domain_verbs(self):
        """TC-M3-03: Active action verbs in each tone match industrial energy operations."""
        out = self.run_jsc_script("""
            var p = window.TONE_SWITCHER_PROFILES;
            print(JSON.stringify({
                tech: p.technical.active_verbs,
                oper: p.operational.active_verbs,
                strat: p.strategic.active_verbs
            }));
        """)
        verbs = json.loads(out)
        # Technical verbs: ניטרתי, כיַילתי/כיילתי, חישבתי, ניתחתי, אפיינתי, התקנתי
        self.assertTrue(any("ניטרתי" in v for v in verbs["tech"]))
        self.assertTrue(any("חישבתי" in v for v in verbs["tech"]))
        self.assertTrue(any("אפיינתי" in v for v in verbs["tech"]))
        # Operational verbs: הובלתי, תפעלתי, ניהלתי, בלמתי, אכפתי, הכרעתי
        self.assertTrue(any("הובלתי" in v for v in verbs["oper"]))
        self.assertTrue(any("תפעלתי" in v for v in verbs["oper"]))
        self.assertTrue(any("בלמתי" in v for v in verbs["oper"]))
        # Strategic verbs: סנכרנתי, תיאמתי, ייעלתי, הכשרתי, הטמעתי, ניהלתי
        self.assertTrue(any("סנכרנתי" in v for v in verbs["strat"]))
        self.assertTrue(any("תיאמתי" in v for v in verbs["strat"]))
        self.assertTrue(any("ייעלתי" in v for v in verbs["strat"]))

    # --- 2. Formula Transformation & Passive-to-Active (transformBulletTone) ---

    def test_m3_04_transform_technical_mode(self):
        """TC-M3-04: Technical mode transforms raw gas bullet into engineering parameters & PRMS."""
        raw = "עבדתי במשמרות בניטור גז ודאגתי שלא יהיו תקלות."
        out = self.run_jsc_script(f"""
            var res = window.transformBulletTone({json.dumps(raw)}, 'technical');
            print(JSON.stringify(res));
        """)
        transformed = json.loads(out)
        self.assertIn("ניטרתי", transformed)
        self.assertIn("PRMS", transformed)
        self.assertIn("45 bar", transformed)
        self.assertNotIn("עבדתי", transformed)
        self.assertNotIn("אני ", transformed)

    def test_m3_05_transform_operational_mode(self):
        """TC-M3-05: Operational mode transforms night shift bullet into 24/7 solo responsibility & HSE metrics."""
        raw = "הייתי אחראי על המשמרת בלילה ודאגתי שלא יהיו תקלות."
        out = self.run_jsc_script(f"""
            var res = window.transformBulletTone({json.dumps(raw)}, 'operational');
            print(JSON.stringify(res));
        """)
        transformed = json.loads(out)
        self.assertIn("24/7", transformed)
        self.assertIn("100%", transformed)
        self.assertTrue("LTI" in transformed or "בטיחות" in transformed)
        self.assertNotIn("הייתי אחראי", transformed)
        self.assertNotIn("אני ", transformed)

    def test_m3_06_transform_strategic_mode(self):
        """TC-M3-06: Strategic mode transforms nomination bullet into cross-organizational INGL/FPSO coordination."""
        raw = "עשיתי נומינציות ודיברתי עם חברת החשמל ונתג״ז."
        out = self.run_jsc_script(f"""
            var res = window.transformBulletTone({json.dumps(raw)}, 'strategic');
            print(JSON.stringify(res));
        """)
        transformed = json.loads(out)
        self.assertIn("סנכרנתי", transformed)
        self.assertIn("נתג״ז", transformed)
        self.assertIn("100%", transformed)
        self.assertNotIn("עשיתי", transformed)

    def test_m3_07_transform_passive_removal(self):
        """TC-M3-07: Passive phrasing ('עבדתי ב', 'הייתי אחראי') is cleanly eliminated."""
        passives = [
            "הייתי אחראי על ניטור לחצים",
            "עבדתי במתקן סולארי",
            "טיפלתי בנומינציות"
        ]
        for p in passives:
            out = self.run_jsc_script(f"""
                var res = window.transformBulletTone({json.dumps(p)}, 'technical');
                print(JSON.stringify(res));
            """)
            transformed = json.loads(out)
            self.assertFalse(transformed.startswith("הייתי"))
            self.assertFalse(transformed.startswith("עבדתי"))
            self.assertFalse(transformed.startswith("טיפלתי"))
            self.assertNotIn("אני ", transformed)

    def test_m3_08_transform_arbitrary_input_compliance(self):
        """TC-M3-08: Arbitrary user input dynamically produces active verb, domain scope, and metric."""
        raw = "בדקתי לחצים במערכת ההולכה"
        out = self.run_jsc_script(f"""
            var res = window.transformBulletTone({json.dumps(raw)}, 'technical');
            print(JSON.stringify(res));
        """)
        transformed = json.loads(out)
        self.assertTrue(transformed.startswith("ניטרתי") or transformed.startswith("כיַילתי") or transformed.startswith("חישבתי"))
        self.assertTrue("bar" in transformed or "%" in transformed)

    def test_m3_09_transform_english_bullet_mode(self):
        """TC-M3-09: English bullets transform into professional English active action verbs with metrics."""
        raw = "I was responsible for night shifts and monitored gas pressures."
        out = self.run_jsc_script(f"""
            var res = window.transformBulletTone({json.dumps(raw)}, 'operational');
            print(JSON.stringify(res));
        """)
        transformed = json.loads(out)
        self.assertTrue(transformed.startswith("Spearheaded") or transformed.startswith("Operated") or transformed.startswith("Monitored"))
        self.assertIn("24/7", transformed)
        self.assertIn("100%", transformed)
        self.assertNotIn("I was", transformed)

    def test_m3_10_transform_empty_or_whitespace(self):
        """TC-M3-10: Empty or whitespace input returns empty string gracefully."""
        out = self.run_jsc_script("""
            var r1 = window.transformBulletTone('', 'technical');
            var r2 = window.transformBulletTone('   ', 'operational');
            print(JSON.stringify({ r1: r1, r2: r2 }));
        """)
        res = json.loads(out)
        self.assertEqual(res["r1"], "")
        self.assertEqual(res["r2"], "")

    # --- 3. Grammar Validator & Metric Detection (validateBulletGrammar) ---

    def test_m3_11_grammar_validator_empty_input(self):
        """TC-M3-11: Empty input returns score 0 with suggestions."""
        out = self.run_jsc_script("""
            var res = window.validateBulletGrammar('');
            print(JSON.stringify(res));
        """)
        res = json.loads(out)
        self.assertEqual(res["score"], 0)
        self.assertFalse(res["hasActiveVerb"])
        self.assertFalse(res["hasMetric"])
        self.assertFalse(res["hasScope"])
        self.assertGreater(len(res["suggestions"]), 0)

    def test_m3_12_grammar_validator_high_score_transformed(self):
        """TC-M3-12: Complete high-impact bullet achieves 100/100 score."""
        bullet = "ניטרתי באופן רציף לחצי צנרת וספיקות גז במערך של 10+ תחנות PRMS, תוך זיהוי מיידי של סטיות לחץ מתחת ל-45 bar ומניעת תקלות הולכה."
        out = self.run_jsc_script(f"""
            var res = window.validateBulletGrammar({json.dumps(bullet)});
            print(JSON.stringify(res));
        """)
        res = json.loads(out)
        self.assertEqual(res["score"], 100)
        self.assertTrue(res["hasActiveVerb"])
        self.assertTrue(res["hasMetric"])
        self.assertTrue(res["hasScope"])
        self.assertEqual(res["detectedTone"], "technical")

    def test_m3_13_grammar_validator_passive_penalized(self):
        """TC-M3-13: Passive statement receives low score (<= 20) and corrective suggestions."""
        bullet = "הייתי אחראי על המשמרת בלילה ודאגתי שלא יהיו תקלות."
        out = self.run_jsc_script(f"""
            var res = window.validateBulletGrammar({json.dumps(bullet)});
            print(JSON.stringify(res));
        """)
        res = json.loads(out)
        self.assertLessEqual(res["score"], 20)
        self.assertFalse(res["hasActiveVerb"])
        self.assertFalse(res["hasMetric"])
        self.assertGreater(len(res["suggestions"]), 0)

    def test_m3_14_grammar_validator_metric_detection_patterns(self):
        """TC-M3-14: Detector flags metric for 24/7, bar, %, MW, 0 LTI, zero harm."""
        bullets_with_metrics = [
            "תפעלתי משמרות 24/7 ללא תקלות",
            "ניטרתי לחצים מתחת ל-45 bar",
            "השגתי 100% רציפות אספקה",
            "הפעלתי שדה סולארי בהספק 20MW",
            "שמרתי על יעד של 0 תאונות LTI",
            "שמרתי על אפס תקלות השבתה"
        ]
        for b in bullets_with_metrics:
            out = self.run_jsc_script(f"""
                var res = window.validateBulletGrammar({json.dumps(b)});
                print(JSON.stringify(res.hasMetric));
            """)
            self.assertTrue(json.loads(out), f"Metric not detected in: {b}")

    def test_m3_15_grammar_validator_scope_detection_patterns(self):
        """TC-M3-15: Detector flags system/scope for PRMS, SCADA, Bifacial PV, INGL, FPSO."""
        bullets_with_scope = [
            "ניטרתי תחנות PRMS בשטח",
            "תפעלתי מערכת SCADA מרכזית",
            "התקנתי פאנלים מסוג Bifacial PV",
            "תיאמתי מול נתג״ז",
            "סנכרנתי מול אסדת FPSO"
        ]
        for b in bullets_with_scope:
            out = self.run_jsc_script(f"""
                var res = window.validateBulletGrammar({json.dumps(b)});
                print(JSON.stringify(res.hasScope));
            """)
            self.assertTrue(json.loads(out), f"Scope not detected in: {b}")

    def test_m3_16_grammar_validator_tone_detection(self):
        """TC-M3-16: Correctly detects technical, operational, and strategic tones."""
        tech = "ניטרתי לחצים 45 bar במערכת PRMS וכיול מכשור"
        oper = "תפעלתי משמרות 24/7 בחירום עם 0 תאונות LTI"
        strat = "סנכרנתי בקשות נומינציה מול נתג״ז ואסדת FPSO"

        out_tech = json.loads(self.run_jsc_script(f"print(JSON.stringify(window.validateBulletGrammar({json.dumps(tech)}).detectedTone));"))
        out_oper = json.loads(self.run_jsc_script(f"print(JSON.stringify(window.validateBulletGrammar({json.dumps(oper)}).detectedTone));"))
        out_strat = json.loads(self.run_jsc_script(f"print(JSON.stringify(window.validateBulletGrammar({json.dumps(strat)}).detectedTone));"))

        self.assertEqual(out_tech, "technical")
        self.assertEqual(out_oper, "operational")
        self.assertEqual(out_strat, "strategic")

    def test_m3_17_grammar_validator_score_clamping(self):
        """TC-M3-17: Grammar score is strictly clamped between 0 and 100."""
        out = self.run_jsc_script("""
            var s1 = window.validateBulletGrammar('').score;
            var s2 = window.validateBulletGrammar('מילה').score;
            var s3 = window.validateBulletGrammar('ניטרתי באופן רציף לחצי צנרת וספיקות גז במערך של 10+ תחנות PRMS, תוך זיהוי מיידי של סטיות לחץ מתחת ל-45 bar ומניעת תקלות הולכה.').score;
            print(JSON.stringify({ s1: s1, s2: s2, s3: s3 }));
        """)
        scores = json.loads(out)
        self.assertGreaterEqual(scores["s1"], 0)
        self.assertLessEqual(scores["s1"], 100)
        self.assertGreaterEqual(scores["s2"], 0)
        self.assertLessEqual(scores["s2"], 100)
        self.assertGreaterEqual(scores["s3"], 0)
        self.assertLessEqual(scores["s3"], 100)

    # --- 4. Bilingual Energy Dictionary (ENERGY_DICTIONARY & searchEnergyDictionary) ---

    def test_m3_18_energy_dictionary_has_at_least_18_terms(self):
        """TC-M3-18: ENERGY_DICTIONARY contains at least 18 essential terms."""
        out = self.run_jsc_script("print(JSON.stringify(window.ENERGY_DICTIONARY.length));")
        count = json.loads(out)
        self.assertGreaterEqual(count, 18)

    def test_m3_19_energy_dictionary_mandatory_terms_present(self):
        """TC-M3-19: Dictionary contains all statutory and domain terms."""
        mandatory_acronyms = [
            "PRMS", "Nomination", "FPSO", "INGL", "SCADA", "PLC", "HMI",
            "Bifacial PV", "Monofacial PV", "BESS", "Inverter", "Transformer",
            "HV", "LV", "LTI", "Zero Harm", "ESD", "Telemetry"
        ]
        out = self.run_jsc_script("print(JSON.stringify(window.ENERGY_DICTIONARY.map(t => t.acronym)));")
        dict_acronyms = json.loads(out)
        for term in mandatory_acronyms:
            self.assertIn(term, dict_acronyms, f"Missing term: {term}")

    def test_m3_20_energy_dictionary_bilingual_fields(self):
        """TC-M3-20: Every dictionary entry has valid bilingual fields and insertable snippet."""
        out = self.run_jsc_script("""
            var invalid = window.ENERGY_DICTIONARY.filter(function(t) {
                return !t.term_en || !t.term_he || !t.category || !t.category_he || !t.snippet;
            });
            print(JSON.stringify(invalid.length));
        """)
        self.assertEqual(json.loads(out), 0)

    def test_m3_21_search_energy_dictionary_by_query(self):
        """TC-M3-21: searchEnergyDictionary filters correctly by English and Hebrew queries."""
        out = self.run_jsc_script("""
            var r1 = window.searchEnergyDictionary('Bifacial', 'all');
            var r2 = window.searchEnergyDictionary('נומינציה', 'all');
            var r3 = window.searchEnergyDictionary('xyznonexistent', 'all');
            print(JSON.stringify({ r1: r1.length, r2: r2.length, r3: r3.length }));
        """)
        res = json.loads(out)
        self.assertGreaterEqual(res["r1"], 1)
        self.assertGreaterEqual(res["r2"], 1)
        self.assertEqual(res["r3"], 0)

    def test_m3_22_search_energy_dictionary_by_category(self):
        """TC-M3-22: searchEnergyDictionary filters correctly by category."""
        categories = ["gas", "renewables", "electrical", "automation", "safety"]
        for cat in categories:
            out = self.run_jsc_script(f"""
                var res = window.searchEnergyDictionary('', '{cat}');
                print(JSON.stringify(res.length));
            """)
            count = json.loads(out)
            self.assertGreaterEqual(count, 1, f"Expected terms in category: {cat}")

    # --- 5. DOM Template & CSS Integrity ---

    def test_m3_23_index_template_has_writer_components(self):
        """TC-M3-23: index.html has complete interactive AI Writer workbench components."""
        html = self.html_file.read_text(encoding="utf-8")
        self.assertIn('id="studioModuleWriter"', html)
        self.assertIn('id="btnToneTechnical"', html)
        self.assertIn('id="btnToneOperational"', html)
        self.assertIn('id="btnToneStrategic"', html)
        self.assertIn('id="writerRawInput"', html)
        self.assertIn('id="writerTransformedOutput"', html)
        self.assertIn('id="btnTransformBullet"', html)
        self.assertIn('id="btnValidateGrammar"', html)
        self.assertIn('id="btnCopyBullet"', html)
        self.assertIn('id="btnApplyToCv"', html)
        self.assertIn('id="grammarScoreBadge"', html)
        self.assertIn('id="indActiveVerb"', html)
        self.assertIn('id="indMetric"', html)
        self.assertIn('id="indScope"', html)
        self.assertIn('id="indTone"', html)
        self.assertIn('id="dictSearchInput"', html)
        self.assertIn('id="dictCardsGrid"', html)

    def test_m3_24_css_has_writer_glassmorphism_rules(self):
        """TC-M3-24: dashboard.css defines all required AI Writer and Tone styling classes."""
        css = self.css_file.read_text(encoding="utf-8")
        self.assertIn('.writer-workspace-content', css)
        self.assertIn('.writer-tone-btn', css)
        self.assertIn('.writer-formula-banner', css)
        self.assertIn('.writer-workbench', css)
        self.assertIn('.writer-card-column', css)
        self.assertIn('.writer-output-box', css)
        self.assertIn('.writer-analysis-card', css)
        self.assertIn('.writer-score-badge', css)
        self.assertIn('.writer-dictionary-section', css)
        self.assertIn('.writer-dict-card', css)

    def test_m3_25_zero_emoji_compliance(self):
        """TC-M3-25: Static scan confirms 0 emojis in modified source files."""
        scanner_script = PROJECT_ROOT / "scripts" / "validate_zero_emoji.py"
        proc = subprocess.run(
            ["python3", str(scanner_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(proc.returncode, 0, f"Zero emoji audit failed:\n{proc.stdout}\n{proc.stderr}")
        self.assertIn("[ZERO-EMOJI AUDIT PASSED]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
