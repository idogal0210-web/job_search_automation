#!/usr/bin/env python3
"""
Unit tests for the three dashboard fixes:
1. Mobile-Desktop Tab Counters & Badges consistency.
2. Complete removal of 'More Filters' (advanced-job-filters) and zero DOM clutter.
3. Stable Job IDs and robust state persistence preventing overwrite/resurrection.
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from src.url_utils import canonical_job_url, stable_job_id
from src.ui_builder import update_weekly_archive, build_and_save_docs_app

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestDashboardStateAndCountersConsistency(unittest.TestCase):

    def test_stable_job_id_deterministic(self):
        # LinkedIn with and without parameters
        url1 = "https://il.linkedin.com/jobs/view/4481748648?refId=xyz&trackingId=abc"
        url2 = "https://www.linkedin.com/jobs/view/practical-engineer-at-solaredge-4481748648"
        self.assertEqual(stable_job_id(url1), "li_4481748648")
        self.assertEqual(stable_job_id(url2), "li_4481748648")

        # Comeet
        c_url = "https://www.comeet.com/jobs/enlightenergy/99.006/grid-coordinator/19.47C"
        self.assertEqual(stable_job_id(c_url), "comeet_19.47C")

        # Drushim
        d_url = "https://www.drushim.co.il/job/1234567/"
        self.assertEqual(stable_job_id(d_url), "drushim_1234567")

        # Content hash fallback
        job1 = {"company": "SolarEdge", "title": "Field Technician"}
        job2 = {"company": "  solaredge  ", "title": "FIELD TECHNICIAN "}
        self.assertEqual(stable_job_id(job1), stable_job_id(job2))
        self.assertTrue(stable_job_id(job1).startswith("ch_"))

    def test_advanced_filters_removed_from_template_and_docs(self):
        tpl_html = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(encoding="utf-8")
        docs_html = (PROJECT_ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        frontend_css = (PROJECT_ROOT / "frontend" / "css" / "dashboard.css").read_text(encoding="utf-8")
        docs_css = (PROJECT_ROOT / "docs" / "dashboard.css").read_text(encoding="utf-8")

        self.assertNotIn("advanced-job-filters", tpl_html)
        self.assertNotIn("advanced-job-filters", docs_html)
        self.assertNotIn("advanced-job-filters", frontend_css)
        self.assertNotIn("advanced-job-filters", docs_css)

        self.assertNotIn('id="scoreFilter"', tpl_html)
        self.assertNotIn('id="scoreFilter"', docs_html)
        self.assertNotIn('id="salaryFilter"', tpl_html)
        self.assertNotIn('id="salaryFilter"', docs_html)

    def test_update_weekly_archive_purged_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "data").mkdir()
            archive_path = str(tmp_root / "data" / "weekly_archive.json")
            catalog_path = str(tmp_root / "data" / "historical_catalog.json")
            sync_state_path = str(tmp_root / "data" / "sync_state.json")

            existing_job = {
                "link": "https://www.linkedin.com/jobs/view/1111111111",
                "title": "Solar Tech",
                "company": "Enlight",
                "date": "2026-11-01"
            }
            purged_job = {
                "link": "https://www.linkedin.com/jobs/view/2222222222",
                "title": "Deleted Tech",
                "company": "Enlight",
                "date": "2026-11-01"
            }

            Path(archive_path).write_text(json.dumps([existing_job, purged_job]))
            Path(catalog_path).write_text(json.dumps({existing_job["link"]: existing_job, purged_job["link"]: purged_job}))
            Path(sync_state_path).write_text(json.dumps({
                "purged": ["https://il.linkedin.com/jobs/view/2222222222?trk=test"],
                "rejected": [],
                "saved": [],
                "starred": []
            }))

            # Run update_weekly_archive without passing rejected_set explicitly - should load from sync_state
            res = update_weekly_archive([], archive_path)
            res_links = [j["link"] for j in res]
            self.assertIn(existing_job["link"], res_links)
            self.assertNotIn(purged_job["link"], res_links)

            # Attempting to add the purged job again via new_jobs must be blocked
            new_attempt = [{
                "link": "https://il.linkedin.com/jobs/view/deleted-tech-2222222222",
                "title": "Deleted Tech",
                "company": "Enlight"
            }]
            res2 = update_weekly_archive(new_attempt, archive_path)
            res2_links = [j["link"] for j in res2]
            self.assertNotIn(purged_job["link"], res2_links)
            self.assertNotIn(new_attempt[0]["link"], res2_links)

    def test_js_has_unified_counter_and_resize(self):
        js_content = (PROJECT_ROOT / "frontend" / "js" / "dashboard.js").read_text(encoding="utf-8")
        # Ensure single source of truth updates both statNewEl and summaryNew simultaneously
        self.assertIn("statNewEl.textContent = countNew", js_content)
        self.assertIn("summaryNew.textContent = countNew", js_content)
        self.assertIn("statStarredEl.textContent = countStarred", js_content)
        self.assertIn("summaryStarred.textContent = countStarred", js_content)
        # Ensure resize listener is installed
        self.assertIn("addEventListener('resize'", js_content)
        # Ensure unstarred tombstone is loaded and saved
        self.assertIn("UNSTARRED_STORAGE_KEY", js_content)
        self.assertIn("RESTORED_STORAGE_KEY", js_content)

    def test_mobile_input_font_size_and_touch_targets(self):
        css_content = (PROJECT_ROOT / "frontend" / "css" / "dashboard.css").read_text(encoding="utf-8")
        # Ensure mobile input and select font size is >= 16px to prevent Safari auto-zoom
        self.assertIn("font-size: 16px !important", css_content)
        # Ensure 44x44px touch targets on mobile
        self.assertIn("min-height: 44px !important", css_content)
        self.assertIn("min-width: 44px !important", css_content)

    def test_zero_synthetic_logos_policy(self):
        js_content = (PROJECT_ROOT / "frontend" / "js" / "dashboard.js").read_text(encoding="utf-8")
        # Ensure no monogram letter avatars are rendered
        self.assertNotIn('<div class="job-company-avatar"', js_content)
        # Ensure onerror handler is present on logo image
        self.assertIn("onerror=", js_content)
        self.assertIn("handleCompanyLogoError", js_content)

    def test_content_job_hash_resilience(self):
        from src.url_utils import content_job_hash
        job_variant1 = {
            "company": 'סולאראדג׳ בע"מ',
            "title": "טכנאי/ת שירות (M/F) — מתקנים סולאריים"
        }
        job_variant2 = {
            "company": "  סולאראדג'  ",
            "title": "טכנאי שירות - מתקנים סולאריים"
        }
        hash1 = content_job_hash(job_variant1)
        hash2 = content_job_hash(job_variant2)
        self.assertTrue(hash1.startswith("ch_"))
        self.assertEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
