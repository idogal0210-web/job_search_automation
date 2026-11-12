"""Unit tests for direct ATS connectors, API-first Career Studio ingestion, and inactive verification."""
import unittest
from unittest.mock import MagicMock, patch

from scripts.scan_inactive_jobs import check_job_url
from src.ats_client import fetch_ats_job_detail, parse_ats_url
from src.config import get_ats_boards
from src.fetchers import (
    CircuitBreaker,
    FETCHERS,
    RunHealth,
    fetch_greenhouse_jobs,
    fetch_lever_jobs,
)
from src.pipeline import enrich, final_status
from src.url_utils import stable_job_id
from tools.cv_tailor.src.scraper import scrape_job


class TestAtsConfigAndIdentity(unittest.TestCase):
    def test_get_ats_boards_loads_verified_providers(self):
        boards = get_ats_boards()
        self.assertGreaterEqual(len(boards["comeet"]), 5)
        self.assertGreaterEqual(len(boards["greenhouse"]), 2)
        self.assertGreaterEqual(len(boards["lever"]), 1)
        comeet_slugs = {item["slug"] for item in boards["comeet"]}
        self.assertIn("enlightenergy", comeet_slugs)
        self.assertIn("mprest", comeet_slugs)

    def test_stable_job_id_supports_greenhouse_lever_ashby(self):
        self.assertEqual(
            stable_job_id("https://job-boards.greenhouse.io/augury/jobs/8310352002"),
            "gh_8310352002",
        )
        self.assertEqual(
            stable_job_id("https://jobs.lever.co/d-fendsolutions/f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53"),
            "lever_f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53",
        )
        self.assertEqual(
            stable_job_id("https://jobs.ashbyhq.com/linear/6dd5500a-4bd4-4f57-ba09-7b07acefecf4"),
            "ashby_6dd5500a-4bd4-4f57-ba09-7b07acefecf4",
        )


class TestDirectAtsFetchersAndBreaker(unittest.TestCase):
    def test_fetch_greenhouse_jobs_success(self):
        mock_session = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "jobs": [
                {
                    "id": 8310352002,
                    "title": "Field Reliability Engineer",
                    "company_name": "Augury",
                    "location": {"name": "Haifa, Israel"},
                    "updated_at": "2026-11-11T10:00:00-05:00",
                    "absolute_url": "https://job-boards.greenhouse.io/augury/jobs/8310352002",
                    "content": "&lt;p&gt;Industrial rotating equipment diagnostics.&lt;/p&gt;",
                }
            ]
        }
        mock_session.get.return_value = mock_resp

        health = RunHealth()
        jobs = fetch_greenhouse_jobs("augury", "Augury", health_metrics=health, session=mock_session)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "Greenhouse")
        self.assertTrue(jobs[0]["is_direct_ats"])
        self.assertTrue(jobs[0]["description_complete"])
        self.assertIn("Industrial rotating equipment", jobs[0]["description"])
        self.assertEqual(health.greenhouse_requests, 1)
        self.assertEqual(health.greenhouse_successes, 1)
        self.assertEqual(health.greenhouse_jobs_found, 1)
        self.assertIn("greenhouse", FETCHERS)

    def test_fetch_lever_jobs_success_and_error(self):
        mock_session = MagicMock()
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = [
            {
                "id": "f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53",
                "text": "Field Training and Support Engineer",
                "hostedUrl": "https://jobs.lever.co/d-fendsolutions/f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53",
                "categories": {"location": "Raanana, Center District"},
                "descriptionPlain": "C-UAS system deployment and field support.",
                "lists": [{"text": "Requirements", "content": "<li>Practical engineer</li>"}],
            }
        ]
        mock_session.get.return_value = ok_resp

        health = RunHealth()
        jobs = fetch_lever_jobs("d-fendsolutions", "D-Fend Solutions", health_metrics=health, session=mock_session)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["source"], "Lever")
        self.assertIn("Practical engineer", jobs[0]["description"])
        self.assertEqual(health.lever_successes, 1)
        self.assertEqual(health.lever_jobs_found, 1)

        err_resp = MagicMock()
        err_resp.status_code = 404
        mock_session.get.return_value = err_resp
        self.assertEqual(fetch_lever_jobs("missing", health_metrics=health, session=mock_session), [])
        self.assertEqual(health.lever_failures, 1)

    def test_circuit_breaker_and_final_status(self):
        breaker = CircuitBreaker(threshold=3)
        self.assertFalse(breaker.is_open("greenhouse"))
        breaker.record_failure("greenhouse")
        breaker.record_failure("greenhouse")
        self.assertFalse(breaker.is_open("greenhouse"))
        breaker.record_failure("greenhouse")
        self.assertTrue(breaker.is_open("greenhouse"))
        breaker.record_success("greenhouse")
        self.assertFalse(breaker.is_open("greenhouse"))

        health = RunHealth(greenhouse_requests=1, greenhouse_failures=1, email_success=True)
        self.assertEqual(final_status(health, email_configured=True), "FAILED_SCRAPERS")


class TestAtsClientAndIntegrations(unittest.TestCase):
    def test_parse_ats_url_variants(self):
        self.assertEqual(
            parse_ats_url("https://job-boards.eu.greenhouse.io/electreon/jobs/4696367101"),
            {"provider": "greenhouse", "company_slug": "electreon", "job_id": "4696367101"},
        )
        self.assertEqual(
            parse_ats_url("https://jobs.lever.co/d-fendsolutions/f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53")["provider"],
            "lever",
        )
        self.assertEqual(
            parse_ats_url("https://www.comeet.com/jobs/xtend/85.00A/integrator/F5.160"),
            {"provider": "comeet", "company_slug": "xtend", "company_uid": "85.00A", "job_id": "F5.160"},
        )
        self.assertIsNone(parse_ats_url("https://www.linkedin.com/jobs/view/123456"))

    def test_fetch_ats_job_detail_states_and_inactive_scanner(self):
        mock_session = MagicMock()
        not_found = MagicMock()
        not_found.status_code = 404
        mock_session.get.return_value = not_found

        res = fetch_ats_job_detail("https://job-boards.greenhouse.io/augury/jobs/999", session=mock_session)
        self.assertFalse(res["ok"])
        self.assertEqual(res["state"], "inactive")
        self.assertEqual(res["status_code"], 404)

        with patch("scripts.scan_inactive_jobs.fetch_ats_job_detail", return_value=res):
            state, reason, code = check_job_url({"link": "https://job-boards.greenhouse.io/augury/jobs/999"})
            self.assertEqual(state, "inactive")
            self.assertEqual(code, 404)
            self.assertIn("Greenhouse", reason)

    def test_pipeline_enrich_and_studio_scraper_api_first(self):
        detail = {
            "ok": True,
            "state": "active",
            "provider": "lever",
            "reason": "ok",
            "status_code": 200,
            "job": {
                "url": "https://jobs.lever.co/d-fendsolutions/f9d4a1ba-baa4-471a-a39a-1b0e4a3e3a53",
                "title": "Field Training Engineer",
                "company": "d-fendsolutions",
                "location": "Raanana",
                "description": "Hands-on UAV RF counter-drone field operations.",
                "source": "ats_lever_api",
            },
        }
        job = {"link": detail["job"]["url"], "source": "Lever", "snippet": ""}
        with patch("src.pipeline.fetch_ats_job_detail", return_value=detail):
            enrich(job)
        self.assertTrue(job["description_complete"])
        self.assertIn("counter-drone", job["description"])

        with patch("tools.cv_tailor.src.scraper.fetch_ats_job_detail", return_value=detail), \
             patch("tools.cv_tailor.src.scraper.scrape_with_firecrawl") as mock_fc:
            posting = scrape_job(detail["job"]["url"], firecrawl_key="fc-should-not-be-used")
        mock_fc.assert_not_called()
        self.assertEqual(posting.source, "ats_lever_api")
        self.assertEqual(posting.title, "Field Training Engineer")


if __name__ == "__main__":
    unittest.main()
