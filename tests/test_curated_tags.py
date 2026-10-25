import unittest
from src.job_policy import extract_curated_tags


class TestCuratedTags(unittest.TestCase):
    def test_stated_salary_positive(self):
        job = {
            "title": "Solar Technician",
            "salary_source_type": "job_ad",
            "salary_range": "15,000 - 18,000 ₪"
        }
        res = extract_curated_tags(job)
        self.assertEqual(res["stated_ad_salary"], "15,000 - 18,000 ₪")
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertIn("tag-salary", tag_types)
        self.assertEqual(res["curated_tags"][0]["label"], "15,000 - 18,000 ₪")

    def test_predicted_salary_is_never_tagged(self):
        job = {
            "title": "Solar Technician",
            "salary_source_type": "predicted",
            "salary_range": "15,000 - 18,000 ₪"
        }
        res = extract_curated_tags(job)
        self.assertIsNone(res["stated_ad_salary"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-salary", tag_types)

    def test_empty_or_placeholder_salary_is_not_tagged(self):
        job = {
            "title": "Solar Technician",
            "salary_source_type": "job_ad",
            "salary_range": "לא צוין במודעה"
        }
        res = extract_curated_tags(job)
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-salary", tag_types)

    def test_field_work_positive(self):
        job = {
            "title": "טכנאי שטח סולארי",
            "snippet": "עבודת שטח במתקני PV ברחבי הארץ"
        }
        res = extract_curated_tags(job)
        self.assertTrue(res["is_field_work"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertIn("tag-field", tag_types)

    def test_field_work_negative_guard(self):
        job = {
            "title": "מנהל תיקי לקוחות",
            "snippet": "עבודה משרדית מלאה - ללא עבודת שטח"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["is_field_work"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-field", tag_types)

    def test_company_car_positive(self):
        job = {
            "title": "הנדסאי שירות",
            "snippet": "התפקיד כולל רכב חברה צמוד ודלקן"
        }
        res = extract_curated_tags(job)
        self.assertTrue(res["provides_company_car"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertIn("tag-car", tag_types)

    def test_company_car_license_only_is_not_tagged(self):
        job = {
            "title": "הנדסאי שירות",
            "snippet": "דרישות: רישיון נהיגה ב בתוקף"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["provides_company_car"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-car", tag_types)

    def test_company_car_negative_guard(self):
        job = {
            "title": "הנדסאי שירות",
            "snippet": "נא לשים לב - התפקיד הינו ללא רכב חברה"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["provides_company_car"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-car", tag_types)

    def test_shifts_24_7_positive(self):
        job = {
            "title": "מפעיל חדר בקרה",
            "snippet": "עבודה במשמרות 24/7 כולל סופי שבוע ולילות"
        }
        res = extract_curated_tags(job)
        self.assertTrue(res["is_shifts_24_7"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertIn("tag-shifts", tag_types)

    def test_shifts_24_7_negative_guard(self):
        job = {
            "title": "מפעיל מתקן",
            "snippet": "משרה יומית סטנדרטית, ללא משמרות 24/7"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["is_shifts_24_7"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-shifts", tag_types)

    def test_junior_positive(self):
        job = {
            "title": "Junior Automation Technician",
            "snippet": "מתאים למתחילים / בוגרי הנדסאי ללא ניסיון, הכשרה מלאה"
        }
        res = extract_curated_tags(job)
        self.assertTrue(res["is_junior_friendly"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertIn("tag-junior", tag_types)

    def test_junior_negative_guard_senior(self):
        job = {
            "title": "Senior Control Engineer",
            "snippet": "דרישות: ניסיון של 5 שנים לפחות בתחום"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["is_junior_friendly"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-junior", tag_types)

    def test_junior_negative_guard_explicit(self):
        job = {
            "title": "מהנדס מערכות",
            "snippet": "התפקיד אינו מתאים למתחילים, לא מתאים לג'וניור"
        }
        res = extract_curated_tags(job)
        self.assertFalse(res["is_junior_friendly"])
        tag_types = [t["type"] for t in res["curated_tags"]]
        self.assertNotIn("tag-junior", tag_types)

    def test_capacity_limit_max_five_tags(self):
        job = {
            "title": "Junior Field Specialist",
            "salary_source_type": "job_ad",
            "salary_range": "16,000 ₪",
            "snippet": "עבודת שטח עם רכב חברה צמוד, משמרות 24/7, מתאים למתחילים"
        }
        res = extract_curated_tags(job)
        self.assertLessEqual(len(res["curated_tags"]), 5)
        self.assertEqual(len(res["curated_tags"]), 5)


if __name__ == "__main__":
    unittest.main()
