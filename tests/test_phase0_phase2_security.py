#!/usr/bin/env python3
"""
Regression test suite for Phase 0 (Privacy & Supabase CAS/RLS) and Phase 2 (XSS & Client Security).
"""

import os
import re
import shutil
import subprocess
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NODE_CMD = shutil.which("node") or ("/usr/local/bin/node" if Path("/usr/local/bin/node").exists() else "node")


class TestPhase0AndPhase2Security(unittest.TestCase):
    def setUp(self):
        self.dashboard_js = (PROJECT_ROOT / "frontend" / "js" / "dashboard.js").read_text(encoding="utf-8")
        self.docs_dashboard_js = (PROJECT_ROOT / "docs" / "dashboard.js").read_text(encoding="utf-8")
        self.ats_engine_js = (PROJECT_ROOT / "frontend" / "js" / "modules" / "atsEngine.js").read_text(encoding="utf-8")
        self.render_js = (PROJECT_ROOT / "frontend" / "js" / "modules" / "render.js").read_text(encoding="utf-8")
        self.geomap_js = (PROJECT_ROOT / "frontend" / "js" / "modules" / "geoMap.js").read_text(encoding="utf-8")
        self.store_js = (PROJECT_ROOT / "frontend" / "js" / "modules" / "store.js").read_text(encoding="utf-8")
        self.index_html = (PROJECT_ROOT / "frontend" / "templates" / "index.html").read_text(encoding="utf-8")

    def test_zero_personal_contact_pii_in_client_bundles_and_published_cvs(self):
        """Finding 10: Public client bundles and published static CVs must not contain personal phone/email."""
        checked_files = [
            PROJECT_ROOT / "frontend" / "js" / "dashboard.js",
            PROJECT_ROOT / "docs" / "dashboard.js",
            PROJECT_ROOT / "frontend" / "js" / "modules" / "atsEngine.js",
            PROJECT_ROOT / "docs" / "js" / "modules" / "atsEngine.js",
            PROJECT_ROOT / "frontend" / "data" / "cv" / "cv_he.html",
            PROJECT_ROOT / "frontend" / "data" / "cv" / "cv_en.html",
            PROJECT_ROOT / "docs" / "career" / "cv" / "cv_he.html",
            PROJECT_ROOT / "docs" / "career" / "cv" / "cv_en.html",
        ]
        forbidden_patterns = [
            "052-632-8886",
            "0526328886",
            "+972-52-632-8886",
            "idogal0210@gmail.com",
        ]
        for path in checked_files:
            content = path.read_text(encoding="utf-8")
            for pat in forbidden_patterns:
                self.assertNotIn(pat, content, f"Forbidden personal PII '{pat}' found in {path}")

    def test_uploaded_cv_uses_session_storage_not_local_storage(self):
        """Finding 7.2: Uploaded CV plaintext must be stored in sessionStorage and purged from localStorage."""
        self.assertIn("sessionStorage.setItem('job_studio_custom_cv_text'", self.dashboard_js)
        self.assertNotIn("localStorage.setItem('job_studio_custom_cv_text'", self.dashboard_js)
        self.assertIn("localStorage.removeItem('job_studio_custom_cv_text')", self.dashboard_js)

    def test_supabase_cas_and_rls_migration_and_client_adapter(self):
        """Findings 8 & 9: Supabase migration + client adapter enforce true CAS, user_id RLS, and no self-signup."""
        mig = PROJECT_ROOT / "supabase" / "migrations" / "20261115011000_harden_sync_state_cas_and_rls.sql"
        self.assertTrue(mig.exists(), "Supabase hardening migration file must exist")
        mig_sql = mig.read_text(encoding="utf-8")
        self.assertIn("user_id uuid references auth.users(id)", mig_sql)
        self.assertIn("version bigint not null default 1", mig_sql)
        self.assertIn("using (user_id = (select auth.uid()))", mig_sql)
        self.assertIn("trg_block_unauthorized_signup", mig_sql)

        # Client adapter must not use blind merge-duplicates upsert
        self.assertNotIn("resolution=merge-duplicates", self.dashboard_js)
        self.assertIn("method: 'PATCH'", self.dashboard_js)
        self.assertIn("'Prefer': 'return=representation'", self.dashboard_js)
        self.assertIn("conflict: true", self.dashboard_js)

        # Self-signup button must be removed from #cloudModal
        soup = BeautifulSoup(self.index_html, "html.parser")
        cloud_modal = soup.find(id="cloudModal")
        self.assertIsNotNone(cloud_modal)
        self.assertNotIn("runCloudAuthAction('signup')", str(cloud_modal))

    def test_studio_onclick_handlers_use_json_stringify_and_escape_html(self):
        """Finding 11: Dynamic onclick handlers in dashboard.js and render.js must serialize arguments via JSON.stringify."""
        self.assertIn("onclick=\"injectKeywordToWriter(${safeTermAttr})\"", self.dashboard_js)
        self.assertIn("onclick=\"selectPreviewLineForEditing(${safeBulletAttr})\"", self.dashboard_js)
        self.assertIn("onclick=\"insertDictionaryTerm(${safeSnippetAttr})\"", self.dashboard_js)
        self.assertIn("onclick=\"openJobModal(${escapeHtml(JSON.stringify(String(job.link || '')))})\"", self.dashboard_js)
        # Ensure vulnerable single-quote replacement patterns are gone
        self.assertNotIn("onclick=\"injectKeywordToWriter('${safeTerm}')\"", self.dashboard_js)
        self.assertNotIn("onclick=\"selectPreviewLineForEditing('${safeBullet}')\"", self.dashboard_js)
        self.assertNotIn("onclick=\"insertDictionaryTerm('${safeSnippet}')\"", self.dashboard_js)

        # Verify render.js onclick handlers also use escapeHtml(JSON.stringify(...))
        self.assertNotIn("window.store.toggleStar('${id}')", self.render_js)
        self.assertNotIn("window.store.setJobAction('${id}'", self.render_js)

    def test_sanitize_url_and_word_boundary_template_matching_in_node(self):
        """Finding 7.2: sanitizeUrl blocks control-char schemes; generateCvBulletActionItem uses word boundaries."""
        node_script = """
        import { sanitizeUrl } from './frontend/js/modules/render.js';
        import { generateCvBulletActionItem } from './frontend/js/modules/atsEngine.js';

        for (const bad of [
          'javascript:alert(1)',
          '\\u0001javascript:alert(1)',
          '\\tjavascript:alert(1)',
          'data:text/html,<script>alert(1)</script>',
          'vbscript:msgbox(1)',
          'ftp://files.example.com/a',
          'https://user:pass@example.com/job'
        ]) {
          if (sanitizeUrl(bad) !== '#') {
            console.error('Failed to block unsafe URL:', bad, '->', sanitizeUrl(bad));
            process.exit(1);
          }
        }

        if (!sanitizeUrl('https://example.com/jobs?id=1&b=2').startsWith('https://example.com/jobs')) {
          process.exit(2);
        }
        if (sanitizeUrl('mailto:hr@example.com') !== 'mailto:hr@example.com') {
          process.exit(3);
        }

        // 'android' contains 'roi' as a substring, so it must NOT match the 'roi' financial template
        const androidItem = generateCvBulletActionItem('android', { company: 'TestCo' });
        if (androidItem.category === 'financials') {
          console.error('Substring false positive: android matched financials/roi');
          process.exit(4);
        }

        // Word-bounded 'roi' must still match financials
        const roiItem = generateCvBulletActionItem('מדדי ROI בפרויקט', { company: 'TestCo' });
        if (roiItem.category !== 'financials') {
          console.error('Expected word-bounded ROI to match financials, got:', roiItem.category);
          process.exit(5);
        }

        console.log('OK');
        """
        proc = subprocess.run(
            [NODE_CMD, "--input-type=module", "-e", node_script],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"Node verification failed: {proc.stderr}")
        self.assertIn("OK", proc.stdout)

    def test_app_js_imports_cleanly_without_duplicate_export(self):
        """Finding 7.2: frontend/js/app.js must import as an ES module without duplicate export SyntaxError."""
        proc = subprocess.run(
            [NODE_CMD, "--input-type=module", "-e", "import * as app from './frontend/js/app.js'; if (typeof app.initApp !== 'function') process.exit(1); console.log('OK');"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, f"ESM import of app.js failed: {proc.stderr}")
        self.assertIn("OK", proc.stdout)

    def test_map_tiles_and_sri_and_index_html_hygiene(self):
        """Findings 7 & 7.2: No unofficial mt1.google.com tiles; chart.js pinned with SRI; no nested role=button in metricsToggleBtn."""
        self.assertNotIn("mt1.google.com", self.dashboard_js)
        self.assertNotIn("mt1.google.com", self.geomap_js)
        self.assertIn("basemaps.cartocdn.com", self.dashboard_js)
        self.assertIn("basemaps.cartocdn.com", self.geomap_js)
        self.assertIn("scriptL.integrity =", self.geomap_js)
        self.assertIn("scriptMC.integrity =", self.geomap_js)

        soup = BeautifulSoup(self.index_html, "html.parser")
        self.assertIsNone(soup.find("meta", attrs={"http-equiv": re.compile("Cache-Control|Pragma|Expires", re.I)}))

        chart_script = soup.find("script", attrs={"src": re.compile(r"chart\.js@4\.4\.1")})
        self.assertIsNotNone(chart_script, "chart.js must be pinned to 4.4.1")
        self.assertTrue(chart_script.get("integrity", "").startswith("sha384-"))

        # pdf.js and mammoth must be lazy-loaded on demand, not blocking initial <head>
        self.assertIsNone(soup.find("script", attrs={"src": re.compile(r"pdf\.min\.js|mammoth\.browser\.min\.js")}))
        self.assertIn("ensurePdfJsLoaded", self.dashboard_js)
        self.assertIn("ensureMammothLoaded", self.dashboard_js)

        # No nested role="button" inside #metricsToggleBtn
        toggle_btn = soup.find(id="metricsToggleBtn")
        self.assertIsNotNone(toggle_btn)
        nested_buttons = toggle_btn.find_all(attrs={"role": "button"})
        self.assertEqual(len(nested_buttons), 0, "metricsToggleBtn must not contain nested role=button elements")


if __name__ == "__main__":
    unittest.main()
