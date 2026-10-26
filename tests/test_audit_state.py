import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src.state_manager import EvaluationLedger


class LedgerWriteTests(unittest.TestCase):
    def test_staging_only_writes_new_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = EvaluationLedger(Path(directory) / "state.json")
            job = {"link": "https://example.com/jobs/1"}
            with patch.object(ledger, "save") as save:
                ledger.stage_candidates([])
                save.assert_not_called()
                ledger.stage_candidates([job])
                save.assert_called_once()
                ledger.stage_candidates([job])
                save.assert_called_once()
            ledger.save()
            restored = EvaluationLedger(ledger.path)
            self.assertEqual(restored.jobs, ledger.jobs)
