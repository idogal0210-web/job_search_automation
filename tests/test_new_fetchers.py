import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from src.fetchers import (
    RunHealth,
    fetch_indeed_jobs,
    fetch_glassdoor_jobs,
    FETCHERS,
    IndeedFetcher,
    GlassdoorFetcher,
)
from src.config import get_search_keywords


class FetchersIndeedGlassdoorTests(unittest.TestCase):
    def test_fetcher_registry_contains_new_sources(self):
        self.assertIn("indeed", FETCHERS)
        self.assertIn("glassdoor", FETCHERS)
        self.assertIsInstance(FETCHERS["indeed"], IndeedFetcher)
        self.assertIsInstance(FETCHERS["glassdoor"], GlassdoorFetcher)

    def test_config_search_keywords_returns_new_sources(self):
        keywords = get_search_keywords()
        self.assertIn("indeed", keywords)
        self.assertIn("glassdoor", keywords)
        self.assertIsInstance(keywords["indeed"], list)
        self.assertIsInstance(keywords["glassdoor"], list)

    def test_fetch_indeed_jobs_mosaic_json(self):
        mock_payload = {
            "metaData": {
                "mosaicProviderJobCardsModel": {
                    "results": [
                        {
                            "jobkey": "jk_scada_1",
                            "title": "SCADA Operator",
                            "company": "Energy Corp",
                            "formattedLocation": "Haifa, Israel",
                            "snippet": "Experienced with <b>SCADA</b> and PLC controllers.",
                        },
                        {
                            "jobkey": "jk_scada_2",
                            "title": "Gas Systems Specialist",
                            "company": "Natural Gas Ltd",
                            "formattedLocation": "South Israel",
                            "snippet": "High pressure natural gas transmission operations.",
                        },
                    ]
                }
            }
        }
        mock_html = (
            "<html><head></head><body>"
            "<script>"
            f'window.mosaic.providerData["mosaic-provider-jobcards"]={json.dumps(mock_payload)};\n'
            "</script></body></html>"
        )
        fake_response = SimpleNamespace(status_code=200, text=mock_html)
        health = RunHealth()

        with patch("src.fetchers.requests.get", return_value=fake_response), \
             patch("src.fetchers.cffi_requests", None), \
             patch("src.fetchers.time.sleep"):
            jobs = fetch_indeed_jobs(["SCADA"], health, location="Israel", max_pages=1)

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0]["title"], "SCADA Operator")
        self.assertEqual(jobs[0]["company"], "Energy Corp")
        self.assertEqual(jobs[0]["link"], "https://il.indeed.com/viewjob?jk=jk_scada_1")
        self.assertEqual(jobs[0]["source"], "Indeed")
        self.assertIn("SCADA and PLC", jobs[0]["snippet"])
        self.assertEqual(health.indeed_requests, 1)
        self.assertEqual(health.indeed_successes, 1)
        self.assertEqual(health.indeed_jobs_found, 2)
        self.assertEqual(health.indeed_failures, 0)

    def test_fetch_indeed_jobs_html_dom_fallback(self):
        mock_html = """
        <html><body>
          <div class="job_seen_beacon" data-jk="jk_dom_99">
            <h2 class="jobTitle"><a data-jk="jk_dom_99"><span>Solar Maintenance Lead</span></a></h2>
            <div data-testid="company-name">SolarTech Israel</div>
            <div data-testid="text-location">Arava</div>
            <div class="job-snippet">Hands-on solar field operations and BESS inverter maintenance.</div>
          </div>
        </body></html>
        """
        fake_response = SimpleNamespace(status_code=200, text=mock_html)
        health = RunHealth()

        with patch("src.fetchers.requests.get", return_value=fake_response), \
             patch("src.fetchers.cffi_requests", None), \
             patch("src.fetchers.time.sleep"):
            jobs = fetch_indeed_jobs(["Solar"], health, location="Israel", max_pages=1)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Solar Maintenance Lead")
        self.assertEqual(jobs[0]["company"], "SolarTech Israel")
        self.assertEqual(jobs[0]["link"], "https://il.indeed.com/viewjob?jk=jk_dom_99")
        self.assertEqual(jobs[0]["source"], "Indeed")
        self.assertEqual(health.indeed_successes, 1)
        self.assertEqual(health.indeed_jobs_found, 1)

    def test_fetch_indeed_jobs_handles_failure(self):
        fake_response = SimpleNamespace(status_code=403, text="Forbidden")
        health = RunHealth()

        with patch("src.fetchers.requests.get", return_value=fake_response), \
             patch("src.fetchers.cffi_requests", None), \
             patch("src.fetchers.time.sleep"):
            jobs = fetch_indeed_jobs(["SCADA"], health, location="Israel", max_pages=1)

        self.assertEqual(jobs, [])
        self.assertEqual(health.indeed_failures, 1)
        self.assertEqual(health.indeed_successes, 0)

    def test_fetch_glassdoor_jobs_success(self):
        mock_html = """
        <html><body>
          <ul>
            <li data-test="jobListing">
              <a data-test="job-title" href="/job-listing/turbines-field-technician-JV_123.htm?jl=123">Turbines Field Technician</a>
              <span class="compactEmployerName">Turbine Power Group4.3</span>
              <div data-test="emp-location">Tel Aviv, Israel</div>
              <div data-test="descSnippet">Turbine maintenance, gas generators and telemetry inspection.</div>
              <img src="https://media.glassdoor.com/logo.png" />
            </li>
          </ul>
        </body></html>
        """
        fake_response = SimpleNamespace(status_code=200, text=mock_html)
        health = RunHealth()

        with patch("src.fetchers.requests.get", return_value=fake_response), \
             patch("src.fetchers.time.sleep"):
            jobs = fetch_glassdoor_jobs(["Turbine"], health, location="Israel", max_pages=1)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Turbines Field Technician")
        self.assertEqual(jobs[0]["company"], "Turbine Power Group")
        self.assertEqual(jobs[0]["link"], "https://www.glassdoor.com/job-listing/turbines-field-technician-JV_123.htm")
        self.assertEqual(jobs[0]["location"], "Tel Aviv, Israel")
        self.assertEqual(jobs[0]["source"], "Glassdoor")
        self.assertEqual(jobs[0]["logo"], "https://media.glassdoor.com/logo.png")
        self.assertEqual(health.glassdoor_requests, 1)
        self.assertEqual(health.glassdoor_successes, 1)
        self.assertEqual(health.glassdoor_jobs_found, 1)

    def test_fetch_glassdoor_jobs_handles_failure(self):
        fake_response = SimpleNamespace(status_code=500, text="Server Error")
        health = RunHealth()

        with patch("src.fetchers.requests.get", return_value=fake_response), \
             patch("src.fetchers.time.sleep"):
            jobs = fetch_glassdoor_jobs(["Turbine"], health, location="Israel", max_pages=1)

        self.assertEqual(jobs, [])
        self.assertEqual(health.glassdoor_failures, 1)
        self.assertEqual(health.glassdoor_successes, 0)


if __name__ == "__main__":
    unittest.main()
