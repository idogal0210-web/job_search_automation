"""Unit tests verifying the redefined job profile and screening policies.
Adheres strictly to the zero-emoji mandatory rule.
"""
import unittest
from src.job_policy import (
    deterministic_filter,
    advertised_low_salary,
    KEYWORD_GROUPS
)
from src.config import (
    get_search_keywords,
    get_excluded_employers,
    get_target_companies
)


class TestJobProfileRedefinition(unittest.TestCase):
    def test_solar_and_bess_site_management_roles_pass(self):
        solar_roles = [
            {"title": "מנהל אתר סולארי", "company": "Enlight", "snippet": "ניהול פרויקט הקמה סולארי בערבה"},
            {"title": "Junior Solar Site Manager", "company": "Energix", "snippet": "C&I solar rooftop project coordination"},
            {"title": "רכז הקמות סולארי", "company": "Doral", "snippet": "ליווי קבלנים ותיאום עבודות שטח"},
            {"title": "BESS Commissioning Engineer", "company": "Nofar Energy", "snippet": "בדיקות קבלה ומסירה למתקני אגירה"},
            {"title": "מפקח איכות והקמות סולארי", "company": "SolarPower", "snippet": "בדיקות טיב ביצוע ופיקוח שטח"},
            {"title": "CleanTech Integration Specialist", "company": "Augwind", "snippet": "אינטגרציה של מערכות אגירה מתקדמות"}
        ]
        for role in solar_roles:
            with self.subTest(title=role["title"]):
                res = deterministic_filter(role)
                self.assertIsNone(res)

    def test_unconditional_24_7_shifts_rejection(self):
        shift_jobs = [
            {"title": "מפעיל חדר בקרה", "company": "OPC Energy", "snippet": "עבודה במשמרות 24/7 כולל לילות וסופ״ש"},
            {"title": "Solar Operations Controller", "company": "Enlight", "snippet": "סבב משמרות סביב השעון 24/7"},
            {"title": "טכנאי תחנת כוח", "company": "דליה אנרגיות", "snippet": "משמרות כולל לילות וסופי שבוע"},
            {"title": "Gas Plant Controller", "company": "דוראד", "snippet": "עבודה במשמרות 24/7"}
        ]
        for job in shift_jobs:
            with self.subTest(title=job["title"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISQUALIFIED")
                self.assertEqual(res["disqualification_reason"], "shifts_24_7_disqualified")

    def test_salary_floor_14k_rejection(self):
        low_salary_job = {
            "title": "הנדסאי סולארי",
            "company": "חברת שמש",
            "snippet": "שכר חודשי מוצע: 11,000 - 13,000 ₪ לחודש"
        }
        res = deterministic_filter(low_salary_job)
        self.assertIsNotNone(res)
        self.assertEqual(res["disqualification_reason"], "below_salary_floor")

        passing_salary_job = {
            "title": "הנדסאי סולארי",
            "company": "Enlight",
            "snippet": "שכר חודשי: 15,000 - 18,000 ₪ לחודש"
        }
        self.assertIsNone(deterministic_filter(passing_salary_job))

    def test_non_energy_factory_scada_rejection(self):
        factory_jobs = [
            {"title": "מפעיל חדר בקרה SCADA", "company": "מפעל מזון שער הנגב", "snippet": "בקרת קווי אריזה במפעל מזון"},
            {"title": "בקר BMS", "company": "קוקה קולה", "snippet": "בקרת מבנה במפעל משקאות מרכזי"},
            {"title": "מפעיל מכונה", "company": "מפעל פלסטיק", "snippet": "הפעלת מכונות הזרקת פלסטיק"}
        ]
        for job in factory_jobs:
            with self.subTest(company=job["company"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["disqualification_reason"], "non_energy_role")

    def test_excluded_staffing_and_security_agencies(self):
        staffing_jobs = [
            {"title": "מפעיל חדר בקרה", "company": "מוקד אמון בע\"מ", "snippet": "מוקדן בקרה"},
            {"title": "טכנאי שירות", "company": "דנאל משאבי אנוש", "snippet": "גיוס לחברה מובילה"},
            {"title": "מפעיל מערכות", "company": "צוות 3 ביטחון", "snippet": "שמירה ובקרה"}
        ]
        for job in staffing_jobs:
            with self.subTest(company=job["company"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["disqualification_reason"], "blacklist")

    def test_keyword_groups_contain_site_management_and_commissioning(self):
        self.assertIn("site_management", KEYWORD_GROUPS)
        self.assertIn("commissioning", KEYWORD_GROUPS)
        self.assertIn("cleantech", KEYWORD_GROUPS)

    def test_search_keywords_config_enriched(self):
        kw = get_search_keywords()
        energy_kw = kw.get("energy", [])
        self.assertTrue(any("Solar Site Manager" in k or "מנהל אתר סולארי" in k for k in energy_kw))
        self.assertTrue(any("Commissioning" in k or "מסירה" in k for k in energy_kw))


if __name__ == "__main__":
    unittest.main()
