"""End-to-end orchestration with local state and mocked external services."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import main
from src.pipeline import evaluate_candidates
from test_recovery import APIError, pool, response


class MainIntegrationTests(unittest.TestCase):
    def test_outage_recovery_failed_email_and_cached_redelivery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            job = {'link': 'https://example.com/job/1', 'title': 'Solar Technician',
                   'company': 'Example', 'snippet': 'Industrial solar maintenance and commissioning. ' * 10}
            client = MagicMock()
            client.models.generate_content.side_effect = APIError(503)
            def evaluate(jobs, ai, health, ledger, **kwargs):
                runtime, _ = pool(('one',))
                kwargs.pop("pool", None)
                return evaluate_candidates(jobs, ai, health, ledger, pool=runtime, enrich_job=lambda j: None, **kwargs)
            delivery_success = [True, False, True]
            def send(*args):
                args[-1].email_success = delivery_success.pop(0)
            with patch.dict('os.environ', {'GEMINI_API_KEY': 'fake', 'SENDER_EMAIL': 'fake@example.com',
                                         'SENDER_APP_PASSWORD': 'fake'}, clear=True), \
                 patch.object(main, '__file__', str(root / 'main.py')), \
                 patch.object(main, 'STATE_FILE', str(root / 'data/jobs_state.json')), \
                 patch.object(main.genai, 'Client', return_value=client), \
                 patch.object(main, 'fetch_linkedin_jobs', return_value=[job]), \
                 patch.object(main, 'fetch_drushim_jobs', return_value=[]), \
                 patch.object(main, 'evaluate_candidates', side_effect=evaluate), \
                 patch.object(main, 'update_weekly_archive', side_effect=lambda jobs, *_: jobs), \
                 patch.object(main, 'build_and_save_docs_app'), \
                 patch.object(main, 'send_email_report', side_effect=send):
                self.assertEqual(main.main(), 0)  # degraded, not a fatal crash
                self.assertEqual(json.loads((root/'data/jobs_state.json').read_text()), [])
                self.assertEqual(json.loads((root/'reports/latest_run.json').read_text())['health']['final_status'], 'DEGRADED_PENDING')
                client.models.generate_content.side_effect = None
                client.models.generate_content.return_value = response()
                self.assertEqual(main.main(), 1)  # failed email, retain READY snapshot
                self.assertEqual(json.loads((root/'data/evaluation_state.json').read_text())['jobs'][job['link']]['stage'], 'READY')
                calls = client.models.generate_content.call_count
                self.assertEqual(main.main(), 0)
                self.assertEqual(client.models.generate_content.call_count, calls)
                self.assertEqual(json.loads((root/'data/jobs_state.json').read_text()), [job['link']])

    def test_dashboard_failure_keeps_ready_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'data').mkdir()
            job = {'link': 'https://example.com/job/2', 'title': 'Technician', 'status': 'QUALIFIED',
                   'match_score': 80, 'evaluation_complete': True, 'evaluation_source': 'gemini'}
            (root/'data/evaluation_state.json').write_text(json.dumps({'version': 1, 'jobs': {
                job['link']: {'stage': 'READY', 'job': job}}}))
            def send(*args):
                args[-1].email_success = True
            with patch.dict('os.environ', {'SENDER_EMAIL': 'fake', 'SENDER_APP_PASSWORD': 'fake'}, clear=True), \
                 patch.object(main, '__file__', str(root/'main.py')), \
                 patch.object(main, 'STATE_FILE', str(root/'data/jobs_state.json')), \
                 patch.object(main, 'fetch_linkedin_jobs', return_value=[]), \
                 patch.object(main, 'fetch_drushim_jobs', return_value=[]), \
                 patch.object(main, 'update_weekly_archive', side_effect=OSError('disk error')), \
                 patch.object(main, 'send_email_report', side_effect=send):
                self.assertEqual(main.main(), 1)
                self.assertEqual(json.loads((root/'data/evaluation_state.json').read_text())['jobs'][job['link']]['stage'], 'READY')


if __name__ == '__main__':
    unittest.main()
