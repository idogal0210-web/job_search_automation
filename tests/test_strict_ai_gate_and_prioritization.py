import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.fetchers import RunHealth
from src.gemini_runtime import EvaluationUnavailable
from src.pipeline import evaluate_candidates
from src.state_manager import EvaluationLedger


class TestStrictAiGateAndPrioritization(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger_path = Path(self.tmp.name) / "evaluation_state.json"
        self.ledger = EvaluationLedger(self.ledger_path)
        self.base_job = {
            "link": "https://example.com/job/new-1",
            "title": "Solar Energy Field Operator",
            "company": "SolarField Ltd",
            "snippet": "Field maintenance technician for solar inverters and SCADA monitoring systems with high reliability.",
            "source": "Direct",
            "location": "Tel Aviv",
        }

    def tearDown(self):
        self.tmp.cleanup()

    def test_keyword_fallback_cannot_qualify_or_publish(self):
        """Verify strict AI-only gate: keyword fallback never qualifies and remains RETRY_PENDING."""
        health = RunHealth()
        # When client is None, pipeline falls back to keyword_fallback
        passed, audit = evaluate_candidates(
            [self.base_job],
            client=None,
            health=health,
            ledger=self.ledger,
            enrich_job=lambda j: None,
        )

        # 1. Must NOT be in passed (which feeds docs/data/jobs.json and email)
        self.assertEqual(passed, [])
        self.assertEqual(health.jobs_passed, 0)

        # 2. Audit record must reflect RETRY_PENDING and 0 match score
        self.assertEqual(len(audit), 1)
        record = audit[0]
        self.assertEqual(record["status"], "RETRY_PENDING")
        self.assertEqual(record["evaluation_source"], "keyword_fallback")
        self.assertEqual(record["match_score"], 0)

        # 3. Ledger stage must remain RETRY_PENDING (never READY or COMPLETE)
        ledger_entry = self.ledger.jobs[self.base_job["link"]]
        self.assertEqual(ledger_entry["stage"], "RETRY_PENDING")
        self.assertEqual(ledger_entry["job"]["status"], "RETRY_PENDING")
        self.assertFalse(ledger_entry["job"]["evaluation_complete"])

    def test_pool_unavailable_forces_retry_pending_and_zero_score(self):
        """Simulate EvaluationUnavailable raised by GeminiPool."""
        health = RunHealth()
        mock_client = MagicMock()

        with patch("src.pipeline.evaluate_and_enrich_job_with_gemini", side_effect=EvaluationUnavailable({"gemini": "quota_exhausted"})):
            passed, audit = evaluate_candidates(
                [self.base_job],
                client=mock_client,
                health=health,
                ledger=self.ledger,
                enrich_job=lambda j: None,
            )

        self.assertEqual(passed, [])
        self.assertEqual(audit[0]["status"], "RETRY_PENDING")
        self.assertEqual(audit[0]["match_score"], 0)
        self.assertEqual(self.ledger.jobs[self.base_job["link"]]["stage"], "RETRY_PENDING")

    def test_new_jobs_prioritized_over_retry_pending(self):
        """Verify that raw new jobs from current run are prioritized ahead of RETRY_PENDING queue."""
        # 1. Populate ledger with an unresolved RETRY_PENDING job from past run
        stale_pending_job = {
            "link": "https://example.com/job/stale-pending",
            "title": "SCADA Operator",
            "company": "OldGrid Corp",
            "snippet": "SCADA control room operator position from last week.",
            "source": "Direct",
        }
        self.ledger.jobs[stale_pending_job["link"]] = {
            "stage": "RETRY_PENDING",
            "job": stale_pending_job,
            "attempts": 1,
            "updated_at": "2026-11-20T10:00:00+00:00",
        }
        self.ledger.save()

        # 2. New job arrives in raw_jobs
        new_job = {
            "link": "https://example.com/job/fresh-today",
            "title": "UAV Technician",
            "company": "DroneAero Ltd",
            "snippet": "Fresh UAV maintenance and flight systems role discovered today.",
            "source": "Direct",
        }

        # 3. Call ledger.select
        selected = self.ledger.select([new_job], handled=set())

        # 4. Verify new job is evaluated first, before stale pending job
        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]["link"], new_job["link"])
        self.assertEqual(selected[1]["link"], stale_pending_job["link"])

    def test_ready_jobs_precede_new_jobs_and_pending(self):
        """Verify READY jobs precede new jobs (0 AI cost delivery), and new jobs precede RETRY_PENDING."""
        ready_job = {
            "link": "https://example.com/job/ready-cached",
            "title": "Gas Turbine Engineer",
            "company": "GasPower Ltd",
            "snippet": "Gas turbine maintenance engineer ready for delivery.",
            "source": "Direct",
            "status": "QUALIFIED",
            "evaluation_complete": True,
            "match_score": 90,
        }
        pending_job = {
            "link": "https://example.com/job/pending-item",
            "title": "BESS Specialist",
            "company": "StoragePower",
            "snippet": "Battery energy storage technician.",
            "source": "Direct",
        }
        self.ledger.jobs[ready_job["link"]] = {
            "stage": "READY",
            "job": ready_job,
            "attempts": 1,
            "updated_at": "2026-11-24T08:00:00+00:00",
        }
        self.ledger.jobs[pending_job["link"]] = {
            "stage": "RETRY_PENDING",
            "job": pending_job,
            "attempts": 1,
            "updated_at": "2026-11-24T08:00:00+00:00",
        }
        self.ledger.save()

        fresh_job = {
            "link": "https://example.com/job/fresh-item",
            "title": "Solar Field Tech",
            "company": "SunTech Ltd",
            "snippet": "Solar field technician.",
            "source": "Direct",
        }

        selected = self.ledger.select([fresh_job], handled=set())
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected[0]["link"], ready_job["link"])
        self.assertEqual(selected[1]["link"], fresh_job["link"])
        self.assertEqual(selected[2]["link"], pending_job["link"])

    def test_complete_records_prune_bulk_snippets_and_descriptions(self):
        """Verify that COMPLETE jobs shed snippets and descriptions to prevent ledger bloat."""
        disqualified_job = {
            "link": "https://example.com/job/hr-role",
            "title": "HR Recruiter",
            "company": "PeopleCorp",
            "snippet": "Long recruiter job description " * 50,
            "description": "Full recruiter text " * 50,
            "source": "Direct",
        }
        self.ledger.record(disqualified_job, {
            "status": "DISQUALIFIED",
            "evaluation_complete": True,
            "match_score": 0,
            "disqualification_reason": "role_fit",
        })

        entry = self.ledger.jobs[disqualified_job["link"]]
        self.assertEqual(entry["stage"], "COMPLETE")
        self.assertEqual(entry["job"]["snippet"], "")
        self.assertEqual(entry["job"]["description"], "")
        self.assertEqual(entry["job"]["status"], "DISQUALIFIED")


if __name__ == "__main__":
    unittest.main()
