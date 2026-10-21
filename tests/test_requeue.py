import tempfile
import unittest
from pathlib import Path
from scripts.requeue_jobs import requeue
from src.state_manager import EvaluationLedger


class RequeueTests(unittest.TestCase):
    def test_explicit_legacy_retry_without_erasing_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = EvaluationLedger(Path(tmp)/'ledger.json')
            job = {'link': 'https://example.com/1', 'title': 'Technician', 'company': 'Example', 'snippet': 'Technical duties'}
            handled = {job['link'], 'https://example.com/2'}
            requeue(ledger, [job])
            self.assertEqual(ledger.jobs, {})
            requeue(ledger, [job], apply=True)
            self.assertEqual(ledger.select([], handled)[0]['link'], job['link'])
            self.assertEqual(len(handled), 2)
            with self.assertRaises(ValueError):
                requeue(ledger, [{'link': 'not a job'}], apply=True)


if __name__ == '__main__':
    unittest.main()
