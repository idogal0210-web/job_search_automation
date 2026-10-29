"""Offline regression cases for defects verified during the project audit."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.evaluators import validate_requirement_assessments, evaluate_and_enrich_job_with_gemini
from src.fetchers import RunHealth, fetch_linkedin_jobs, fetch_drushim_jobs, fetch_drushim_full_job_description, _get_with_retries
from src.pipeline import enrich, final_status, evaluate_candidates
from src.publishers import build_unified_html_email, send_email_report
from src.state_manager import EvaluationLedger
from src.ui_builder import build_and_save_docs_app
from src.url_utils import canonical_job_url, safe_http_url

ROOT = Path(__file__).resolve().parents[1]


class AuditRegressionTests(unittest.TestCase):
    def test_email_escapes_text_and_rejects_unsafe_links(self):
        job = {'title': '<img src=x onerror=alert(1)>', 'company': '<script>x</script>',
               'link': 'javascript:alert(1)', 'salary_range': '<b>20000</b>',
               'salary_source_url': 'data:text/html,attack'}
        html = build_unified_html_email([job], [job], 'javascript:alert(1)')
        self.assertNotIn('<script>', html)
        self.assertNotIn('<img src=x', html)
        self.assertNotIn('javascript:', html)
        self.assertNotIn('data:text', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertEqual(job['link'], 'javascript:alert(1)')

    def test_top_pick_salary_has_estimate_label(self):
        html = build_unified_html_email([{'link':'https://example.com','salary_range':'15000'}],
                                       [{'link':'https://example.com','salary_range':'15000'}], 'https://example.com')
        self.assertGreaterEqual(html.count('הערכה בלבד'), 1)

    def test_smtp_quit_failure_does_not_resend(self):
        server = MagicMock(); server.quit.side_effect = OSError('closed')
        with patch('src.publishers.smtplib.SMTP', return_value=server), patch('src.publishers.time.sleep'):
            health = RunHealth()
            self.assertTrue(send_email_report('fake','fake',[],[],[],'https://example.com',health))
        server.sendmail.assert_called_once()

    def test_uncertain_smtp_delivery_is_not_retried(self):
        server = MagicMock(); server.sendmail.side_effect = OSError('disconnected')
        with patch('src.publishers.smtplib.SMTP', return_value=server), patch('src.publishers.time.sleep'):
            self.assertFalse(send_email_report('fake','fake',[],[],[],'https://example.com',RunHealth()))
        server.sendmail.assert_called_once()

    def test_url_normalization_preserves_requisition_query(self):
        self.assertEqual(canonical_job_url('https://EXAMPLE.com/job/?id=2&utm_source=a#top'), 'https://example.com/job?id=2')
        self.assertNotEqual(canonical_job_url('https://example.com/?id=1'),canonical_job_url('https://example.com/?id=2'))
        self.assertEqual(canonical_job_url('https://il.linkedin.com/jobs/view/role-12345?trk=x'), 'https://www.linkedin.com/jobs/view/12345')

    def test_unsafe_urls(self):
        for url in ['javascript:alert(1)', '//example.com', 'https://user:pass@example.com', 'https://example.com\nattack', 'https://[broken']:
            with self.subTest(url=url): self.assertEqual(safe_http_url(url),'')

    def test_description_fetch_rejects_spoofed_host(self):
        with patch('src.fetchers.requests.get') as get:
            self.assertEqual(fetch_drushim_full_job_description('https://attacker.invalid/drushim.co.il/job/1'), '')
            get.assert_not_called()

    def test_long_snippet_is_enriched(self):
        job={'link':'https://www.linkedin.com/jobs/view/12345','source':'LinkedIn','snippet':'snippet '*100}
        with patch('src.pipeline.fetch_linkedin_full_job_description',return_value='full evidence') as fetch:
            enrich(job);enrich(job)
            fetch.assert_called_once()
        self.assertEqual(job['description'],'full evidence')

    def test_both_evidence_quotes_required(self):
        for ad,profile in [('missing','actual profile'),('actual ad','invented'),('','')]:
            entry={'requirement':'test','ad_evidence':{'quote':ad},'profile_evidence':{'quote':profile},'assessment':'match'}
            self.assertEqual(validate_requirement_assessments([entry],'actual ad','actual profile')[0]['assessment'],'unknown')

    def test_missing_ai_evidence_stays_pending(self):
        pool=MagicMock(); pool.evaluate.return_value={'match_score':90,'status':'QUALIFIED','technical_role':True,
            'sector_key':'energy','concrete_matches_count':3,'reasoning':'test','evaluation_model':'mock','evaluation_complete':True}
        result=evaluate_and_enrich_job_with_gemini(object(),'Solar technician','Example','industrial maintenance',False,RunHealth(),pool=pool)
        self.assertEqual(result['status'],'RETRY_PENDING');self.assertFalse(result['evaluation_complete'])

    def test_comeet_health_is_part_of_run_status(self):
        health=RunHealth(linkedin_requests=1,linkedin_failures=1,comeet_requests=1,comeet_successes=1,email_success=True)
        self.assertEqual(final_status(health,email_configured=True),'DEGRADED_NETWORK')
        health=RunHealth(comeet_requests=1,comeet_failures=1,email_success=True)
        self.assertEqual(final_status(health,email_configured=True),'FAILED_SCRAPERS')

    def test_fixture_parsers_and_changed_html(self):
        for source,fetch in [('linkedin',fetch_linkedin_jobs),('drushim',fetch_drushim_jobs)]:
            response=SimpleNamespace(status_code=200,text=(ROOT/'tests/fixtures'/f'{source}_jobs.html').read_text())
            with patch('src.fetchers.requests.get',return_value=response),patch('src.fetchers.time.sleep'):
                health=RunHealth(); jobs=fetch(['test','test'],health)
                self.assertEqual(len(jobs),1);self.assertEqual(getattr(health,source+'_requests'),1)
            response.text='<html>Unexpected sign-in page</html>'
            with patch('src.fetchers.requests.get',return_value=response),patch('src.fetchers.time.sleep'):
                health=RunHealth();self.assertEqual(fetch(['test'],health),[])
                self.assertEqual(getattr(health,source+'_failures'),1)
                self.assertEqual(getattr(health,source+'_successes'),0)

    def test_bounded_read_retries(self):
        client=MagicMock();client.get.return_value=SimpleNamespace(status_code=429,headers={'Retry-After':'3'})
        with patch('src.fetchers.time.sleep') as sleep:
            _get_with_retries(client,'https://example.com',timeout=8)
            self.assertEqual(client.get.call_count,3)
            self.assertEqual([call.args[0] for call in sleep.call_args_list],[3,3])
        client.reset_mock();client.get.return_value.headers={'Retry-After':'500'}
        with patch('src.fetchers.time.sleep') as sleep:
            _get_with_retries(client,'https://example.com',timeout=8)
            client.get.assert_called_once();sleep.assert_not_called()
        client.reset_mock();client.get.return_value.status_code=403
        _get_with_retries(client,'https://example.com',timeout=8);client.get.assert_called_once()

    def test_canonical_dedup_preserves_history_and_distinct_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=EvaluationLedger(Path(tmp)/'state.json')
            job={'link':'https://example.com/job?id=1','title':'technician'}
            ledger.record(job,{'status':'DISQUALIFIED','evaluation_complete':True})
            self.assertEqual(ledger.select([{**job,'link':job['link']+'&utm_source=new'}],set()),[])
            self.assertEqual(len(ledger.select([{**job,'link':'https://example.com/job?id=2'}],set())),1)
            self.assertIn(job['link'],ledger.jobs)

    def test_cross_source_duplicate_requires_matching_location_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=EvaluationLedger(Path(tmp)/'state.json')
            job={'link':'https://example.com/1','title':'technician','company':'Example','location':'Haifa','snippet':'full description '*30,'source':'LinkedIn'}
            copy={**job,'link':'https://example.org/2','source':'Drushim'}
            self.assertEqual(len(ledger.select([job,copy],set())),1)
            copy['location']='Tel Aviv'
            self.assertEqual(len(ledger.select([job,copy],set())),2)

    def test_bad_catalog_is_not_replaced_by_empty_public_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'data/historical_catalog.json').write_text('{invalid')
            with self.assertRaises(json.JSONDecodeError):build_and_save_docs_app([],[],tmp)
            self.assertFalse((root/'docs/data/historical_catalog.json').exists())

    def test_schedule_gate_summer_winter_and_dst_transition(self):
        workflow=(ROOT/'.github/workflows/daily_job_search.yml').read_text()
        code=workflow.split("python - <<'PYTHON'\n",1)[1].split('          PYTHON',1)[0]
        import textwrap, os
        code=textwrap.dedent(code)
        for day,hour in [('2026-07-01T07:17:00+03:00',4),('2026-12-01T07:17:00+02:00',5),
                         ('2026-10-24T07:17:00+03:00',4),('2026-10-25T07:17:00+02:00',5)]:
            for scheduled in [4,5]:
                with tempfile.TemporaryDirectory() as tmp:
                    output=Path(tmp)/'output'
                    with patch.dict(os.environ,{'EVENT_NAME':'schedule','EVENT_SCHEDULE':f'17 {scheduled} * * 0-5','GITHUB_OUTPUT':str(output)}):
                        exec(code.replace('datetime.now(ZoneInfo("Asia/Jerusalem"))',f'datetime.fromisoformat("{day}")'),{})
                    self.assertEqual(output.read_text().strip(),f'run={str(scheduled==hour).lower()}')
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'output'
            with patch.dict(os.environ,{'EVENT_NAME':'workflow_dispatch','EVENT_SCHEDULE':'','GITHUB_OUTPUT':str(output)}):
                exec(code,{})
            self.assertEqual(output.read_text().strip(),'run=true')

    def test_pipeline_preserves_scraped_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=EvaluationLedger(Path(tmp)/'state.json')
            job={'link':'https://example.com/metadata','title':'Solar Technician','company':'Example',
                 'snippet':'Industrial maintenance '*20,'location':'Haifa','source_id':'ABC','source':'Comeet','logo':'https://example.com/logo.png'}
            evaluate_candidates([job],None,RunHealth(),ledger,enrich_job=lambda j:None)
            for key in ['location','source_id','logo']:
                self.assertEqual(ledger.jobs[job['link']]['job'][key],job[key])

    def test_historical_catalog_is_never_truncated(self):
        from src.ui_builder import update_weekly_archive
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir()
            catalog={f'https://example.com/{i}':{'link':f'https://example.com/{i}','date':'2020-01-01'} for i in range(1501)}
            path=root/'data/historical_catalog.json';path.write_text(json.dumps(catalog))
            update_weekly_archive([],str(root/'data/weekly_archive.json'),set())
            self.assertEqual(json.loads(path.read_text()),catalog)

    def test_corrupt_archive_is_not_reset(self):
        from src.ui_builder import update_weekly_archive
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();path=root/'data/weekly_archive.json';path.write_text('{invalid')
            with self.assertRaises(json.JSONDecodeError):update_weekly_archive([],str(path),set())
            self.assertEqual(path.read_text(),'{invalid')

    def test_salary_never_relabels_foreign_currency_or_invents_range(self):
        from src.salary_engine import extract_salary_from_ad
        for text in ['Salary 15k-18k USD per month','שכר 15,000 - 18,000 דולר USD','שכר שנתי 18,000 ₪']:
            self.assertIsNone(extract_salary_from_ad(text))
        result=extract_salary_from_ad('שכר 16000 ₪')
        self.assertEqual(result['extracted_min'],16000)
        self.assertEqual(result['extracted_max'],16000)
        self.assertIn('הערכה חודשית',extract_salary_from_ad('65 ש"ח לשעה')['salary_range'])

    def test_required_gap_or_contradiction_stays_pending(self):
        pool=MagicMock()
        matches=[{'requirement':word,'importance':'preferred','ad_evidence':{'quote':word},
                  'profile_evidence':{'quote':'SCADA'},'assessment':'match'} for word in ['industrial','maintenance']]
        for assessment in ['gap','unknown']:
            required={'requirement':'License','importance':'required','ad_evidence':{'quote':'license'},
                      'profile_evidence':{'quote':'Certified Electrician Studies'},'assessment':assessment}
            pool.evaluate.return_value={'match_score':90,'status':'QUALIFIED','technical_role':True,
                'sector_key':'energy','concrete_matches_count':3,'reasoning':'test','evaluation_model':'mock',
                'evaluation_complete':True,'requirement_assessments':matches+[required]}
            result=evaluate_and_enrich_job_with_gemini(object(),'Solar technician','Example','industrial maintenance license',False,RunHealth(),pool=pool)
            self.assertEqual(result['status'],'RETRY_PENDING')

    def test_delivery_commits_only_the_five_reported_jobs(self):
        import main
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ledger=MagicMock();ledger.select.return_value=[];ledger.completed_links.return_value=set()
            jobs=[{'link':f'https://example.com/{i}','match_score':80} for i in range(7)]
            def sent(*args):args[-1].email_success=True
            with patch.dict('os.environ',{'SENDER_EMAIL':'fake','SENDER_APP_PASSWORD':'fake'},clear=True), \
                 patch.object(main,'__file__',str(root/'main.py')),patch.object(main,'STATE_FILE',str(root/'data/jobs_state.json')), \
                 patch.object(main,'EvaluationLedger',return_value=ledger), \
                 patch.object(main,'fetch_linkedin_jobs',return_value=[]),patch.object(main,'fetch_drushim_jobs',return_value=[]), \
                 patch.object(main,'fetch_comeet_jobs',return_value=[]),patch.object(main,'evaluate_candidates',return_value=(jobs,[])), \
                 patch.object(main,'update_weekly_archive',return_value=jobs),patch.object(main,'build_and_save_docs_app'), \
                 patch.object(main,'send_email_report',side_effect=sent):
                self.assertEqual(main.main(),0)
            ledger.commit_delivery.assert_called_once_with([j['link'] for j in jobs[:5]])

    def test_unavailable_full_portal_description_stays_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger=EvaluationLedger(Path(tmp)/'ledger.json')
            job={'link':'https://www.linkedin.com/jobs/view/12345','source':'LinkedIn','title':'Solar Technician',
                 'company':'Example','snippet':'industrial maintenance '*30}
            client=MagicMock()
            passed,_=evaluate_candidates([job],client,RunHealth(),ledger,enrich_job=lambda j:None)
            self.assertEqual(passed,[])
            self.assertEqual(ledger.jobs[job['link']]['stage'],'RETRY_PENDING')
            client.models.generate_content.assert_not_called()
