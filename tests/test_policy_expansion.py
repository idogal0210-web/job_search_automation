import unittest
from src.job_policy import (
    deterministic_filter,
    advertised_high_salary,
    advertised_very_high_salary,
    advertised_low_salary,
    is_known_enterprise,
    KEYWORD_GROUPS
)


class PolicyExpansionTests(unittest.TestCase):
    def test_specialized_energy_roles_not_auto_rejected(self):
        titles = [
            "בקר תפעול מערכות אנרגיה מתחדשת ואגירה",
            "Renewable Energy & BESS Operator",
            "מתאם חיבורי רשת ותשתיות",
            "Grid Interconnection Coordinator",
            "מומחה תפעול מסחרי ורנומינציות",
            "Commercial Operations & Nominations Specialist",
            "אינטגרטור תפעול ואוטומציה לחדרי בקרה",
            "Operational Automation & SCADA Specialist",
            "מתאם התחשבנות מנייה וסליקה",
            "Energy Settlement & Billing Coordinator",
            "הנדסאי תפעול ואחזקת מתקני לחץ וגז",
            "Gas & Pressure Systems Operations Specialist",
            "בקר אנרגיה בכיר",
            "מנהל משמרת בקרה",
            "Senior Energy Dispatcher"
        ]
        for title in titles:
            with self.subTest(title=title):
                self.assertIsNone(deterministic_filter({"title": title, "company": "Energix"}))

    def test_low_salary_rejected(self):
        job = {
            "title": "הנדסאי מכונות",
            "company": "חברה תעשייתית",
            "snippet": "שכר חודשי: 12,000 - 14,000 ₪ לחודש"
        }
        res = deterministic_filter(job)
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "DISQUALIFIED")
        self.assertEqual(res["disqualification_reason"], "below_salary_floor")

    def test_manual_garage_work_rejected(self):
        garage_titles = [
            "מכונאי רכב מוסמך",
            "פחח וצמיגאי",
            "מרכיב בפס ייצור",
            "מרכיב מכני בפס"
        ]
        for title in garage_titles:
            with self.subTest(title=title):
                res = deterministic_filter({"title": title, "company": "מוסך דרום"})
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISQUALIFIED")
                self.assertEqual(res["disqualification_reason"], "manual_no_engineering_horizon")

    def test_control_room_24_7_policy(self):
        # 1. 24/7 rotating shifts are strictly disqualified unconditionally
        job_24_7 = {
            "title": "בקר חדר בקרה SCADA",
            "company": "חברה אנונימית",
            "snippet": "עבודה במשמרות 24/7 כולל לילות וסופ\"ש."
        }
        res_24_7 = deterministic_filter(job_24_7)
        self.assertIsNotNone(res_24_7)
        self.assertEqual(res_24_7["disqualification_reason"], "shifts_24_7_disqualified")

        # 2. 24/7 even in known enterprise is disqualified per strict user policy
        job_known_24_7 = {
            "title": "בקר חדר בקרה SCADA",
            "company": "OPC Energy",
            "snippet": "עבודה במשמרות 24/7 כולל לילות וסופ\"ש."
        }
        res_known_24_7 = deterministic_filter(job_known_24_7)
        self.assertIsNotNone(res_known_24_7)
        self.assertEqual(res_known_24_7["disqualification_reason"], "shifts_24_7_disqualified")

        # 3. Non-24/7 day work SCADA in known enterprise passes
        job_day_scada = {
            "title": "בקר חדר בקרה SCADA",
            "company": "OPC Energy",
            "snippet": "משרת יום א'-ה' בתחנת כוח, שעות נוספות לפי הצורך."
        }
        self.assertIsNone(deterministic_filter(job_day_scada))

        # 4. Non-energy factory SCADA is disqualified
        job_food_factory = {
            "title": "מפעיל חדר בקרה SCADA",
            "company": "מפעל מזון שער הנגב",
            "snippet": "בקרה על קווי אריזה וייצור במפעל מזון."
        }
        res_food = deterministic_filter(job_food_factory)
        self.assertIsNotNone(res_food)
        self.assertEqual(res_food["disqualification_reason"], "non_energy_role")

    def test_salary_detection_helpers(self):
        self.assertTrue(advertised_very_high_salary("שכר חודשי: 21,000 - 24,000 ₪"))
        self.assertFalse(advertised_very_high_salary("שכר חודשי: 18,000 - 19,000 ₪"))
        self.assertTrue(advertised_low_salary("משכורת: 12,000 ₪ לחודש"))
        self.assertFalse(advertised_low_salary("משכורת: 16,000 ₪ לחודש"))

    def test_known_enterprise_detection(self):
        self.assertTrue(is_known_enterprise("OPC Energy Ltd"))
        self.assertTrue(is_known_enterprise("אנלייט אנרגיה"))
        self.assertTrue(is_known_enterprise("אלביט מערכות"))
        self.assertFalse(is_known_enterprise("חברה בלתי מוכרת בע\"מ"))


if __name__ == "__main__":
    unittest.main()
