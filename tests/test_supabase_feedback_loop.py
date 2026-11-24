"""Unit tests for Supabase Few-Shot Feedback Loop (TASK-100)."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.fetchers import RunHealth
from src.evaluators import evaluate_and_enrich_job_with_gemini
from src.supabase_feedback import (
    build_catalog_job_index,
    fetch_triage_feedback_keys,
    format_few_shot_prompt_block,
    get_few_shot_block,
    get_few_shot_calibration_data,
)


class TestSupabaseFeedbackLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root_dir = Path(self.tmp.name)

        # Create mock catalog and sync_state files
        data_dir = self.root_dir / "data"
        docs_data_dir = self.root_dir / "docs" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        docs_data_dir.mkdir(parents=True, exist_ok=True)

        self.mock_sync_state = {
            "starred": [
                "https://example.com/job/star-1",
                "https://example.com/job/star-2",
            ],
            "rejected": [
                "https://example.com/job/rej-1",
            ],
            "saved": [],
            "purged": [],
        }
        (data_dir / "sync_state.json").write_text(json.dumps(self.mock_sync_state), encoding="utf-8")

        self.mock_catalog = {
            "https://example.com/job/star-1": {
                "link": "https://example.com/job/star-1",
                "title": "Solar Construction Site Coordinator",
                "company": "SunCorp Ltd",
                "job_summary": "Field management of utility scale solar project installation and commissioning.",
            },
            "https://example.com/job/star-2": {
                "link": "https://example.com/job/star-2",
                "title": "BESS Technical Integration Engineer",
                "company": "BatteryTech",
                "job_summary": "Grid interconnection and commissioning of commercial battery storage systems.",
            },
            "https://example.com/job/rej-1": {
                "link": "https://example.com/job/rej-1",
                "title": "Packaging Line Mechanic",
                "company": "FoodFactory Corp",
                "job_summary": "Routine maintenance of conveyor belts and bottling packaging lines 24/7.",
            },
        }
        (data_dir / "historical_catalog.json").write_text(json.dumps(self.mock_catalog), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_fetch_triage_keys_from_supabase_mock(self):
        """Verify successful remote retrieval from Supabase REST endpoint."""
        mock_payload = {
            "starred": ["https://example.com/job/remote-star"],
            "rejected": ["https://example.com/job/remote-rej"],
        }
        mock_rows = [{"payload": mock_payload, "updated_at": "2026-11-24T12:00:00Z"}]

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps(mock_rows).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp

        with patch("urllib.request.urlopen", return_value=mock_resp):
            keys = fetch_triage_feedback_keys(supabase_url="https://fake.supabase.co", supabase_key="fake-key")

        self.assertEqual(keys["starred"], ["https://example.com/job/remote-star"])
        self.assertEqual(keys["rejected"], ["https://example.com/job/remote-rej"])

    def test_fetch_triage_keys_falls_back_silently_to_local(self):
        """Verify graceful silent fallback to data/sync_state.json when Supabase network fails."""
        with patch("urllib.request.urlopen", side_effect=OSError("Network unreachable")):
            keys = fetch_triage_feedback_keys(
                supabase_url="https://fake.supabase.co",
                supabase_key="fake-key",
                fallback_file=self.root_dir / "data" / "sync_state.json",
            )

        self.assertEqual(len(keys["starred"]), 2)
        self.assertEqual(len(keys["rejected"]), 1)
        self.assertIn("https://example.com/job/star-1", keys["starred"])

    def test_fetch_triage_keys_empty_when_all_fail(self):
        """Verify that when both network and local files fail, empty lists are returned without crashing."""
        nonexistent = self.root_dir / "nonexistent.json"
        with patch("urllib.request.urlopen", side_effect=Exception("Unknown error")):
            keys = fetch_triage_feedback_keys(
                supabase_url="https://fake.supabase.co",
                fallback_file=nonexistent,
            )

        self.assertEqual(keys, {"starred": [], "rejected": []})

    def test_get_few_shot_calibration_data_matches_catalog(self):
        """Verify matching triage keys to catalog items without PII."""
        index = build_catalog_job_index(root_dir=self.root_dir)
        calib = get_few_shot_calibration_data(
            max_starred=5,
            max_rejected=5,
            catalog_index=index,
            feedback_keys=self.mock_sync_state,
        )

        self.assertEqual(len(calib["starred"]), 2)
        self.assertEqual(len(calib["rejected"]), 1)
        self.assertEqual(calib["starred"][0]["company"], "BatteryTech")
        self.assertEqual(calib["starred"][1]["company"], "SunCorp Ltd")
        self.assertEqual(calib["rejected"][0]["company"], "FoodFactory Corp")

    def test_format_few_shot_prompt_block_structure_and_bounds(self):
        """Verify formatting of the few-shot block and bounded length."""
        calib = {
            "starred": [
                {"company": "Enlight", "title": "PM Construction", "summary": "Solar site coordination"},
            ],
            "rejected": [
                {"company": "ACME", "title": "Shift Laborer", "summary": "24/7 rotating night shifts"},
            ],
        }
        block = format_few_shot_prompt_block(calib)
        self.assertIn("Candidate triage calibration", block)
        self.assertIn("Enlight - PM Construction", block)
        self.assertIn("ACME - Shift Laborer", block)
        self.assertLessEqual(len(block), 1200)

        # Empty data yields empty string
        empty_block = format_few_shot_prompt_block({"starred": [], "rejected": []})
        self.assertEqual(empty_block, "")

    def test_evaluate_and_enrich_job_injects_few_shot_block(self):
        """Verify that evaluate_and_enrich_job_with_gemini passes few_shot_context into prompt."""
        custom_few_shot = "Candidate triage calibration:\n- Test Company | Test Role\n\n"
        mock_client = MagicMock()
        mock_pool = MagicMock()
        mock_pool.evaluate.return_value = {
            "match_score": 85,
            "status": "QUALIFIED",
            "technical_role": True,
            "concrete_matches_count": 3,
            "sector_key": "solar",
            "evaluation_model": "mock",
            "evaluation_source": "gemini",
            "evaluation_complete": True,
            "requirement_assessments": [
                {"requirement": "solar", "importance": "required", "assessment": "match", "ad_evidence": {"quote": "solar exp"}}
            ],
        }

        evaluate_and_enrich_job_with_gemini(
            mock_client,
            title="Solar Project Coordinator",
            company="Enlight",
            snippet="Solar project coordination and field execution.",
            is_drone=False,
            health_metrics=RunHealth(),
            pool=mock_pool,
            few_shot_context=custom_few_shot,
        )

        self.assertTrue(mock_pool.evaluate.called)
        sent_prompt = mock_pool.evaluate.call_args[0][1]
        self.assertIn("Candidate triage calibration", sent_prompt)
        self.assertIn("Test Company | Test Role", sent_prompt)


if __name__ == "__main__":
    unittest.main()
