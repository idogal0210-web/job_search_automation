import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.evaluators import evaluate_and_enrich_job_with_gemini, is_target_company
from src.fetchers import RunHealth
from src.gemini_runtime import Evaluation, EvaluationUnavailable, GeminiPool, classify_error
from src.job_policy import apply_keyword_fallback, advertised_high_salary, deterministic_filter, is_drone_job
from src.pipeline import evaluate_candidates, final_status
from src.publishers import build_unified_html_email
from src.state_manager import EvaluationLedger, load_state, save_state_atomic


def response(**overrides):
    data = dict(status='QUALIFIED', technical_role=True, match_score=80,
                concrete_matches_count=3, reasoning='התאמה טכנית', sector_key='energy')
    data['requirement_assessments'] = [
        {'requirement': requirement, 'importance': 'preferred',
         'ad_evidence': {'quote': quote, 'source_field': 'snippet'},
         'profile_evidence': {'quote': profile, 'source_field': 'profile'},
         'assessment': 'match'}
        for requirement, quote, profile in [
            ('Technical maintenance', 'maintenance', 'troubleshooting'),
            ('Industrial systems', 'industrial', 'Electro-mechanical systems')]]
    data.update(overrides)
    return SimpleNamespace(text=json.dumps(data))


class APIError(Exception):
    def __init__(self, code, message='error', wait=None):
        self.code = code
        self.response = SimpleNamespace(headers={'Retry-After': str(wait)} if wait else {})
        super().__init__(message)


class Clock:
    def __init__(self):
        self.now = 0
        self.sleeps = []
    def __call__(self):
        return self.now
    def sleep(self, duration):
        self.sleeps.append(duration)
        self.now += duration


def pool(models=('one', 'two'), attempts=2):
    clock = Clock()
    runtime = GeminiPool(models, clock=clock, sleep=clock.sleep, jitter=lambda: 0,
                         max_attempts=attempts, min_interval=0)
    return runtime, clock


class ModelRecoveryTests(unittest.TestCase):
    def test_429_is_not_assumed_daily(self):
        self.assertEqual(classify_error(APIError(429, 'quota exceeded per minute')), 'rate_limit')
        self.assertEqual(classify_error(APIError(429, 'GenerateRequestsPerDay')), 'daily_quota')

    def test_retry_and_cooldown_are_per_model(self):
        runtime, clock = pool()
        client = MagicMock()
        client.models.generate_content.side_effect = [APIError(503), APIError(503), response(), response()]
        health = RunHealth()
        self.assertEqual(runtime.evaluate(client, 'prompt', health)['evaluation_model'], 'two')
        self.assertEqual(runtime.evaluate(client, 'prompt', health)['evaluation_model'], 'two')
        self.assertEqual([c.kwargs['model'] for c in client.models.generate_content.call_args_list], ['one', 'one', 'two', 'two'])
        clock.now += 30
        client.models.generate_content.side_effect = None
        client.models.generate_content.return_value = response()
        self.assertEqual(runtime.evaluate(client, 'prompt', health)['evaluation_model'], 'one')
        self.assertEqual(health.gemini_successes, 3)

    def test_daily_quota_only_disables_affected_model(self):
        runtime, _ = pool()
        client = MagicMock()
        client.models.generate_content.side_effect = [APIError(429, 'daily quota'), response(), response()]
        runtime.evaluate(client, 'prompt', RunHealth())
        runtime.evaluate(client, 'prompt', RunHealth())
        self.assertEqual(client.models.generate_content.call_count, 3)

    def test_all_unavailable_returns_pending_signal(self):
        runtime, _ = pool()
        client = MagicMock()
        client.models.generate_content.side_effect = APIError(503)
        with self.assertRaises(EvaluationUnavailable):
            runtime.evaluate(client, 'p', RunHealth())
        self.assertEqual(client.models.generate_content.call_count, 4)
        with self.assertRaises(EvaluationUnavailable):
            runtime.evaluate(client, 'p', RunHealth())
        self.assertEqual(client.models.generate_content.call_count, 4)

    def test_json_retry_same_model_then_recovers(self):
        runtime, _ = pool()
        client = MagicMock()
        client.models.generate_content.side_effect = [SimpleNamespace(text='{broken'), response()]
        result = runtime.evaluate(client, 'p', RunHealth())
        self.assertEqual(result['evaluation_model'], 'one')
        self.assertEqual(client.models.generate_content.call_count, 2)

    def test_schema_rejects_boolean_score_out_of_range_and_missing_role(self):
        for overrides in ({'match_score': True}, {'match_score': 101}, {'concrete_matches_count': -1}, {'sector_key': 'invented'}):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                Evaluation.model_validate_json(response(**overrides).text)
        data = json.loads(response().text)
        del data['technical_role']
        with self.assertRaises(ValueError):
            Evaluation.model_validate(data)

    def test_long_retry_after_does_not_block_other_models(self):
        runtime, clock = pool()
        client = MagicMock()
        client.models.generate_content.side_effect = [APIError(429, wait=120), response()]
        self.assertEqual(runtime.evaluate(client, 'p', RunHealth())['evaluation_model'], 'two')
        self.assertEqual(clock.now, 0)
        self.assertGreaterEqual(runtime.states['one'].open_until, 120)

    def test_timeout_retried_but_config_error_not_retried(self):
        for error, calls in ((TimeoutError('timed out'), 2), (APIError(404), 1)):
            runtime, _ = pool(('one',))
            client = MagicMock()
            client.models.generate_content.side_effect = error
            with self.assertRaises(EvaluationUnavailable):
                runtime.evaluate(client, 'p', RunHealth())
            self.assertEqual(client.models.generate_content.call_count, calls)


class PolicyTests(unittest.TestCase):
    def test_technical_titles_are_not_auto_rejected(self):
        for title in ('BESS Presales Engineer', 'Technical Customer Support Specialist', 'מפעיל מוקד בקרה SCADA'):
            with self.subTest(title=title):
                self.assertIsNone(deterministic_filter({'title': title}))

    def test_obvious_noise_is_rejected(self):
        for title in ('דרוש/ה קצב למפעל בקר', 'מחסנאי/ת לבקר תנובה', 'Sales Manager - Solar Energy'):
            self.assertEqual(deterministic_filter({'title': title})['status'], 'DISQUALIFIED')

    def test_generic_control_room_rejected_in_fallback(self):
        self.assertEqual(apply_keyword_fallback({'title': 'בקר חדר בקרה', 'snippet': 'חניון ומחסומים'})['disqualification_reason'],
                         'control_room_lacks_scada_or_high_salary')

    def test_salary_gate_uses_monthly_lower_bound(self):
        self.assertTrue(advertised_high_salary('שכר חודשי: 18,500 - 20,000 ₪'))
        for text in ('שכר חודשי: 14,000 - 18,000 ₪', 'שכר עד 20,000 ₪ לחודש',
                     'שכר 100 ₪ לשעה', 'salary 20,000 USD per month', 'שכר גבוה מאוד',
                     'שכר 18,000 ₪ נטו לחודש'):
            self.assertFalse(advertised_high_salary(text), text)

    def test_drone_detection_hebrew_and_sector(self):
        self.assertTrue(is_drone_job({'title': 'אינטגרטור רחפנים'}))
        self.assertTrue(is_drone_job({'sector_key': 'cuas'}))
        self.assertFalse(is_drone_job({'title': 'Gas Plant Operator'}))

    @patch('src.evaluators.TARGET_COMPANIES', [])
    @patch('src.evaluators.TARGET_COMPANIES_BY_CATEGORY', {})
    def test_alias_does_not_create_unapproved_target(self):
        self.assertFalse(is_target_company('אלביט מערכות')[0])

    def evaluate(self, *, title='Practical Engineer', drone=False, **overrides):
        client = MagicMock()
        client.models.generate_content.return_value = response(**overrides)
        runtime, _ = pool(('one',))
        with patch('src.evaluators.is_target_company', return_value=(True, 'solar')):
            result = evaluate_and_enrich_job_with_gemini(client, title, 'SolarEdge',
                'Technical maintenance of industrial systems.', drone, RunHealth(), pool=runtime)
        return result, client

    def test_bonus_once_after_eligibility(self):
        result, client = self.evaluate(match_score=86)
        self.assertEqual((result['base_match_score'], result['priority_bonus'], result['match_score']), (86, 5, 91))
        prompt = client.models.generate_content.call_args.kwargs['contents']
        self.assertIn('without any employer preference bonus', prompt)

    def test_bonus_cannot_push_drone_over_threshold(self):
        result, _ = self.evaluate(drone=True, match_score=68)
        self.assertEqual(result['status'], 'DISQUALIFIED')
        self.assertEqual(result['priority_bonus'], 0)

    def test_ai_drone_classification_also_uses_drone_threshold(self):
        result, _ = self.evaluate(sector_key='drones', match_score=68)
        self.assertEqual(result['status'], 'DISQUALIFIED')

    def test_target_does_not_rescue_rejection_or_low_matches(self):
        for overrides in ({'technical_role': False}, {'status': 'DISQUALIFIED'}, {'concrete_matches_count': 1}):
            result, _ = self.evaluate(match_score=95, **overrides)
            self.assertEqual(result['status'], 'DISQUALIFIED')
            self.assertEqual(result['priority_bonus'], 0)

    def test_target_sales_filtered_before_api(self):
        result, client = self.evaluate(title='Sales Manager - Solar Energy')
        self.assertEqual(result['status'], 'DISQUALIFIED')
        client.models.generate_content.assert_not_called()


class StateAndPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'ledger.json'
        self.ledger = EvaluationLedger(self.path)
        self.job = {'link': 'https://example.com/job/1', 'title': 'Solar Technician',
                    'company': 'Example', 'snippet': 'Maintenance of solar fields and industrial systems. ' * 8}

    def test_pending_survives_without_refetch(self):
        result = apply_keyword_fallback(self.job)
        self.ledger.record(self.job, result)
        loaded = EvaluationLedger(self.path)
        selected = loaded.select([], set())
        self.assertEqual(selected[0]['link'], self.job['link'])
        self.assertEqual(loaded.completed_links(), set())

    def test_missing_key_keeps_pending_and_does_not_publish(self):
        health = RunHealth()
        passed, _ = evaluate_candidates([self.job], None, health, self.ledger, enrich_job=lambda j: None)
        self.assertEqual(passed, [])
        self.assertEqual(health.pending_evaluations, 1)
        self.assertEqual(self.ledger.completed_links(), set())

    def test_no_usable_description_remains_pending(self):
        job = {**self.job, 'snippet': 'Solar Technician'}
        client = MagicMock()
        evaluate_candidates([job], client, RunHealth(), self.ledger, enrich_job=lambda j: None)
        self.assertEqual(self.ledger.jobs[job['link']]['stage'], 'RETRY_PENDING')
        client.models.generate_content.assert_not_called()

    def test_rejection_never_enters_keyword_fallback(self):
        job = {**self.job, 'title': 'HR Recruiter'}
        health = RunHealth()
        passed, _ = evaluate_candidates([job], None, health, self.ledger, enrich_job=lambda j: None)
        self.assertEqual(passed, [])
        self.assertEqual(health.fallback_evaluations, 0)
        self.assertEqual(self.ledger.completed_links(), {job['link']})

    def test_ready_reused_after_delivery_failure_then_committed(self):
        client = MagicMock()
        client.models.generate_content.return_value = response()
        runtime, _ = pool(('one',))
        passed, _ = evaluate_candidates([self.job], client, RunHealth(), self.ledger, pool=runtime, enrich_job=lambda j: None)
        self.assertEqual(len(passed), 1)
        self.assertEqual(self.ledger.jobs[self.job['link']]['stage'], 'READY')
        loaded = EvaluationLedger(self.path)
        retry, _ = evaluate_candidates(loaded.select([], set()), client, RunHealth(), loaded,
                                     pool=runtime, enrich_job=lambda j: None)
        self.assertEqual(client.models.generate_content.call_count, 1)
        loaded.commit_delivery([retry[0]['link']])
        self.assertEqual(loaded.select([self.job], set()), [])

    def test_legacy_history_preserved_and_duplicates_removed(self):
        self.assertEqual(self.ledger.select([self.job], {self.job['link']}), [])
        self.assertEqual(len(self.ledger.select([self.job, self.job, {'title': 'no URL'}], set())), 1)

    def test_corrupt_state_is_not_silently_reset(self):
        self.path.write_text('{invalid')
        with self.assertRaises(json.JSONDecodeError):
            EvaluationLedger(self.path)

    def test_atomic_save_failure_preserves_original(self):
        save_state_atomic(self.path, {'old': 1})
        with patch('src.state_manager.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                save_state_atomic(self.path, {'new': 2})
        self.assertEqual(load_state(self.path, strict=True), {'old': 1})

    def test_partial_success_is_not_success(self):
        health = RunHealth(gemini_successes=11, pending_evaluations=17, email_success=True)
        self.assertEqual(final_status(health, email_configured=True), 'DEGRADED_PENDING')
        html = build_unified_html_email([], [], 'https://example.com', health)
        self.assertIn('17 משרות ממתינות', html)
        self.assertNotIn('הסריקה עברה בהצלחה', html)

    def test_output_failures_and_healthy_empty(self):
        health = RunHealth(email_success=True)
        self.assertEqual(final_status(health, email_configured=True), 'SUCCESS_EMPTY_RUN')
        self.assertEqual(final_status(health, email_configured=True, dashboard_ok=False), 'FAILED_DASHBOARD')
        self.assertEqual(final_status(health, email_configured=True, state_ok=False), 'FAILED_STATE')
        health.email_success = False
        self.assertEqual(final_status(health, email_configured=True), 'FAILED_EMAIL')
        self.assertEqual(final_status(health, email_configured=False), 'DEGRADED_EMAIL_NOT_CONFIGURED')


if __name__ == '__main__':
    unittest.main()
