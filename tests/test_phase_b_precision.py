"""
Tests for Phase B upgrades:
1. Salary engine context validation (no false positives from user/client numbers).
2. Shift and company car negation detection.
3. Normative vs explicit company car labeling.
4. Target company exact/boundary matching (no false positives like 'דליה כהן').
5. Control room threshold validation against raw job ad evidence.
"""

import unittest
from unittest.mock import MagicMock, patch
from src.salary_engine import evaluate_job_salary, extract_salary_from_ad, detect_shifts, detect_company_car
from src.evaluators import is_target_company, evaluate_and_enrich_job_with_gemini

class TestPhaseBPrecision(unittest.TestCase):

    def test_non_salary_counters_rejected(self):
        text = "חברה מובילה המשרתת מעל 10,000–20,000 משתמשים ביום."
        res = extract_salary_from_ad(text)
        self.assertIsNone(res)

    def test_explicit_salary_range_accepted(self):
        text = "שכר חודשי מוצע: 14,000 - 18,000 ₪ בהתאם לניסיון."
        res = extract_salary_from_ad(text)
        self.assertIsNotNone(res)
        self.assertEqual(res["salary_source_type"], "job_ad")
        self.assertIn("14,000 - 18,000", res["salary_range"])

    def test_shifts_negation(self):
        text = "משרה מלאה בימים א-ה, ללא משמרות וללא שבתות."
        self.assertFalse(detect_shifts(text))

    def test_company_car_negation(self):
        text = "טכנאי שטח סולארי, ללא רכב - נדרש רכב פרטי לצורך הגעה."
        self.assertFalse(detect_company_car(text))

    def test_normative_vs_explicit_car_label(self):
        # Normative car in solar benchmark without explicit ad mention
        res_norm = evaluate_job_salary({
            "title": "טכנאי שטח סולארי",
            "snippet": "תחזוקת פאנלים סולאריים",
            "sector_key": "solar"
        })
        self.assertIn("מקובל רכב ענפי", res_norm["salary_range"])
        self.assertFalse(res_norm["has_company_car"])
        self.assertTrue(res_norm["is_normative_vehicle"])

        # Explicit car in ad
        res_exp = evaluate_job_salary({
            "title": "טכנאי שטח סולארי",
            "snippet": "אחזקת שדות סולאריים כולל רכב חברה צמוד",
            "sector_key": "solar"
        })
        self.assertIn("+ רכב צמוד", res_exp["salary_range"])
        self.assertTrue(res_exp["has_company_car"])

    @patch('src.evaluators.TARGET_COMPANIES_BY_CATEGORY', {
        'natural_gas_israel': ['Dalia Power'],
        'drones_uav_and_defense': ['Elbit']})
    def test_target_company_no_false_substring_match(self):
        # 'דליה' is a target power station (Dalia Power), but 'דליה כהן חנות בגדים' must NOT match!
        is_target, _ = is_target_company("דליה כהן חנות בגדים בע\"מ")
        self.assertFalse(is_target)

        # Exact target matches
        is_target, cat = is_target_company("דליה אנרגיות")
        self.assertTrue(is_target)
        self.assertEqual(cat, "natural_gas_israel")

        is_target, cat = is_target_company("אלביט מערכות")
        self.assertTrue(is_target)
        self.assertEqual(cat, "drones_uav_and_defense")

    def test_control_room_threshold_rejects_generic_security(self):
        mock_client = MagicMock()
        # Mock Gemini returning a high match_score for a generic control room role without SCADA
        mock_resp = MagicMock()
        mock_resp.text = '{"match_score": 85, "concrete_matches_count": 3, "reasoning": "בקר בניין", "sector_key": "scada", "salary_range": "10,000 - 12,000 ₪"}'
        mock_client.models.generate_content.return_value = mock_resp
        mock_health = MagicMock()

        res = evaluate_and_enrich_job_with_gemini(
            client=mock_client,
            title="בקר חדר בקרה - פיקוח מתחם לוגיסטי",
            company="חברת ניהול נכסים",
            snippet="מענה לקריאות שירות בחניון ופתיחת מחסומים.",
            is_drone=False,
            health_metrics=mock_health
        )
        self.assertIsNotNone(res)
        self.assertEqual(res.get("status"), "DISQUALIFIED")
        self.assertEqual(res.get("match_score"), 0)
        self.assertEqual(res.get("disqualification_reason"), "control_room_lacks_scada_or_high_salary")

if __name__ == "__main__":
    unittest.main()
