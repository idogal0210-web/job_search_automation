import unittest
from src.gemini_runtime import Evaluation, RequirementAssessment, EvidenceQuote
from src.evaluators import validate_requirement_assessments


class TestRequirementAssessments(unittest.TestCase):
    def test_backward_compatibility_empty_assessments(self):
        # Ensure older evaluations without requirement_assessments still validate strictly
        raw = {
            "status": "QUALIFIED",
            "technical_role": True,
            "match_score": 85,
            "concrete_matches_count": 3,
            "reasoning": "Technical fit",
            "sector_key": "solar"
        }
        ev = Evaluation.model_validate(raw)
        self.assertEqual(ev.requirement_assessments, [])

    def test_valid_evidence_quotes(self):
        assessments = [
            {
                "requirement": "ניסיון מעשי ב-SCADA",
                "importance": "required",
                "ad_evidence": {"quote": "ניסיון במערכות SCADA", "source_field": "requirements"},
                "profile_evidence": {"quote": "24/7 mission-critical control room operations", "source_field": "experience"},
                "assessment": "match",
                "explanation": "התאמה מלאה למערכות בקרה"
            }
        ]
        raw_text = "דרוש טכנאי עם ניסיון במערכות SCADA ובקרת מבנה"
        validated = validate_requirement_assessments(assessments, raw_text)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["assessment"], "match")
        self.assertEqual(validated[0]["ad_evidence"]["quote"], "ניסיון במערכות SCADA")

    def test_hallucinated_quote_is_sanitized_to_unknown(self):
        assessments = [
            {
                "requirement": "מהנדס רשתות CCNA",
                "importance": "required",
                "ad_evidence": {"quote": "חובה תעודת CCNA של סיסקו", "source_field": "requirements"},
                "profile_evidence": {"quote": "", "source_field": ""},
                "assessment": "match",
                "explanation": "התאמה"
            }
        ]
        raw_text = "דרוש מפעיל חדר בקרה ללא דרישות תקשורת"
        validated = validate_requirement_assessments(assessments, raw_text)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["assessment"], "unknown")
        self.assertEqual(validated[0]["ad_evidence"]["source_field"], "unverified")
        self.assertIn("ציטוט המודעה לא אומת", validated[0]["explanation"])


if __name__ == "__main__":
    unittest.main()
