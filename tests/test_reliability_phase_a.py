import unittest
from unittest.mock import MagicMock
from src.evaluators import evaluate_and_enrich_job_with_gemini
from main import apply_keyword_fallback

class TestEvaluationAndFallbackReliability(unittest.TestCase):
    """
    Verifies Phase A fixes:
    1. Disqualified jobs return status DISQUALIFIED.
    2. Fallback rejects non-technical roles and blacklisted titles even if keywords exist.
    3. Technical errors vs business disqualifications are correctly distinguished.
    """

    def test_business_disqualification_sales_solar(self):
        # A sales role in solar energy must be DISQUALIFIED, not None or Qualified
        mock_client = MagicMock()
        mock_health = MagicMock()
        res = evaluate_and_enrich_job_with_gemini(
            client=mock_client,
            title="Sales Manager - Solar Energy",
            company="SolarCo",
            snippet="Join our team as Sales Manager selling residential PV systems.",
            is_drone=False,
            health_metrics=mock_health
        )
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "DISQUALIFIED")
        self.assertEqual(res.get("match_score"), 0)
        # Client should not even be called due to deterministic pre-filter
        mock_client.models.generate_content.assert_not_called()

    def test_business_disqualification_hr_recruiter(self):
        mock_client = MagicMock()
        mock_health = MagicMock()
        res = evaluate_and_enrich_job_with_gemini(
            client=mock_client,
            title="HR Recruiter - Energy Sector",
            company="EnergyHR",
            snippet="Looking for a recruiter to source technical talent for gas and solar projects.",
            is_drone=False,
            health_metrics=mock_health
        )
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "DISQUALIFIED")
        self.assertEqual(res.get("match_score"), 0)
        mock_client.models.generate_content.assert_not_called()

    def test_fallback_rejects_sales_job(self):
        # Even if keyword fallback is directly triggered, it should reject non-technical titles
        job = {
            "title": "Sales Representative - PV Panels",
            "snippet": "Excellent sales skills required for solar inverters and SCADA monitoring sales.",
            "company": "InvertCo"
        }
        res = apply_keyword_fallback(job)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "DISQUALIFIED")
        self.assertEqual(res.get("match_score"), 0)

    def test_fallback_defers_genuine_technical_job(self):
        job = {
            "title": "הנדסאי מכונות - מפעיל חדר בקרה SCADA",
            "snippet": "דרוש הנדסאי מכונות לתפעול ובקרה בתחנת כוח גז טבעי.",
            "company": "PowerPlant Ltd"
        }
        res = apply_keyword_fallback(job)
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "RETRY_PENDING")
        self.assertFalse(res["evaluation_complete"])
        self.assertGreater(res.get("keyword_score"), 0)

if __name__ == "__main__":
    unittest.main()
