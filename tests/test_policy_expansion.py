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
        self.assertTrue(is_known_enterprise("אפולו פאוור"))
        self.assertTrue(is_known_enterprise("Aeronautics"))
        self.assertTrue(is_known_enterprise("בז\"ן"))
        self.assertTrue(is_known_enterprise("נטפים"))
        self.assertTrue(is_known_enterprise("חברת החשמל"))
        self.assertTrue(is_known_enterprise("נגה"))
        self.assertTrue(is_known_enterprise("mPrest"))
        self.assertFalse(is_known_enterprise("חברה בלתי מוכרת בע\"מ"))

    def test_target_companies_46_count_and_categories(self):
        from src.config import get_target_companies, get_target_company_tiers
        targets, categories = get_target_companies()
        self.assertEqual(len(targets), 46)
        self.assertEqual(len(categories), 3)
        self.assertEqual(len(categories["solar_and_bess"]), 17)
        self.assertEqual(len(categories["gas_and_energy_infrastructure"]), 15)
        self.assertEqual(len(categories["drones_uav_and_defense"]), 14)
        tiers = get_target_company_tiers()
        self.assertEqual(len(tiers.get("tier1_companies", [])), 32)
        self.assertEqual(len(tiers.get("tier2_companies", [])), 14)

    def test_tiered_priority_bonus_calculation(self):
        from src.evaluators import is_target_company, get_target_company_tier
        # Tier 1 checks (+10 bonus)
        t1_samples = [
            "Enlight", "Doral", "Energix", "Nofar", "SolarEdge", "Apollo Power",
            "OPC Energy", "Dalia Power", "חברת החשמל", "נגה", "Supergas", "Baran Group", "בז\"ן"
        ]
        for comp in t1_samples:
            is_tgt, cat = is_target_company(comp)
            tier = get_target_company_tier(comp)
            self.assertTrue(is_tgt, f"{comp} should be target company")
            self.assertEqual(tier, 1, f"{comp} should be Tier 1")

        # Tier 2 checks (+5 bonus)
        t2_samples = [
            "Elbit", "IAI", "Rafael", "Aeronautics", "BlueBird Aero Systems",
            "XTEND", "Percepto", "NextVision", "Spear UAV", "Steadicopter", "CopterPIX"
        ]
        for comp in t2_samples:
            is_tgt, cat = is_target_company(comp)
            tier = get_target_company_tier(comp)
            self.assertTrue(is_tgt, f"{comp} should be target company")
            self.assertEqual(tier, 2, f"{comp} should be Tier 2")

        # Non-target
        is_tgt, _ = is_target_company("חברה גנרית כלשהי")
        tier = get_target_company_tier("חברה גנרית כלשהי")
        self.assertFalse(is_tgt)
        self.assertEqual(tier, 0)

    def test_commute_radius_policy(self):
        # 1. Central location passes
        central_jobs = [
            {"title": "הנדסאי סולארי", "company": "Doral", "location": "תל אביב", "snippet": "במשרדי החברה"},
            {"title": "הנדסאי סולארי", "company": "Doral", "location": "פתח תקווה", "snippet": "עבודה במרכז"},
            {"title": "הנדסאי סולארי", "company": "Doral", "location": "ראשון לציון", "snippet": "באזור התעשייה"},
            {"title": "הנדסאי סולארי", "company": "Doral", "location": "נתניה", "snippet": "בפארק שיאים"}
        ]
        for job in central_jobs:
            with self.subTest(loc=job["location"]):
                self.assertIsNone(deterministic_filter(job))

        # 2. Distant North/South without vehicle/remote fails
        distant_jobs = [
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "חיפה", "snippet": "באתר החברה בחיפה"},
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "כרמיאל", "snippet": "עבודה יומיומית בכרמיאל"},
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "באר שבע", "snippet": "משרה מלאה בבאר שבע"},
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "דימונה", "snippet": "במפעל בדימונה"}
        ]
        for job in distant_jobs:
            with self.subTest(loc=job["location"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISQUALIFIED")
                self.assertEqual(res["disqualification_reason"], "location_out_of_range")

        # 3. Distant location with company car or remote passes
        exempt_jobs = [
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "חיפה", "snippet": "כולל רכב חברה ונסיעות בכל הארץ"},
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "באר שבע", "snippet": "משרת Remote מהבית"},
            {"title": "הנדסאי מכונות", "company": "חברה תעשייתית", "location": "חיפה", "snippet": "עבודה היברידית"}
        ]
        for job in exempt_jobs:
            with self.subTest(snippet=job["snippet"]):
                self.assertIsNone(deterministic_filter(job))

    def test_salary_floor_16k_policy(self):
        # Advertised max < 16,000 is disqualified
        low_jobs = [
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "שכר: 12,000 - 15,000 ₪ לחודש"},
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "משכורת: 15,500 ₪ לחודש"},
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "שכר עד 14,000 ₪ לחודש"}
        ]
        for job in low_jobs:
            with self.subTest(snippet=job["snippet"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISQUALIFIED")
                self.assertEqual(res["disqualification_reason"], "below_salary_floor")

        # Advertised max >= 16,000 passes
        valid_jobs = [
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "שכר: 16,000 - 19,000 ₪ לחודש"},
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "משכורת: 16,000 ₪ לחודש"},
            {"title": "הנדסאי סולארי", "company": "Doral", "snippet": "שכר: 18,000 - 22,000 ₪ לחודש"}
        ]
        for job in valid_jobs:
            with self.subTest(snippet=job["snippet"]):
                self.assertIsNone(deterministic_filter(job))

    def test_junior_project_manager_and_coordinator_policy(self):
        # Technical Junior PM / Coordinator passes
        valid_pm_jobs = [
            {"title": "Junior Project Manager", "company": "Enlight", "snippet": "ניהול פרויקטי הקמה סולאריים ואגירת אנרגיה"},
            {"title": "Project Coordinator", "company": "Energix", "snippet": "תיאום קבלנים בשדות סולאריים וחיבורי רשת"},
            {"title": "רכז הקמות", "company": "Doral", "snippet": "רכז הקמת פרויקטי אנרגיה מתחדשת"},
            {"title": "עוזר מנהל פרויקט", "company": "Lesico", "snippet": "פרויקטי תשתית צנרת וגז טבעי"},
            {"title": "PMO טכני", "company": "Baran Group", "snippet": "מעקב לו\"ז ותקציב בפרויקטים הנדסיים"},
            {"title": "Junior Site Manager", "company": "Shikun & Binui Energy", "snippet": "ניהול אתר הקמה סולארי"}
        ]
        for job in valid_pm_jobs:
            with self.subTest(title=job["title"]):
                self.assertIsNone(deterministic_filter(job))

        # Non-technical PM (marketing, HR, digital) is disqualified
        non_tech_pm_jobs = [
            {"title": "Junior Project Manager", "company": "Startup", "snippet": "שיווק דיגיטלי וקמפיינים בסושיאל"},
            {"title": "Project Coordinator", "company": "Agency", "snippet": "ניהול פרויקטי משאבי אנוש וגיוס עובדים"},
            {"title": "רכזת פרויקטים", "company": "Fintech", "snippet": "פרויקטים פיננסיים והנהלת חשבונות"},
            {"title": "עוזר מנהל פרויקט", "company": "Health", "snippet": "מחקר קליני ורגולציה רפואית"}
        ]
        for job in non_tech_pm_jobs:
            with self.subTest(title=job["title"]):
                res = deterministic_filter(job)
                self.assertIsNotNone(res)
                self.assertEqual(res["status"], "DISQUALIFIED")
                self.assertEqual(res["disqualification_reason"], "non_technical_pm")


if __name__ == "__main__":
    unittest.main()
