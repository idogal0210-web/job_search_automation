"""
Adversarial Empirical Challenger Test Suite for Milestone 3:
AI Writer Grammar Validator & Bilingual Energy Dictionary Boundary Explorer.

Validates:
1. validateBulletGrammar Adversarial Challenges:
   - Passive phrasing (Hebrew & English) scores <= 30 and generates passive warning.
   - Passive phrasing with partial signals (metric only or scope only) scores <= 30 and generates passive warning.
   - Perfect bullets across Technical, Operational, and Strategic tones score >= 90 (100).
   - Boundary scoring: empty string, pure whitespace, single word, ultra-long strings (10,000+ chars),
     hyper-repetition, special characters, HTML/XSS injection strictly clamped between 0 and 100.
   - Correct detection of active verb, metric, scope, and tone.
2. searchEnergyDictionary Boundary Challenges:
   - Exact and partial Hebrew queries (terms, acronyms, descriptions).
   - Exact and partial English queries (acronyms, terms, technical concepts).
   - Mixed-case invariance (lower, UPPER, MixedCase).
   - Non-existent queries return empty array.
   - Category filtering across all 5 domain categories (gas, renewables, electrical, automation, safety).
   - Empty/whitespace query returns all items in category.
   - Non-existent categories return empty array.
   - Combined query + category filtering precision.
3. Phosphor Icon Glyph Conformance:
   - All Phosphor icon classes in #studioModuleWriter and writer JS code are valid glyphs in @phosphor-icons/web@2.1.1.
4. Strict Zero-Emoji Compliance:
   - scripts/validate_zero_emoji.py passes with 0 emojis.
"""

import json
import os
import re
import subprocess
import unittest
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSC_BIN = "/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc"


class TestMilestone3GrammarDictChallenger(unittest.TestCase):
    """Empirical challenge suite for M3 grammar validation and energy dictionary search."""

    @classmethod
    def setUpClass(cls):
        cls.js_file = PROJECT_ROOT / "frontend" / "js" / "dashboard.js"
        cls.html_file = PROJECT_ROOT / "frontend" / "templates" / "index.html"
        cls.css_file = PROJECT_ROOT / "frontend" / "css" / "dashboard.css"
        cls.docs_html = PROJECT_ROOT / "docs" / "index.html"
        cls.docs_js = PROJECT_ROOT / "docs" / "dashboard.js"

    def run_jsc(self, script_code: str) -> str:
        """Run JavaScript code inside JSC with dashboard.js loaded."""
        harness = """
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

        runner = harness + "\n" + js_src + "\n" + script_code
        proc = subprocess.run(
            [JSC_BIN, "-e", runner],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode != 0:
            raise RuntimeError(f"JSC Execution Failed (code {proc.returncode}):\n{proc.stderr}\nOutput:\n{proc.stdout}")
        return proc.stdout.strip()

    # =========================================================================
    # PART 1: validateBulletGrammar Adversarial Challenges
    # =========================================================================

    def test_challenge_passive_phrasing_scores_and_warnings(self):
        """Passive phrasing must score <= 30 and generate passive warning suggestion."""
        passive_samples = [
            "הייתי אחראי על",
            "הייתי אחראי על ניהול המשמרת",
            "הייתי מפעיל במתקן הגז",
            "עבדתי במתקן סולארי ובדקתי פאנלים",
            "עבדתי במשמרות לילה",
            "עשיתי בדיקות שגרתיות במתקן",
            "עשיתי נומינציות",
            "טיפלתי בתקלות שבר",
            "טיפלתי במערכות סולאריות",
            "לקחתי חלק בצוות התפעול",
            "עזרתי למנהל המשמרת",
            "אחראי על הפעלת המתקן",
            "אחריות על סגירת שסתומים",
            "I was responsible for routine maintenance",
            "Responsible for operations",
            "Worked on pipeline checks",
            "Helped senior engineers with calibration",
            "Assisted in emergency shutdown tests"
        ]

        for sample in passive_samples:
            out = self.run_jsc(f"""
                var res = window.validateBulletGrammar({json.dumps(sample)});
                print(JSON.stringify(res));
            """)
            res = json.loads(out)
            self.assertLessEqual(
                res["score"], 30,
                f"Passive bullet exceeded 30 points (got {res['score']}): {sample}"
            )
            self.assertFalse(
                res["hasActiveVerb"],
                f"Passive bullet falsely flagged as active verb: {sample}"
            )
            has_passive_warning = any(
                ("סביל" in s or "הייתי אחראי" in s or "עבדתי" in s)
                for s in res.get("suggestions", [])
            )
            self.assertTrue(
                has_passive_warning,
                f"Passive warning not found in suggestions for: {sample}. Got: {res.get('suggestions')}"
            )

    def test_challenge_passive_with_partial_signals_clamped_at_or_below_30(self):
        """Passive phrasing with either scope or metric alone must still score <= 30 and flag warning."""
        partial_passives = [
            # Passive + scope (PRMS) -> 20 base + 20 scope - 20 passive = 20 <= 30
            "הייתי אחראי על מערכת PRMS",
            # Passive + scope (SCADA) -> 20 base + 20 scope - 20 passive = 20 <= 30
            "עבדתי מול מערכות SCADA",
            # Passive + metric (24/7) -> 20 base + 30 metric - 20 passive = 30 <= 30
            "עבדתי במשמרות 24/7",
            # Passive + metric (100%) -> 20 base + 30 metric - 20 passive = 30 <= 30
            "I was responsible for 100% uptime"
        ]

        for sample in partial_passives:
            out = self.run_jsc(f"""
                var res = window.validateBulletGrammar({json.dumps(sample)});
                print(JSON.stringify(res));
            """)
            res = json.loads(out)
            self.assertLessEqual(
                res["score"], 30,
                f"Partial passive bullet exceeded 30 points (got {res['score']}): {sample}"
            )
            has_passive_warning = any(
                ("סביל" in s or "הייתי אחראי" in s or "עבדתי" in s)
                for s in res.get("suggestions", [])
            )
            self.assertTrue(has_passive_warning, f"Missing passive warning for: {sample}")

    def test_challenge_perfect_bullets_score_above_90(self):
        """Perfect bullets (Active verb + scope + metric) must score >= 90 across all tones."""
        perfect_samples = [
            # Technical Hebrew
            "ניטרתי לחצי צנרת במערך תחנות PRMS תוך שמירה על לחץ יעד של 45 bar.",
            "כיַילתי מכשירי מדידה במערכת SCADA להשגת רמת דיוק של 99.8%.",
            "כיילתי שסתומי בקרה במערך PRMS תוך עמידה בלחץ של 65 bar.",
            "חישבתי מפל לחצים בצנרת גז טבעי במערך SCADA תוך הפחתת סטיות ל-0.5%.",
            "אפיינתי מערכי פאנלים סולאריים מסוג Bifacial PV עם ממירי מתח בהספק 15MW.",
            "התקנתי בקרי PLC במערכות מתח גבוה HV תוך השגת 100% תאימות.",
            "תכננתי מערכי אגירת אנרגיה מסוג BESS בהספק 50MW לפי חוק החשמל.",
            "שדרגתי ערוצי טלמטריה במערכות DCS בתוך 48 שעות.",
            # Operational Hebrew
            "הובלתי משמרות 24/7 בחדר בקרה SCADA עם 0 תאונות LTI.",
            "תפעלתי מתקן הולכת גז בחירום מול נתג״ז עם 100% רציפות אספקה.",
            "ניהלתי תרחישי חירום במערך תחנות PRMS עם אפס תקלות השבתה.",
            "בלמתי אירועי דליפה במערכות ESD ללא נפגעים וב-0 אירועי בטיחות.",
            "אכפתי נוהל נעילה ותיוג LOTO במתקני מתח גבוה HV לאורך 3 שנים.",
            "שימשתי כגורם תפעולי מוביל במשמרות 24/7 לניהול מערכות PRMS עם 0 LTI.",
            # Strategic Hebrew
            "סנכרנתי בקשות נומינציה מול נתג״ז ואסדת FPSO תוך הבטחת 100% עמידה ביעדים.",
            "תיאמתי הזרמות גז יומיות מול נתג״ז במערכות SCADA בתוך 24 שעות.",
            "ייעלתי ממשקי עבודה מול אסדת הפקה ימית FPSO שהובילו לחיסכון של 12%.",
            "הכשרתי צוותי תפעול במערכי PRMS תוך הגעה ל-100% הסמכה.",
            "הטמעתי מערכות בקרה מבוזרות DCS במתקני אנרגיה בתוך 6 חודשים.",
            # English Perfect Bullets
            "Monitored 15 PRMS gas stations achieving 100% uptime with 0 LTI.",
            "Spearheaded 24/7 SCADA operations maintaining 45 bar gas pressure.",
            "Synchronized gas nomination schedules with INGL achieving 100% delivery.",
            "Calibrated HV transformers and inverters under strict zero harm standards.",
            "Engineered Bifacial PV arrays and BESS storage delivering 25MW.",
            "Operated DCS and PLC control rooms with zero downtime over 2 years."
        ]

        for sample in perfect_samples:
            out = self.run_jsc(f"""
                var res = window.validateBulletGrammar({json.dumps(sample)});
                print(JSON.stringify(res));
            """)
            res = json.loads(out)
            self.assertGreaterEqual(
                res["score"], 90,
                f"Perfect bullet scored below 90 (got {res['score']}): {sample}"
            )
            self.assertTrue(res["hasActiveVerb"], f"Active verb not detected: {sample}")
            self.assertTrue(res["hasMetric"], f"Metric not detected: {sample}")
            self.assertTrue(res["hasScope"], f"Scope not detected: {sample}")
            self.assertTrue(
                any("מצוין" in s for s in res.get("suggestions", [])),
                f"Praise suggestion not generated for perfect bullet: {sample}"
            )

    def test_challenge_boundary_scoring_strictly_clamped_0_to_100(self):
        """Score must be strictly clamped to [0, 100] across all boundary, adversarial and extreme inputs."""
        extreme_inputs = [
            "",                                  # empty string -> score 0
            "   ",                               # whitespace only -> score 0
            "\t\r\n\t",                          # tabs and newlines -> score 0
            "א",                                 # single letter
            "שלום",                              # single word
            "בדיקה כללית של מערכת ללא מדדים",    # arbitrary sentence without domain markers
            "...... !?!?!?!? ,,,, ;;;; ----",   # pure punctuation
            "<script>alert('xss')</script>",     # HTML injection
            "<div class='box'>ניטרתי PRMS 45 bar</div>",  # HTML with valid text
            "ניטרתי " * 100,                     # repeated active verb
            ("ניטרתי תחנות PRMS לחץ 45 bar 100% 24/7 0 LTI " * 20),  # hyper-dense max indicators
            ("הייתי עבדתי עשיתי טיפלתי לקחתי עזרתי אחראי " * 20),   # hyper-dense passive penalties
            "A" * 10000                          # 10,000 chars stress string
        ]

        for text in extreme_inputs:
            out = self.run_jsc(f"""
                var res = window.validateBulletGrammar({json.dumps(text)});
                print(JSON.stringify(res));
            """)
            res = json.loads(out)
            score = res.get("score")
            self.assertIsInstance(score, int, f"Score is not an integer: {score}")
            self.assertGreaterEqual(score, 0, f"Score below 0 ({score}) for input: {text[:40]}")
            self.assertLessEqual(score, 100, f"Score above 100 ({score}) for input: {text[:40]}")

            if not text.strip():
                self.assertEqual(score, 0, f"Empty or whitespace input must score 0, got {score}")

    # =========================================================================
    # PART 2: searchEnergyDictionary Adversarial Challenges
    # =========================================================================

    def test_challenge_dictionary_hebrew_queries(self):
        """Hebrew search finds correct terms by Hebrew term, acronym, or Hebrew description."""
        hebrew_tests = [
            ("נומינציה", ["Nomination"]),
            ("גז", ["PRMS", "Nomination", "FPSO", "INGL"]),
            ("סולארי", ["Bifacial PV", "Monofacial PV", "BESS", "Inverter"]),
            ("שנאי", ["Transformer"]),
            ("מתח גבוה", ["HV"]),
            ("מתח נמוך", ["LV"]),
            ("בטיחות", ["LTI", "Zero Harm", "ESD", "LOTO"]),
            ("נעילה ותיוג", ["LOTO"]),
            ("הפחתת לחץ", ["PRMS"]),
            ("אסדת הפקה", ["FPSO"]),
            ("אגירת אנרגיה", ["BESS"]),
            ("סקאדה", ["SCADA"])
        ]

        for query, expected_acronyms in hebrew_tests:
            out = self.run_jsc(f"""
                var res = window.searchEnergyDictionary({json.dumps(query)}, 'all');
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            found = json.loads(out)
            for exp in expected_acronyms:
                self.assertIn(
                    exp, found,
                    f"Hebrew query '{query}' did not find expected acronym '{exp}'. Found: {found}"
                )

    def test_challenge_dictionary_english_queries(self):
        """English search finds terms by acronym, English name, or sub-term."""
        english_tests = [
            ("PRMS", ["PRMS"]),
            ("SCADA", ["SCADA"]),
            ("Bifacial", ["Bifacial PV"]),
            ("Monofacial", ["Monofacial PV"]),
            ("BESS", ["BESS"]),
            ("Inverter", ["Inverter"]),
            ("Transformer", ["Transformer"]),
            ("HV", ["HV"]),
            ("LV", ["LV"]),
            ("LTI", ["LTI"]),
            ("Zero Harm", ["Zero Harm"]),
            ("ESD", ["ESD"]),
            ("Telemetry", ["Telemetry"]),
            ("LOTO", ["LOTO"]),
            ("DCS", ["DCS"]),
            ("FPSO", ["FPSO"]),
            ("INGL", ["INGL"]),
            ("PLC", ["PLC"]),
            ("HMI", ["HMI"]),
            ("Nomination", ["Nomination"])
        ]

        for query, expected_acronyms in english_tests:
            out = self.run_jsc(f"""
                var res = window.searchEnergyDictionary({json.dumps(query)}, 'all');
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            found = json.loads(out)
            for exp in expected_acronyms:
                self.assertIn(
                    exp, found,
                    f"English query '{query}' did not find expected acronym '{exp}'. Found: {found}"
                )

    def test_challenge_dictionary_mixed_case_invariance(self):
        """searchEnergyDictionary must be strictly case-insensitive for queries and categories."""
        case_variations = [
            ("prms", "PRMS"),
            ("Prms", "PRMS"),
            ("PRMS", "PRMS"),
            ("pRmS", "PRMS"),
            ("scada", "SCADA"),
            ("SCADA", "SCADA"),
            ("sCaDa", "SCADA"),
            ("bess", "BESS"),
            ("BESS", "BESS"),
            ("inverter", "Inverter"),
            ("INVERTER", "Inverter"),
            ("InVeRtEr", "Inverter"),
            ("zero harm", "Zero Harm"),
            ("ZERO HARM", "Zero Harm"),
            ("zErO hArM", "Zero Harm"),
            ("lti", "LTI"),
            ("LTI", "LTI"),
            ("loto", "LOTO"),
            ("LOTO", "LOTO")
        ]

        for q_input, expected_acronym in case_variations:
            out = self.run_jsc(f"""
                var res = window.searchEnergyDictionary({json.dumps(q_input)}, 'all');
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            found = json.loads(out)
            self.assertIn(
                expected_acronym, found,
                f"Mixed-case query '{q_input}' failed to match '{expected_acronym}'."
            )

    def test_challenge_dictionary_non_existent_terms(self):
        """Non-existent terms and invalid queries must return an empty list gracefully."""
        invalid_queries = [
            "QuantumComputing",
            "xyz123nonexistent",
            "ReactJS",
            "ReduxThunk",
            "!@#$%^&*()_+",
            "MachineLearningDeepNeuralNetwork"
        ]

        for q in invalid_queries:
            out = self.run_jsc(f"""
                var res = window.searchEnergyDictionary({json.dumps(q)}, 'all');
                print(JSON.stringify(res.length));
            """)
            count = json.loads(out)
            self.assertEqual(count, 0, f"Query '{q}' should return 0 results, got {count}")

    def test_challenge_dictionary_category_filters(self):
        """Category filters must accurately partition terms with zero leaks or omissions."""
        categories = {
            "gas": ["PRMS", "Nomination", "FPSO", "INGL"],
            "renewables": ["Bifacial PV", "Monofacial PV", "BESS"],
            "electrical": ["Inverter", "Transformer", "HV", "LV"],
            "automation": ["SCADA", "PLC", "HMI", "Telemetry", "DCS"],
            "safety": ["LTI", "Zero Harm", "ESD", "LOTO"]
        }

        total_partition_count = sum(len(terms) for terms in categories.values())
        self.assertEqual(total_partition_count, 20, "Total categorized terms must be exactly 20")

        for cat, expected_terms in categories.items():
            # Test lowercase category
            out_lower = self.run_jsc(f"""
                var res = window.searchEnergyDictionary('', '{cat}');
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            terms_lower = json.loads(out_lower)
            self.assertEqual(
                sorted(terms_lower), sorted(expected_terms),
                f"Mismatch in category '{cat}' filter results"
            )

            # Test uppercase category
            out_upper = self.run_jsc(f"""
                var res = window.searchEnergyDictionary('', '{cat.upper()}');
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            terms_upper = json.loads(out_upper)
            self.assertEqual(
                sorted(terms_upper), sorted(expected_terms),
                f"Category '{cat.upper()}' casing was not respected"
            )

        # Test non-existent category
        out_invalid_cat = self.run_jsc("""
            var res = window.searchEnergyDictionary('', 'nonexistent_cat_999');
            print(JSON.stringify(res.length));
        """)
        self.assertEqual(json.loads(out_invalid_cat), 0)

    def test_challenge_dictionary_query_and_category_cross_filtering(self):
        """Cross-filtering query and category simultaneously must produce exact intersections."""
        cross_tests = [
            ("PV", "renewables", ["Bifacial PV", "Monofacial PV"]),
            ("PV", "gas", []),
            ("SCADA", "automation", ["SCADA"]),
            ("SCADA", "safety", []),
            ("PRMS", "gas", ["PRMS"]),
            ("PRMS", "electrical", []),
            ("Zero", "safety", ["LTI", "Zero Harm"]),
            ("Harm", "safety", ["Zero Harm"]),
            ("Zero", "gas", [])
        ]

        for query, cat, expected in cross_tests:
            out = self.run_jsc(f"""
                var res = window.searchEnergyDictionary({json.dumps(query)}, {json.dumps(cat)});
                print(JSON.stringify(res.map(function(t) {{ return t.acronym; }})));
            """)
            found = json.loads(out)
            self.assertEqual(
                sorted(found), sorted(expected),
                f"Cross-filter query='{query}' cat='{cat}' mismatch. Got: {found}, Expected: {expected}"
            )

    # =========================================================================
    # PART 3: Phosphor Icon Glyph Conformance (@phosphor-icons/web@2.1.1)
    # =========================================================================

    def test_challenge_phosphor_icons_conformance_with_web_v2_1_1(self):
        """Verify that every icon class used in #studioModuleWriter and writer JS is valid in @phosphor-icons/web@2.1.1."""
        cdn_urls = [
            "https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/duotone/style.css",
            "https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/bold/style.css",
            "https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css"
        ]

        valid_glyphs = set()
        for url in cdn_urls:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
                matches = re.findall(r"\.ph-([a-z0-9-]+):before", content)
                valid_glyphs.update(matches)

        self.assertGreater(len(valid_glyphs), 1400, "Failed to fetch comprehensive Phosphor glyph set")

        # 1. Extract icons from #studioModuleWriter in frontend/templates/index.html
        html = self.html_file.read_text(encoding="utf-8")
        writer_section_match = re.search(
            r'<section id="studioModuleWriter".*?</section>', html, re.DOTALL
        )
        self.assertIsNotNone(writer_section_match, "#studioModuleWriter not found in index.html")
        writer_html = writer_section_match.group(0)

        html_classes = re.findall(r'class=["\']([^"\']+)["\']', writer_html)
        writer_glyphs = set()
        for cls_str in html_classes:
            for token in cls_str.split():
                if token.startswith("ph-") and token not in (
                    "ph-duotone", "ph-bold", "ph-fill", "ph-regular", "ph-light", "ph-thin"
                ):
                    glyph = token[3:]  # strip 'ph-'
                    writer_glyphs.add((glyph, f"HTML class='{token}'"))

        # 2. Extract icons from writer section in frontend/js/dashboard.js
        js_src = self.js_file.read_text(encoding="utf-8")
        writer_js_match = re.search(
            r'CAREER STUDIO: MILESTONE 3.*?window\.initWriterModule = initWriterModule;',
            js_src, re.DOTALL
        )
        self.assertIsNotNone(writer_js_match, "Writer JS section not found in dashboard.js")
        writer_js = writer_js_match.group(0)

        # Match icon strings like icon: "ph-gear-six", "ph-check-circle", etc.
        js_icon_matches = re.findall(r'ph-([a-z0-9-]+)', writer_js)
        for g in js_icon_matches:
            if g not in ("duotone", "bold", "fill", "regular", "light", "thin"):
                writer_glyphs.add((g, f"JS icon ph-{g}"))

        self.assertGreaterEqual(len(writer_glyphs), 25, "Expected at least 25 distinct Phosphor icon glyphs")

        invalid_glyphs = []
        for glyph, location in sorted(writer_glyphs):
            if glyph not in valid_glyphs:
                invalid_glyphs.append(f"{glyph} ({location})")

        self.assertEqual(
            len(invalid_glyphs), 0,
            f"Found invalid Phosphor icons not present in @phosphor-icons/web@2.1.1: {invalid_glyphs}"
        )

    # =========================================================================
    # PART 4: Zero Emoji Static Compliance
    # =========================================================================

    def test_challenge_zero_emoji_script_audit(self):
        """scripts/validate_zero_emoji.py must pass with exit code 0."""
        scanner_script = PROJECT_ROOT / "scripts" / "validate_zero_emoji.py"
        proc = subprocess.run(
            ["python3", str(scanner_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.assertEqual(
            proc.returncode, 0,
            f"Zero-emoji audit failed with exit code {proc.returncode}:\n{proc.stdout}\n{proc.stderr}"
        )
        self.assertIn("[ZERO-EMOJI AUDIT PASSED]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
