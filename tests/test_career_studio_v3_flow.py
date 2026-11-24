#!/usr/bin/env python3
"""
tests/test_career_studio_v3_flow.py

Focused unit and behavioral tests for Career Studio v3.0 (docs/CAREER_STUDIO_V3_SPEC.md):
- Single Context Header + 4-stage chronological stepper (Steps 1-4 unlocked and accessible).
- Contextual 55/45 split workbench: Live A4 Preview in Steps 1-2, Job Brief Card in Steps 3-4,
  and synchronized mobile <dialog> mode switching.
- Step 3: LinkedIn Headline, About, Skills, Recruiter outreach message, Copy handlers,
  Direct Apply green CTA, and Proceed to Step 4 button.
- Step 4: Domain-matched question bank (energy, solar_bess, gas, scada, uav, pm),
  4-tag STAR breakdown (S/T/A/R), online bridge evaluation (/api/interview/evaluate),
  and honest local mode fallback indicator.
- CSS & Hygiene invariants: zero emojis, zero backdrop-filter, zero transition: all, zero 100vw.
"""

import json
import re
import unittest
from pathlib import Path

from bs4 import BeautifulSoup
from scripts.validate_zero_emoji import scan_file
from tests.js_runner import run_js, skip_if_no_js

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestCareerStudioV3Flow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_path = PROJECT_ROOT / "frontend" / "templates" / "index.html"
        cls.css_path = PROJECT_ROOT / "frontend" / "css" / "dashboard.css"
        cls.js_path = PROJECT_ROOT / "frontend" / "js" / "dashboard.js"
        cls.html_text = cls.html_path.read_text(encoding="utf-8")
        cls.css_text = cls.css_path.read_text(encoding="utf-8")
        cls.js_text = cls.js_path.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html_text, "html.parser")

    def test_01_four_step_dom_scaffolding_and_stepper_unlocked(self):
        """All 4 stepper items and 4 panes exist in index.html without disabled locks."""
        for step in range(1, 5):
            item = self.soup.find(id=f"studioStepItem{step}")
            self.assertIsNotNone(item, f"Missing #studioStepItem{step}")
            self.assertNotIn("disabled", item.get("class", []), f"Step {step} must not be disabled")
            btn = item.find("button")
            self.assertIsNotNone(btn)
            self.assertFalse(btn.has_attr("disabled"), f"Step {step} button must be enabled")

            pane = self.soup.find(id=f"studioPaneStep{step}")
            self.assertIsNotNone(pane, f"Missing #studioPaneStep{step}")

        # Side column holds both Live A4 Preview (Steps 1-2) and Job Brief Card (Steps 3-4)
        self.assertIsNotNone(self.soup.find(id="studioA4PreviewCard"))
        self.assertIsNotNone(self.soup.find(id="studioJobBriefCard"))

        # Mobile preview dialog holds both A4 wrap and Job Brief wrap without role="dialog"
        dlg = self.soup.find(id="studioMobilePreviewDialog")
        self.assertIsNotNone(dlg)
        self.assertEqual(dlg.name, "dialog")
        self.assertFalse(dlg.has_attr("role"), "Native <dialog> must not set role='dialog'")
        self.assertFalse(dlg.has_attr("aria-modal"), "Native <dialog> must not set aria-modal")
        self.assertIsNotNone(self.soup.find(id="studioMobileA4Wrap"))
        self.assertIsNotNone(self.soup.find(id="studioMobileJobBriefWrap"))

    def test_02_step3_and_step4_controls_present_in_dom(self):
        """Step 3 LinkedIn/Apply and Step 4 STAR simulator controls exist with proper IDs."""
        step3_ids = (
            "studioLinkedinHeadline",
            "studioLinkedinAbout",
            "studioLinkedinSkillsList",
            "studioLinkedinSkillsText",
            "studioRecruiterMessage",
            "studioDirectApplyLink",
            "studioBtnProceedToStep4",
        )
        for el_id in step3_ids:
            self.assertIsNotNone(self.soup.find(id=el_id), f"Missing Step 3 element #{el_id}")

        # Verify Copy buttons for Headline, About, Skills, and Recruiter message
        step3_pane = self.soup.find(id="studioPaneStep3")
        copy_btns = step3_pane.find_all("button", onclick=re.compile(r"copyStudioFieldText"))
        self.assertEqual(len(copy_btns), 4, "Step 3 must provide 4 Copy buttons (Headline, About, Skills, Outreach)")

        step4_ids = (
            "studioInterviewQuestionTitle",
            "studioStarAnswerInput",
            "studioStarEvalModeBadge",
            "studioStarEvalModeText",
            "studioBtnEvaluateStar",
            "studioStarTotalScore",
            "starCardSituation",
            "starCardTask",
            "starCardAction",
            "starCardResult",
            "starScoreSituation",
            "starScoreTask",
            "starScoreAction",
            "starScoreResult",
        )
        for el_id in step4_ids:
            self.assertIsNotNone(self.soup.find(id=el_id), f"Missing Step 4 element #{el_id}")

        domain_pills = self.soup.select("#studioPaneStep4 .studio-domain-pill[data-domain]")
        domains = {p.get("data-domain") for p in domain_pills}
        self.assertEqual(domains, {"energy", "solar_bess", "gas", "scada", "uav", "pm"})

    def test_03_css_invariants_zero_forbidden_properties_and_brace_balance(self):
        """Stylesheet preserves brace depth 0 and avoids backdrop-filter, transition: all, and 100vw."""
        depth = sum(line.count("{") - line.count("}") for line in self.css_text.splitlines())
        self.assertEqual(depth, 0, "CSS brace depth must equal 0")
        self.assertNotIn("backdrop-filter:", self.css_text)
        self.assertIsNone(re.search(r"transition\s*:\s*all\b", self.css_text))
        self.assertIsNone(re.search(r"\b100vw\b", self.css_text))
        self.assertIn("grid-template-columns: 55fr 45fr;", self.css_text)

    def test_04_js_four_step_transitions_side_column_linkedin_and_star_evaluation(self):
        """Behavioral JS execution across Steps 1 -> 2 -> 3 -> 4, side-column swap, LinkedIn, and STAR."""
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
        window.sessionStorage = window.localStorage;
        var localStorage = window.localStorage;
        var sessionStorage = window.sessionStorage;
        if (typeof globalThis.setTimeout !== 'function') {{
          globalThis.setTimeout = function() {{ return 1; }};
        }}
        if (typeof globalThis.clearTimeout !== 'function') {{
          globalThis.clearTimeout = function() {{}};
        }}

        var __copied = [];
        globalThis.navigator = {{
          clipboard: {{
            writeText: function(txt) {{
              __copied.push(txt);
              return Promise.resolve();
            }}
          }}
        }};

        function makeClassList(initial) {{
          var set = {{}};
          (initial || []).forEach(function(c) {{ set[c] = true; }});
          return {{
            add: function() {{
              for (var i = 0; i < arguments.length; i++) set[arguments[i]] = true;
            }},
            remove: function() {{
              for (var i = 0; i < arguments.length; i++) delete set[arguments[i]];
            }},
            toggle: function(c, force) {{
              if (force === undefined) {{
                set[c] = !set[c];
              }} else if (force) {{
                set[c] = true;
              }} else {{
                delete set[c];
              }}
              return Boolean(set[c]);
            }},
            contains: function(c) {{ return Boolean(set[c]); }}
          }};
        }}

        function makeEl(id, classes) {{
          var el = {{
            id: id,
            value: '',
            textContent: '',
            innerText: '',
            innerHTML: '',
            className: (classes || []).join(' '),
            disabled: false,
            checked: true,
            open: false,
            dir: 'rtl',
            style: {{ display: '' }},
            attrs: {{}},
            children: [],
            options: [],
            classList: makeClassList(classes),
            setAttribute: function(k, v) {{ this.attrs[k] = String(v); }},
            getAttribute: function(k) {{ return this.attrs[k] || null; }},
            removeAttribute: function(k) {{ delete this.attrs[k]; }},
            appendChild: function(child) {{ this.children.push(child); return child; }},
            replaceChildren: function() {{
              this.children = Array.prototype.slice.call(arguments);
            }},
            querySelector: function() {{ return this._innerBtn || null; }},
            addEventListener: function() {{}},
            focus: function() {{}},
            showModal: function() {{ this.open = true; }},
            close: function() {{ this.open = false; }}
          }};
          return el;
        }}

        var __dom = {{}};
        var ids = [
          'radarWorkspace', 'careerStudioWorkspace', 'modeSwitchRadar', 'modeSwitchStudio',
          'studioJobSelect', 'studioActiveJobTitle', 'studioActiveCompanyBadge', 'studioOverallScoreVal',
          'studioBridgeDot', 'studioBridgeLabel', 'studioCvFileNameLabel',
          'studioMobilePreviewBtn', 'studioMobilePreviewIcon', 'studioMobilePreviewLabel',
          'studioMobilePreviewDialog', 'studioMobilePreviewTitle', 'studioMobilePreviewSubtitle',
          'studioMobileDialogIcon', 'studioMobileA4Wrap', 'studioMobileJobBriefWrap', 'studioMobileA4Sheet',
          'studioPaneStep1', 'studioPaneStep2', 'studioPaneStep3', 'studioPaneStep4',
          'studioStepItem1', 'studioStepItem2', 'studioStepItem3', 'studioStepItem4',
          'studioA4PreviewCard', 'studioJobBriefCard', 'studioLiveA4Sheet', 'studioDocWordCount',
          'studioJobTitleInput', 'studioJobCompanyInput', 'studioJobUrlInput', 'studioJobDescriptionInput',
          'studioRunResearchCheckbox', 'studioBtnAnalyzeAts', 'studioBlacklistBanner', 'studioBlacklistMessage',
          'studioThresholdsContainer', 'studioPassingThresholdsCount', 'studioPassingThresholdsList',
          'studioBlockingAlert', 'studioGapsContainer', 'studioGapsCountBadge',
          'gapListBlocking', 'gapCountBlocking', 'gapListImportant', 'gapCountImportant',
          'gapListNiceToHave', 'gapCountNiceToHave', 'studioResearchDetails', 'studioResearchSummaryText',
          'studioBtnProceedToStep2', 'studioBtnProceedToStep3', 'studioBtnProceedToStep4',
          'studioKeywordsChipCloud', 'studioInjectKeywordsCount', 'studioBulletInput',
          'studioBulletResultBox', 'studioBulletResultText', 'studioBtnUpgradeBullet', 'studioBtnGeneratePackage',
          'studioTabPreviewCv', 'studioTabPreviewCoverLetter',
          'studioBriefJobTitle', 'studioBriefCompany', 'studioBriefLocation', 'studioBriefScore',
          'studioBriefDescription', 'studioBriefKeywords', 'studioBriefGapsList', 'studioBriefExternalLink',
          'studioLinkedinHeadline', 'studioLinkedinAbout', 'studioLinkedinSkillsList',
          'studioLinkedinSkillsText', 'studioRecruiterMessage', 'studioDirectApplyLink', 'studioApplyUrlHint',
          'studioQuestionDomainBadge', 'studioQuestionCounter', 'studioInterviewQuestionTitle',
          'studioInterviewQuestionFocus', 'studioStarAnswerInput', 'studioStarEvalModeBadge',
          'studioStarEvalModeText', 'studioBtnEvaluateStar', 'studioStarTotalScore', 'studioStarSourceTag',
          'starCardSituation', 'starCardTask', 'starCardAction', 'starCardResult',
          'starScoreSituation', 'starScoreTask', 'starScoreAction', 'starScoreResult',
          'starFeedbackSituation', 'starFeedbackTask', 'starFeedbackAction', 'starFeedbackResult',
          'studioStarGoldenBox', 'studioStarGoldenText', 'studioStarTipsList',
          'toast', 'toastIcon', 'toastMsg'
        ];
        ids.forEach(function(id) {{
          __dom[id] = makeEl(id, []);
          if (id.indexOf('studioStepItem') === 0) {{
            __dom[id]._innerBtn = makeEl(id + '_btn', ['studio-step-btn']);
          }}
        }});

        var __domainPills = ['energy', 'solar_bess', 'gas', 'scada', 'uav', 'pm'].map(function(d) {{
          var p = makeEl('pill_' + d, ['studio-domain-pill']);
          p.setAttribute('data-domain', d);
          return p;
        }});

        var __bridgeOnline = false;
        globalThis.fetch = function(url, opts) {{
          if (!__bridgeOnline) {{
            return Promise.reject(new Error('offline'));
          }}
          if (String(url).indexOf('/api/session') !== -1) {{
            return Promise.resolve({{
              ok: true,
              status: 200,
              json: function() {{ return Promise.resolve({{ token: 'tok_test_123' }}); }}
            }});
          }}
          if (String(url).indexOf('/api/interview/evaluate') !== -1) {{
            return Promise.resolve({{
              ok: true,
              status: 200,
              json: function() {{
                return Promise.resolve({{
                  ok: true,
                  source: 'gemini',
                  evaluation: {{
                    total_score: 91,
                    situation_score: 18,
                    situation_feedback: 'זירת מתקן סולארי ברורה.',
                    task_score: 19,
                    task_feedback: 'הוגדר יעד החזרת ממיר לעבודה.',
                    action_score: 36,
                    action_feedback: 'בידוד סטרינג ותיאום ב-SCADA.',
                    result_score: 18,
                    result_feedback: 'חזרה ל-100% תפוקה.',
                    golden_answer: 'במשמרת בקרה איתרתי תקלת ממיר וביצעתי בידוד מבוקר.',
                    improvement_tips: ['לציין משך השבתה בדקות.']
                  }}
                }});
              }}
            }});
          }}
          return Promise.reject(new Error('not mocked'));
        }};

        globalThis.__INLINE_JOBS_FALLBACK__ = [
          {{
            link: 'https://enlightenergy.com/careers/pv-bess-ops',
            title: 'מהנדס/ת תפעול ובקרה סולאר ו-BESS',
            company: 'Enlight Renewable Energy',
            location: 'ראש העין',
            base_match_score: 90,
            match_score: 90,
            sector_key: 'solar',
            job_summary: 'בקרה ותפעול מתקני PV ואגירת אנרגיה BESS מול SCADA.',
            company_requirements: 'הנדסאי מכונות או חשמל, ניסיון ב-SCADA.',
            fit_gaps: 'יתרון לרישיון חשמלאי מוסמך'
          }}
        ];

        var document = {{
          documentElement: makeEl('html', []),
          body: makeEl('body', []),
          activeElement: null,
          addEventListener: function() {{}},
          removeEventListener: function() {{}},
          createElement: function(tag) {{ return makeEl(tag, []); }},
          createTextNode: function(txt) {{ return {{ textContent: String(txt) }}; }},
          getElementById: function(id) {{ return __dom[id] || null; }},
          querySelector: function() {{ return null; }},
          querySelectorAll: function(sel) {{
            if (sel.indexOf('.studio-domain-pill') !== -1) return __domainPills;
            return [];
          }}
        }};

        {self.js_text}

        (async function() {{
          // 1. Switch to Studio and select Solar/BESS job
          window.switchDashboardAppMode('studio');
          window.onStudioJobSelectChange('https://enlightenergy.com/careers/pv-bess-ops');

          var step1SideA4 = __dom.studioA4PreviewCard.style.display;
          var step1SideBrief = __dom.studioJobBriefCard.style.display;

          // 2. Run offline fallback ATS analysis on Step 1 -> proceed to Step 2
          await window.runStudioAtsAnalysis();
          window.proceedToStudioStep2();
          var step2SideA4 = __dom.studioA4PreviewCard.style.display;
          var step2SideBrief = __dom.studioJobBriefCard.style.display;

          // 3. Proceed to Step 3: side column must swap to Job Brief Card
          window.proceedToStudioStep3();
          var step3PaneVis = __dom.studioPaneStep3.style.display;
          var step3SideA4 = __dom.studioA4PreviewCard.style.display;
          var step3SideBrief = __dom.studioJobBriefCard.style.display;
          var mobileBtnStep3 = __dom.studioMobilePreviewLabel.textContent;
          var headlineVal = __dom.studioLinkedinHeadline.value;
          var skillsVal = __dom.studioLinkedinSkillsText.value;
          var applyHref = __dom.studioDirectApplyLink.getAttribute('href');
          var applyDisabled = __dom.studioDirectApplyLink.classList.contains('is-disabled');

          window.copyStudioFieldText('studioLinkedinHeadline', 'copied');
          window.openStudioMobilePreview();
          var mobileBriefVisInStep3 = __dom.studioMobileJobBriefWrap.style.display;
          var mobileA4VisInStep3 = __dom.studioMobileA4Wrap.style.display;
          window.closeStudioMobilePreview();

          // 4. Proceed to Step 4: verify auto-detected solar_bess domain, offline STAR eval, then online bridge eval
          window.proceedToStudioStep4();
          var step4PaneVis = __dom.studioPaneStep4.style.display;
          var step4SideBrief = __dom.studioJobBriefCard.style.display;
          var domainBadge = __dom.studioQuestionDomainBadge.textContent;

          window.loadSampleStarOutline();
          var localEv = await window.evaluateStudioStarAnswer();
          var offlineBadgeMode = __dom.studioStarEvalModeBadge.className;
          var offlineSourceTag = __dom.studioStarSourceTag.textContent;

          // Switch bridge online and re-evaluate
          __bridgeOnline = true;
          var onlineEv = await window.evaluateStudioStarAnswer();
          var onlineBadgeMode = __dom.studioStarEvalModeBadge.className;
          var onlineTotalText = __dom.studioStarTotalScore.textContent;

          print(JSON.stringify({{
            step1SideA4: step1SideA4,
            step1SideBrief: step1SideBrief,
            step2SideA4: step2SideA4,
            step2SideBrief: step2SideBrief,
            step3PaneVis: step3PaneVis,
            step3SideA4: step3SideA4,
            step3SideBrief: step3SideBrief,
            mobileBtnStep3: mobileBtnStep3,
            hasHeadline: headlineVal.indexOf('מהנדס/ת תפעול ובקרה סולאר ו-BESS') !== -1,
            hasSkills: skillsVal.length > 10,
            applyHref: applyHref,
            applyDisabled: applyDisabled,
            copiedCount: __copied.length,
            mobileBriefVisInStep3: mobileBriefVisInStep3,
            mobileA4VisInStep3: mobileA4VisInStep3,
            step4PaneVis: step4PaneVis,
            step4SideBrief: step4SideBrief,
            domainBadge: domainBadge,
            localTotal: localEv.total_score,
            offlineBadgeMode: offlineBadgeMode,
            offlineSourceTag: offlineSourceTag,
            onlineTotal: onlineEv.total_score,
            onlineBadgeMode: onlineBadgeMode,
            onlineTotalText: onlineTotalText
          }}));
        }})().catch(function(err) {{
          print(JSON.stringify({{ __error: String(err && err.stack || err) }}));
        }});
        """
        proc = run_js(harness)
        self.assertEqual(proc.returncode, 0, f"JS harness failed:\n{proc.stderr}\n{proc.stdout}")
        lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip().startswith("{")]
        self.assertTrue(lines, f"Expected JSON output from harness, got: {proc.stdout}")
        data = json.loads(lines[-1])
        self.assertNotIn("__error", data, f"JS runtime threw error: {data.get('__error')}")

        # Steps 1-2 keep A4 visible and Job Brief hidden
        self.assertNotEqual(data["step1SideA4"], "none")
        self.assertEqual(data["step1SideBrief"], "none")
        self.assertEqual(data["step2SideA4"], "flex")
        self.assertEqual(data["step2SideBrief"], "none")

        # Step 3 shows Step 3 pane and swaps side column + mobile dialog to Job Brief
        self.assertEqual(data["step3PaneVis"], "block")
        self.assertEqual(data["step3SideA4"], "none")
        self.assertEqual(data["step3SideBrief"], "flex")
        self.assertEqual(data["mobileBtnStep3"], "תמצית משרה")
        self.assertTrue(data["hasHeadline"])
        self.assertTrue(data["hasSkills"])
        self.assertEqual(data["applyHref"], "https://enlightenergy.com/careers/pv-bess-ops")
        self.assertFalse(data["applyDisabled"])
        self.assertEqual(data["copiedCount"], 1)
        self.assertEqual(data["mobileBriefVisInStep3"], "block")
        self.assertEqual(data["mobileA4VisInStep3"], "none")

        # Step 4 shows Step 4 pane, keeps Job Brief in side column, selects Solar/BESS domain, and evaluates STAR
        self.assertEqual(data["step4PaneVis"], "block")
        self.assertEqual(data["step4SideBrief"], "flex")
        self.assertEqual(data["domainBadge"], "סולאר ו-BESS")
        self.assertGreaterEqual(data["localTotal"], 70)
        self.assertIn("offline", data["offlineBadgeMode"])
        self.assertIn("מקומי", data["offlineSourceTag"])
        self.assertEqual(data["onlineTotal"], 91)
        self.assertIn("online", data["onlineBadgeMode"])
        self.assertEqual(data["onlineTotalText"], "91/100")

    def test_05_zero_emoji_in_v3_test_file(self):
        """This test module strictly adheres to zero-emoji rules."""
        violations = scan_file(Path(__file__))
        self.assertEqual(len(violations), 0, f"Emoji violations found: {violations}")


if __name__ == "__main__":
    unittest.main()
