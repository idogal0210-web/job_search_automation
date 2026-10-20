"""Tests for Job Market Salary Intelligence Engine."""

import unittest
from src.salary_engine import evaluate_job_salary, extract_salary_from_ad, classify_role_category

class TestSalaryIntelligence(unittest.TestCase):
    def test_direct_ad_extraction_range(self):
        text = "דרוש הנדסאי מכונות, שכר מוצע: 14,000 - 18,000 ₪ בחודש בהתאם לניסיון."
        res = extract_salary_from_ad(text)
        self.assertIsNotNone(res)
        self.assertEqual(res["estimate_type"], "advertised")
        self.assertEqual(res["quality_level"], "high")
        self.assertEqual(res["salary_source_type"], "job_ad")
        self.assertIn("14,000 - 18,000", res["salary_range"])
        self.assertEqual(res["p25"], 14000)
        self.assertEqual(res["p75"], 18000)

    def test_direct_ad_extraction_k_notation(self):
        text = "Field Technician for solar systems. Comp: 15k-18k per month."
        res = extract_salary_from_ad(text)
        self.assertIsNotNone(res)
        self.assertEqual(res["estimate_type"], "advertised")
        self.assertEqual(res["quality_level"], "high")
        self.assertEqual(res["extracted_min"], 15000)
        self.assertEqual(res["extracted_max"], 18000)

    def test_direct_ad_extraction_hourly(self):
        text = "דרוש מפעיל מתקן, שכר 65 ש\"ח לשעה משרה מלאה."
        res = extract_salary_from_ad(text)
        self.assertIsNotNone(res)
        self.assertEqual(res["estimate_type"], "advertised")
        self.assertEqual(res["pay_period"], "hour")
        self.assertEqual(res["extracted_min"], 65 * 182)

    def test_benchmark_matrix_scada_shifts(self):
        job = {
            "title": "בקר חדר בקרה SCADA",
            "company": "חברת אנרגיה",
            "snippet": "עבודה במשמרות 24/7 וסופי שבוע, ניטור מערכות חשמל ובקרה",
            "sector_key": "scada"
        }
        res = evaluate_job_salary(job)
        self.assertEqual(res["estimate_type"], "market_estimate")
        self.assertEqual(res["quality_level"], "medium")
        self.assertEqual(res["salary_source_type"], "sector_benchmark")
        self.assertTrue(res["has_shifts"])
        self.assertIn("כולל משמרות 24/7", res["salary_source_label"])
        self.assertEqual(res["p25"], 16000)
        self.assertEqual(res["p75"], 21000)

    def test_benchmark_matrix_solar_car(self):
        job = {
            "title": "טכנאי שטח סולארי ואגירה",
            "company": "סולאר פתרונות",
            "snippet": "אחזקת שדות פוטו-וולטאיים כולל רכב צמוד מלא",
            "sector_key": "solar"
        }
        res = evaluate_job_salary(job)
        self.assertEqual(res["estimate_type"], "market_estimate")
        self.assertEqual(res["quality_level"], "medium")
        self.assertTrue(res["has_company_car"])
        self.assertIn("רכב צמוד", res["salary_range"])

    def test_graceful_abstention_outside_core(self):
        job = {
            "title": "מנהל קמפיינים PPC ומדיה דיגיטלית",
            "company": "חברת שיווק",
            "snippet": "ניהול תקציבי פרסום בגוגל ופייסבוק ללא ציון שכר",
            "sector_key": "marketing"
        }
        res = evaluate_job_salary(job)
        self.assertEqual(res["estimate_type"], "insufficient_data")
        self.assertEqual(res["quality_level"], "insufficient")
        self.assertEqual(res["salary_source_type"], "none")
        self.assertEqual(res["salary_range"], "לא צוין במודעה")
        self.assertIsNone(res["p25"])
        self.assertIsNone(res["p75"])

if __name__ == "__main__":
    unittest.main()
