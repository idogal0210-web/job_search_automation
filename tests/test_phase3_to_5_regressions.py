"""
Regression tests for Phases 3, 4, and 5 of the Project & Career Studio Review:
- Finding 3: Inactive job detection (30-page HTML corpus, 2-signal rule, JSON-LD validThrough, job-check.js parity)
- Finding 4: Company name normalization, word-boundary logo backfill, and employer blacklist disambiguation
- Finding 5: Fit gaps word-boundary matching ('subscription' != 'bsc'), PII-free public strings, non-destructive reasoning
- Finding 2 & Section 3: project_hygiene.py protection enforcement, ast.parse without pycache, secret patterns, exact deps
- Finding 6 & Section 3: evaluate_dataset.py f1=0.0, stage metrics, stratified ledger sampling, expanded zero-emoji ranges
- Phase 5: main.py email outbox idempotency, unified final_status, and latest_run.json quality metrics
"""

import json
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import main
from scripts.backfill_company_logos import find_domain_for_company, find_local_logo_for_company
from scripts.evaluate_dataset import compute_metrics, evaluate_dataset_file, sample_from_archive
from scripts.project_hygiene import (
    _parse_requirement_packages,
    is_protected,
    scan_project,
    scan_secrets,
    validate_integrity,
)
from scripts.scan_inactive_jobs import CLOSURE_CONFIG, _valid_through_expired, classify_job_html
from scripts.update_job_gaps_and_reasoning import analyze_fit_gaps, update_job_record_in_place
from scripts.validate_zero_emoji import check_text
from src.company_matcher import company_tokens_match, deduplicate_employer_list, normalize_company_name
from src.fetchers import RunHealth
from src.pipeline import final_status, run_report
from tools.cv_tailor.src.utils import check_employer_blacklist

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestFinding3InactiveJobDetectionAndCorpus(unittest.TestCase):
    def test_30_page_html_regression_corpus(self):
        """
        30-page HTML regression corpus:
        - 18 active pages with tricky false-positive traps (must all classify as 'active')
        - 12 genuinely closed/expired pages across ATS and generic sites (must all classify as 'inactive')
        """
        active_corpus = [
            # 1. SPA React bundle with 404/closed strings inside <script>
            (
                "https://careers.acme-energy.com/jobs/101",
                """<html><head><title>Solar Field Engineer</title>
                <script>window.__ROUTES__ = {"404": "Page not found", "closed": "This job is no longer available", "cls": "closed-job__flavor"};</script>
                </head><body><main><h1>Solar Field Engineer</h1><p>Join our solar PV commissioning team.</p><button>Apply Now</button></main></body></html>""",
            ),
            # 2. Vue/HTML <template> containing 404 and closed banners
            (
                "https://careers.acme-energy.com/jobs/102",
                """<html><body><template id="err-tpl"><h1>Page not found</h1><p>No longer accepting applications</p></template>
                <main><h1>SCADA Control Room Operator</h1><p>Operate high-voltage substations.</p><button>Apply Now</button></main></body></html>""",
            ),
            # 3. Hebrew footer with 'פג תוקף'
            (
                "https://jobs.israel-power.co.il/role/103",
                """<html><body><main><h1>טכנאי מערכות אנרגיה</h1><p>תחזוקת מערכות אגירת אנרגיה בשטח.</p><button>הגש מועמדות</button></main>
                <footer><p>כל הזכויות שמורות. אם פג תוקף החיבור שלך, התחבר מחדש.</p></footer></body></html>""",
            ),
            # 4. Navigation bar mentioning 'no longer open'
            (
                "https://careers.acme-energy.com/jobs/104",
                """<html><body><nav><a href="/archive">Positions no longer open</a></nav>
                <main><h1>Mechanical Commissioning Lead</h1><p>Lead gas turbine testing.</p><button>Apply Now</button></main></body></html>""",
            ),
            # 5. Sidebar related-jobs with closed text
            (
                "https://careers.acme-energy.com/jobs/105",
                """<html><body><main><h1>UAV Integration Technician</h1><p>Assemble and test drones.</p><button>Apply Now</button></main>
                <aside class="related-jobs"><p>This job is no longer available</p><p>המשרה נסגרה</p></aside></body></html>""",
            ),
            # 6. Div with recommended-jobs class containing closure phrase
            (
                "https://careers.acme-energy.com/jobs/106",
                """<html><body><main><h1>BESS Field Engineer</h1><p>Battery storage maintenance.</p><button>Apply Now</button></main>
                <div id="recommended-jobs"><span>No longer accepting applications</span></div></body></html>""",
            ),
            # 7. Active JobPosting JSON-LD + expired ItemList recommended jobs
            (
                "https://careers.acme-energy.com/jobs/107",
                """<html><head>
                <script type="application/ld+json">{"@type": "JobPosting", "title": "Solar Engineer", "validThrough": "2099-12-31"}</script>
                <script type="application/ld+json">{"@type": "ItemList", "itemListElement": [{"@type": "JobPosting", "validThrough": "2020-01-01"}]}</script>
                </head><body><main><h1>Solar Engineer</h1><button>Apply Now</button></main></body></html>""",
            ),
            # 8. Multiple JobPosting objects where the URL-matched one is active and another is expired
            (
                "https://careers.acme-energy.com/jobs/108",
                """<html><head>
                <script type="application/ld+json">[
                  {"@type": "JobPosting", "url": "https://careers.acme-energy.com/jobs/108", "validThrough": "2099-12-31"},
                  {"@type": "JobPosting", "url": "https://careers.acme-energy.com/jobs/001", "validThrough": "2020-01-01"}
                ]</script>
                </head><body><main><h1>Active Role 108</h1><button>Apply Now</button></main></body></html>""",
            ),
            # 9. Non-JSON-LD script containing validThrough in the past
            (
                "https://careers.acme-energy.com/jobs/109",
                """<html><head><script>const archived = {"validThrough": "2019-05-01"};</script></head>
                <body><main><h1>Gas Turbine Operator</h1><p>Full time role in Hadera.</p><button>Apply Now</button></main></body></html>""",
            ),
            # 10. Single weak phrase 'page not found' in job description prose
            (
                "https://careers.acme-energy.com/jobs/110",
                """<html><body><main><h1>QA Automation Engineer</h1>
                <p>You will test web dashboards, verify API responses, and ensure page not found states are handled gracefully across all environments.</p>
                <button>Apply Now</button></main></body></html>""",
            ),
            # 11. Single weak phrase 'no longer open' in company overview prose
            (
                "https://careers.acme-energy.com/jobs/111",
                """<html><body><main><h1>Field Service Engineer</h1>
                <p>While our legacy warehouse in Ashdod is no longer open, our new Caesarea hub supports all field operations nationwide.</p>
                <button>Apply Now</button></main></body></html>""",
            ),
            # 12. Single weak Hebrew phrase 'פג תוקף' in qualification instructions
            (
                "https://jobs.israel-power.co.il/role/112",
                """<html><body><main><h1>חשמלאי שטח למתקנים סולאריים</h1>
                <p>דרישות: רישיון חשמלאי בתוקף (מועמד שרישיונו פג תוקף יידרש להציג אישור חידוש לפני תחילת העבודה).</p>
                <button>הגש מועמדות</button></main></body></html>""",
            ),
            # 13. Single strong phrase in hiring process explanation on an active page with Apply CTA
            (
                "https://careers.acme-energy.com/jobs/113",
                """<html><body><main><h1>Project Execution Engineer</h1>
                <p>We review resumes on a rolling basis. Once this position is closed, all applicants will receive an email notification regarding next steps in our recruitment pipeline. Minimum 2 years of field engineering experience required.</p>
                <button>Apply Now</button></main></body></html>""",
            ),
            # 14. Non-ATS page with stale JSON-LD validThrough but active Apply Now button and zero closure text
            (
                "https://careers.acme-energy.com/jobs/114",
                """<html><head><script type="application/ld+json">{"@type": "JobPosting", "validThrough": "2022-01-01"}</script></head>
                <body><main><h1>HV Substation Technician</h1><p>Active opening for substation maintenance.</p><button>Apply Now</button></main></body></html>""",
            ),
            # 15. Active LinkedIn job page
            (
                "https://www.linkedin.com/jobs/view/115",
                """<html><body><main><h1>Flight Test Operator</h1><p>Operate UAV test flights in central Israel.</p><a class="apply">Apply Now</a></main></body></html>""",
            ),
            # 16. Active Comeet job page
            (
                "https://www.comeet.com/jobs/enlight/99.006/solar-engineer/116",
                """<html><body><main><h1>מהנדס ביצוע סולארי</h1><p>ניהול הקמת חוות סולאריות.</p><button>הגשת מועמדות</button></main></body></html>""",
            ),
            # 17. Active Drushim job page with cookie banner containing 'פג תוקף'
            (
                "https://www.drushim.co.il/job/117/",
                """<html><body><div class="cookie-banner">תוקף עוגיות פג תוקף לאחר שנה</div>
                <main><h1>הנדסאי מכונות לתעשייה</h1><p>תפקיד שטח מאתגר.</p><a class="btn">שלח קורות חיים</a></main></body></html>""",
            ),
            # 18. Active Greenhouse job page with CSS class rule for .closed-job__flavor inside <style>
            (
                "https://job-boards.greenhouse.io/company/jobs/118",
                """<html><head><style>.closed-job__flavor { color: red; }</style></head>
                <body><main><h1>Mechanical Assembly Tech</h1><form><input type="file" name="resume" /></form></main></body></html>""",
            ),
        ]

        inactive_corpus = [
            # 19. LinkedIn closed flavor class
            (
                "https://www.linkedin.com/jobs/view/201",
                """<html><body><main><h1>Solar Engineer</h1><span class="closed-job__flavor">No longer accepting applications</span></main></body></html>""",
            ),
            # 20. LinkedIn topcard closed class
            (
                "https://www.linkedin.com/jobs/view/202",
                """<html><body><main><div class="topcard__flavor--closed">Applications closed</div></main></body></html>""",
            ),
            # 21. Explicit data-job-closed="true" attribute
            (
                "https://careers.acme-energy.com/jobs/203",
                """<html><body><main data-job-closed="true"><h1>Field Technician</h1></main></body></html>""",
            ),
            # 22. Known ATS (Drushim) with Hebrew inactive message
            (
                "https://www.drushim.co.il/job/204/",
                """<html><body><main><div class="alert">המשרה אינה פעילה באתר</div></main></body></html>""",
            ),
            # 23. Known ATS (AllJobs) with Hebrew not-relevant message
            (
                "https://www.alljobs.co.il/Job/205",
                """<html><body><main><h1>מודעה זו אינה רלוונטית</h1></main></body></html>""",
            ),
            # 24. Known ATS (Lever) with expired primary JSON-LD validThrough
            (
                "https://jobs.lever.co/company/206",
                """<html><head><script type="application/ld+json">{"@type": "JobPosting", "validThrough": "2021-01-01"}</script></head>
                <body><main><h1>Operations Engineer</h1></main></body></html>""",
            ),
            # 25. Non-ATS site with heading + body closure signals
            (
                "https://careers.acme-energy.com/jobs/207",
                """<html><body><main><h1>This position is closed</h1><p>We are no longer accepting applications for this role.</p></main></body></html>""",
            ),
            # 26. Non-ATS site with alert banner + strong closure statement
            (
                "https://careers.acme-energy.com/jobs/208",
                """<html><head><title>Job Expired</title></head><body><main><div role="alert">This job is no longer available.</div></main></body></html>""",
            ),
            # 27. Non-ATS Hebrew site with h2 + body closure signals
            (
                "https://jobs.israel-power.co.il/role/209",
                """<html><body><main><h2>המשרה נסגרה</h2><p>הגשת מועמדות למשרה זו הסתיימה.</p></main></body></html>""",
            ),
            # 28. Non-ATS Hebrew site with alert class + job not located
            (
                "https://jobs.israel-power.co.il/role/210",
                """<html><body><main><div class="alert job-closed">לא אותרה משרה מבוקשת באתר</div></main></body></html>""",
            ),
            # 29. Non-ATS short stub with strong closure statement and no apply CTA
            (
                "https://jobs.israel-power.co.il/role/211",
                """<html><body><main><p>המשרה אוישה ואינה מקבלת מועמדויות.</p></main></body></html>""",
            ),
            # 30. Non-ATS page with expired primary JSON-LD validThrough and no active apply CTA
            (
                "https://careers.acme-energy.com/jobs/212",
                """<html><head><script type="application/ld+json">{"@type": "JobPosting", "validThrough": "2022-06-01"}</script></head>
                <body><main><h1>Solar Engineer</h1><p>Posting expired.</p></main></body></html>""",
            ),
        ]

        self.assertEqual(len(active_corpus) + len(inactive_corpus), 30)

        for idx, (url, html) in enumerate(active_corpus, 1):
            state, reason = classify_job_html(html, page_url=url)
            self.assertEqual(state, "active", f"Active corpus item #{idx} ({url}) falsely marked inactive: {reason}")

        for idx, (url, html) in enumerate(inactive_corpus, 19):
            state, reason = classify_job_html(html, page_url=url)
            self.assertEqual(state, "inactive", f"Inactive corpus item #{idx} ({url}) missed closure signal")

    def test_cloudflare_worker_signature_parity_and_cache_control(self):
        worker_js = (ROOT_DIR / "tools" / "cloudflare-worker" / "job-check.js").read_text(encoding="utf-8")
        # Verify no-store is used for non-cacheable/unknown responses
        self.assertIn('"no-store"', worker_js)
        self.assertIn('body.state === "active" || body.state === "inactive"', worker_js)
        self.assertIn("MAX_RESPONSE_BYTES", worker_js)

        # Verify every signature ID and pattern from src/closure_signatures.json appears in job-check.js
        for section in ("structural_markers", "strong_signatures", "weak_signatures"):
            for entry in CLOSURE_CONFIG[section]:
                self.assertIn(entry["id"], worker_js)
                self.assertIn(entry["reason"], worker_js)


class TestFinding4CompanyNormalizationAndMatching(unittest.TestCase):
    def test_logo_backfill_prevents_substring_false_positives(self):
        false_positive_companies = [
            "Mercedes-Benz Energy",
            "Intelligent Systems Ltd",
            "Marina Solar Tech",
            "Topcon Positioning",
            "Diff Engineering",
            "Asleep Labs",
            "Pineapple Power",
        ]
        for comp in false_positive_companies:
            self.assertIsNone(find_domain_for_company(comp), f"False domain match for {comp}")
            self.assertIsNone(find_local_logo_for_company(comp), f"False local logo match for {comp}")

        # True positives must still match accurately
        self.assertEqual(find_domain_for_company("Mer Group"), "mer-group.com")
        self.assertEqual(find_domain_for_company("Intel Israel"), "intel.com")
        self.assertEqual(find_domain_for_company("RINA Consulting"), "rina.org")
        self.assertEqual(find_domain_for_company("OPC Energy"), "opc-energy.com")
        self.assertEqual(find_local_logo_for_company("OPC Energy Ltd."), "assets/logos/opc.svg")

    def test_employer_blacklist_word_boundaries_and_hebrew_disambiguation(self):
        # Must NOT block non-matching companies or common Hebrew words in prose
        not_blocked = [
            ("Sensors Ltd", "Developing industrial optical sensors"),
            ("Single Phase Solar", "Inverter maintenance"),
            ("עתיד אנרגיה בע\"מ", "הקמת מערכות סולאריות"),
            ("מעוף טכנולוגיות", "פיתוח מערכות בקרה"),
            ("Enlight Renewable Energy", "אנחנו בונים עתיד ירוק לתעשיית האנרגיה עם מעוף ומצוינות"),
        ]
        for company, text in not_blocked:
            blocked, reason = check_employer_blacklist(company, text)
            self.assertFalse(blocked, f"Company '{company}' was falsely blocked: {reason}")

        # Must block actual excluded employers across quote/case variations
        must_block = [
            ("Energean Israel", ""),
            ("אנרג'יאן ישראל", ""),
            ("אנרגיאן", ""),
            ("INGL", ""),
            ("נתג״ז", ""),
            ("נתג\"ז", ""),
            ("ORS Human Resources", ""),
            ("עתיד השמה", ""),
            ("עתיד בע\"מ", ""),
            ("מעוף משאבי אנוש", ""),
            ("קבוצת מעוף", ""),
        ]
        for company, text in must_block:
            blocked, _ = check_employer_blacklist(company, text)
            self.assertTrue(blocked, f"Excluded employer '{company}' was not blocked")

    def test_quote_and_casefold_normalization(self):
        self.assertEqual(normalize_company_name("נתג״ז"), 'נתג"ז')
        self.assertEqual(normalize_company_name("אנרג׳יאן"), "אנרג'יאן")
        deduped = deduplicate_employer_list(["Energean", "energean", "נתג״ז", "נתג\"ז", "אנרג'יאן", "אנרגיאן"])
        self.assertEqual(len(deduped), 3)
        self.assertTrue(company_tokens_match("חברת נתג״ז בע\"מ", "נתג\"ז"))


class TestFinding5FitGapsAndReasoning(unittest.TestCase):
    def test_subscription_does_not_trigger_bsc_gap(self):
        job = {
            "title": "Energy Operations Coordinator",
            "company": "SolarCo",
            "company_requirements": "Manage customer subscription renewals, alert monitoring, and obscure telemetry logs.",
            "job_summary": "Operations role in Tel Aviv.",
            "snippet": "Full-time subscription management and SCADA monitoring.",
        }
        gaps = analyze_fit_gaps(job)
        self.assertNotIn("B.Sc", gaps)
        self.assertNotIn("אזרחית", gaps)
        self.assertEqual(gaps, "אין פערי סף מהותיים מול דרישות התפקיד.")

    def test_real_bsc_requirement_triggers_public_safe_gap(self):
        job = {
            "title": "Mechanical Engineer",
            "company": "SolarCo",
            "company_requirements": "B.Sc in Mechanical Engineering required. 3+ years experience.",
            "job_summary": "Design thermal systems.",
        }
        gaps = analyze_fit_gaps(job)
        self.assertIn("B.Sc", gaps)
        # Ensure zero personal/military PII in public gap strings
        self.assertNotIn("בלימודים", gaps)
        self.assertNotIn("פיקודי", gaps)
        self.assertNotIn("קרבי", gaps)

    def test_update_job_record_preserves_full_reasoning(self):
        long_reasoning = (
            "התאמה גבוהה לתפקיד בזכות ניסיון במערכות אנרגיה ובקרה. "
            "המועמד מביא רקע מעשי בתפעול מתקנים. "
            "בנוסף קיימת היכרות עם נהלי בטיחות ואיכות."
        )
        job = {"title": "Technician", "company": "OPC", "reasoning": long_reasoning}
        update_job_record_in_place(job)
        self.assertEqual(job["full_reasoning"], long_reasoning)
        self.assertTrue(len(job["reasoning"]) < len(long_reasoning))


class TestPhase4HygieneAndEvaluationTools(unittest.TestCase):
    def test_project_hygiene_protects_data_and_docs_files(self):
        self.assertTrue(is_protected("data/jobs_state.json.bak"))
        self.assertTrue(is_protected("docs/job-intake-notes.md"))
        self.assertTrue(is_protected("src/backup.tmp"))
        self.assertFalse(is_protected("scratch_notes.bak"))
        self.assertFalse(is_protected("src/__pycache__/module.cpython-39.pyc"))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "docs").mkdir()
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "data" / "keep.bak").write_text("protected", encoding="utf-8")
            (root / "docs" / "keep-intake.md").write_text("protected", encoding="utf-8")
            (root / "root_temp.bak").write_text("disposable", encoding="utf-8")
            (root / "node_modules" / "pkg" / "broken.json").write_text("{invalid", encoding="utf-8")

            scan = scan_project(root)
            disposable_paths = [item["path"] for item in scan["tier2_disposable"]]
            self.assertIn("root_temp.bak", disposable_paths)
            self.assertNotIn(os.path.join("data", "keep.bak"), disposable_paths)
            self.assertNotIn(os.path.join("docs", "keep-intake.md"), disposable_paths)

    def test_exact_dependency_package_parsing_and_secret_patterns(self):
        pkgs = _parse_requirement_packages("requests-toolbelt==1.0.0\ngoogle-genai>=0.3.0\n# comment")
        self.assertIn("requests-toolbelt", pkgs)
        self.assertNotIn("requests", pkgs)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_sb = "sb_" + "secret_" + ("a1" * 10)
            fake_aws = "AK" + "IA" + ("9" * 16)
            fake_ant = "sk-" + "ant-api03-" + ("b2" * 12)
            (root / "leak.txt").write_text(
                f"{fake_sb}\n{fake_aws}\n{fake_ant}\n",
                encoding="utf-8",
            )
            self.assertEqual(scan_secrets(root), 3)

    def test_compute_metrics_zero_f1_and_stratified_sampling(self):
        zero_tp_results = [
            {"predicted": "relevant", "expected": "irrelevant"},
            {"predicted": "irrelevant", "expected": "relevant"},
        ]
        m = compute_metrics(zero_tp_results)
        self.assertEqual(m["precision"], 0.0)
        self.assertEqual(m["recall"], 0.0)
        self.assertIsNotNone(m["f1"])
        self.assertEqual(m["f1"], 0.0)

        with tempfile.TemporaryDirectory() as tmp:
            ledger_path = Path(tmp) / "evaluation_state.json"
            out_path = Path(tmp) / "sampled.json"
            ledger_data = {
                "version": 1,
                "jobs": {
                    f"https://example.com/q/{i}": {
                        "stage": "READY",
                        "job": {"title": f"Role Q{i}", "company": "SolarCo", "snippet": "ok", "status": "QUALIFIED", "evaluation_source": "gemini"},
                    }
                    for i in range(5)
                }
                | {
                    f"https://example.com/g/{i}": {
                        "stage": "COMPLETE",
                        "job": {"title": f"Role G{i}", "company": "RetailCo", "snippet": "no", "status": "DISQUALIFIED", "evaluation_source": "deterministic"},
                    }
                    for i in range(5)
                }
                | {
                    f"https://example.com/a/{i}": {
                        "stage": "COMPLETE",
                        "job": {"title": f"Role A{i}", "company": "SoftCo", "snippet": "no", "status": "DISQUALIFIED", "evaluation_source": "gemini"},
                    }
                    for i in range(5)
                },
            }
            ledger_path.write_text(json.dumps(ledger_data), encoding="utf-8")
            exported = sample_from_archive(output_path=str(out_path), count=9, ledger_path=str(ledger_path))
            self.assertEqual(exported["strata_counts"]["passed_pipeline"], 3)
            self.assertEqual(exported["strata_counts"]["rejected_gate"], 3)
            self.assertEqual(exported["strata_counts"]["rejected_ai"], 3)

    def test_expanded_zero_emoji_ranges(self):
        for ch in ("\u2b50", "\U0001f004", "\u2122", "\u2139", "\u200d"):
            violations = check_text(f"Sample text with {ch} symbol")
            self.assertEqual(len(violations), 1, f"Failed to detect banned codepoint U+{ord(ch):04X}")


class TestPhase5OutboxAndObservability(unittest.TestCase):
    def test_email_outbox_prevents_duplicate_send_after_state_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            outbox_file = Path(tmp) / "email_outbox.json"
            jobs = [{"link": "https://example.com/job/99", "title": "Solar Tech", "match_score": 88}]
            send_mock = MagicMock(side_effect=lambda *args: setattr(args[-1], "email_success", True))

            with patch.dict("os.environ", {"SENDER_EMAIL": "bot@example.com", "SENDER_APP_PASSWORD": "secret"}, clear=True), \
                 patch.object(main, "send_email_report", side_effect=send_mock):
                health1 = RunHealth()
                main.dispatch_notifications(jobs, True, health1, outbox_path=outbox_file)
                self.assertEqual(send_mock.call_count, 1)
                self.assertTrue(health1.email_success)
                outbox_state = json.loads(outbox_file.read_text(encoding="utf-8"))
                self.assertEqual(outbox_state["status"], "SENT")

                # Simulate retry before persist_state acknowledged the outbox
                health2 = RunHealth()
                main.dispatch_notifications(jobs, True, health2, outbox_path=outbox_file)
                self.assertEqual(send_mock.call_count, 1, "Outbox must prevent duplicate SMTP send for SENT batch")
                self.assertTrue(health2.email_success)

    def test_run_report_includes_quality_metrics(self):
        health = RunHealth(candidates_found=4, jobs_evaluated=4, jobs_passed=1, jobs_rejected=3, gemini_attempts=2)
        audit = [
            {"status": "DISQUALIFIED", "evaluation_source": "deterministic"},
            {"status": "DISQUALIFIED", "evaluation_source": "deterministic"},
            {"status": "DISQUALIFIED", "evaluation_source": "gemini"},
            {"status": "QUALIFIED", "evaluation_source": "gemini"},
        ]
        inactive_rep = {"total_scanned": 20, "unknown_count": 2}
        rep = run_report(health, audit, inactive_report=inactive_rep)
        qm = rep["quality_metrics"]
        self.assertEqual(qm["gate_rejection_rate"], 0.5)
        self.assertEqual(qm["deterministic_rejections"], 2)
        self.assertEqual(qm["gemini_evaluations"], 2)
        self.assertGreater(qm["estimated_gemini_cost_usd"], 0.0)
        self.assertEqual(qm["unknown_scan_rate"], 0.1)


if __name__ == "__main__":
    unittest.main()
