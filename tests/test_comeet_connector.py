import unittest
from unittest.mock import MagicMock
from src.fetchers import RunHealth, fetch_comeet_jobs


class TestComeetConnector(unittest.TestCase):
    def test_fetch_comeet_jobs_success(self):
        sample_html = """
        <!doctype html>
        <html>
        <script>
        COMPANY_DATA = {"name": "Enlight"};
        COMPANY_POSITIONS_DATA = [
            {
                "name": "Solar Field Engineer",
                "uid": "AB.123",
                "location": {"name": "Israel", "city": "Rosh Haayin"},
                "url_active_page": "https://www.comeet.com/jobs/enlightenergy/99.006/solar-field-engineer/AB.123",
                "custom_fields": {
                    "details": [
                        {"name": "Description", "value": "<p>Responsible for solar PV maintenance.</p>"},
                        {"name": "Requirements", "value": "<ul><li>Practical engineer diploma</li></ul>"}
                    ]
                }
            }
        ];
        </script>
        </html>
        """
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_session.get.return_value = mock_response

        health = RunHealth()
        jobs = fetch_comeet_jobs("enlightenergy", "99.006", "Enlight", health_metrics=health, session=mock_session)

        self.assertEqual(len(jobs), 1)
        job = jobs[0]
        self.assertEqual(job["title"], "Solar Field Engineer")
        self.assertEqual(job["company"], "Enlight")
        self.assertEqual(job["source"], "Comeet")
        self.assertTrue(job["is_direct_ats"])
        self.assertIn("Rosh Haayin", job["location"])
        self.assertIn("Practical engineer diploma", job["snippet"])

        self.assertEqual(health.comeet_requests, 1)
        self.assertEqual(health.comeet_successes, 1)
        self.assertEqual(health.comeet_failures, 0)
        self.assertEqual(health.comeet_jobs_found, 1)

    def test_fetch_comeet_jobs_http_error(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_session.get.return_value = mock_response

        health = RunHealth()
        jobs = fetch_comeet_jobs(health_metrics=health, session=mock_session)
        self.assertEqual(jobs, [])
        self.assertEqual(health.comeet_failures, 1)

    def test_fetch_comeet_jobs_malformed_html(self):
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No positions here</body></html>"
        mock_session.get.return_value = mock_response

        health = RunHealth()
        jobs = fetch_comeet_jobs(health_metrics=health, session=mock_session)
        self.assertEqual(jobs, [])
        self.assertEqual(health.comeet_failures, 1)

    def test_fetch_comeet_jobs_network_exception(self):
        mock_session = MagicMock()
        mock_session.get.side_effect = TimeoutError("Connection timed out")

        health = RunHealth()
        jobs = fetch_comeet_jobs(health_metrics=health, session=mock_session)
        self.assertEqual(jobs, [])
        self.assertEqual(health.comeet_failures, 1)


if __name__ == "__main__":
    unittest.main()
