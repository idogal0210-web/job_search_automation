"""Unit tests for Groq (Llama 3.3 70B) runtime and multi-provider evaluation."""
import json
import unittest
from unittest.mock import MagicMock, patch

from src.fetchers import RunHealth
from src.gemini_runtime import EvaluationUnavailable
from src.groq_runtime import GroqPool
from src.pipeline import evaluate_candidates
from src.state_manager import EvaluationLedger


def sample_groq_response():
    data = {
        "status": "QUALIFIED",
        "technical_role": True,
        "match_score": 85,
        "concrete_matches_count": 3,
        "reasoning": "התאמה טכנית גבוהה למערכות אנרגיה סולארית",
        "sector_key": "solar",
        "sector": "סולארי",
        "location": "חיפה",
        "company_domain_product": "אנרגיה סולארית",
        "job_summary": "אחזקת שדות סולאריים",
        "experience_strengths": "ניסיון מעשי",
        "key_highlights": "התאמה גבוהה",
        "company_size": "בינונית",
        "junior_openness": "כן",
        "work_model": "שטח",
        "company_requirements": "הנדסאי מכונות"
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(data)}}]
    }
    return mock_resp


class TestGroqRuntime(unittest.TestCase):
    def test_missing_key_raises_unavailable(self):
        pool = GroqPool(api_key="")
        health = RunHealth()
        with self.assertRaises(EvaluationUnavailable):
            pool.evaluate("Test prompt", health)

    @patch("requests.post")
    def test_successful_evaluation(self, mock_post):
        mock_post.return_value = sample_groq_response()
        pool = GroqPool(api_key="gsk_test123")
        health = RunHealth()
        data = pool.evaluate("Test prompt", health)
        self.assertEqual(data["status"], "QUALIFIED")
        self.assertEqual(data["evaluation_source"], "groq")
        self.assertEqual(data["evaluation_model"], "llama-3.3-70b-versatile")
        self.assertTrue(data["evaluation_complete"])
        self.assertEqual(health.gemini_successes, 1)

    @patch("requests.post")
    def test_pipeline_fallback_to_groq_when_gemini_fails(self, mock_post):
        mock_post.return_value = sample_groq_response()
        groq_pool = GroqPool(api_key="gsk_test123")

        gemini_pool = MagicMock()
        gemini_pool.evaluate.side_effect = EvaluationUnavailable({"gemini-3.8-flash": "daily_quota"})

        ledger = MagicMock()
        ledger.jobs = {}

        job = {
            "link": "https://example.com/job/solar1",
            "title": "Solar Technician",
            "company": "SolarField Ltd",
            "snippet": "Maintenance of industrial solar PV systems, inverters and SCADA monitoring. " * 5
        }
        health = RunHealth()
        client = MagicMock()

        with patch.dict("os.environ", {"PREFER_GROQ": "false"}):
            passed, audit = evaluate_candidates(
                [job], client, health, ledger,
                pool=gemini_pool, groq_pool=groq_pool, enrich_job=lambda j: None
            )

        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["evaluation_source"], "groq")
        self.assertEqual(passed[0]["status"], "QUALIFIED")
        self.assertEqual(health.pending_evaluations, 0)

    @patch("requests.post")
    def test_pipeline_uses_groq_directly_when_gemini_none(self, mock_post):
        mock_post.return_value = sample_groq_response()
        groq_pool = GroqPool(api_key="gsk_test123")

        ledger = MagicMock()
        ledger.jobs = {}

        job = {
            "link": "https://example.com/job/solar2",
            "title": "Solar Technician",
            "company": "SolarField Ltd",
            "snippet": "Maintenance of industrial solar PV systems, inverters and SCADA monitoring. " * 5
        }
        health = RunHealth()

        passed, audit = evaluate_candidates(
            [job], None, health, ledger,
            groq_pool=groq_pool, enrich_job=lambda j: None
        )

        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["evaluation_source"], "groq")
        self.assertEqual(passed[0]["status"], "QUALIFIED")


if __name__ == "__main__":
    unittest.main()
