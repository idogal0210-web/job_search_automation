"""Offline responsive checks against an isolated dashboard build; no external requests."""
import argparse
import json, threading, functools, sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root', type=Path, required=True, help='Isolated generated docs directory')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--asset-cache', type=Path, help='Optional JSON map of downloaded public CDN assets')
parser.add_argument('--phase', default='after', choices=['before','after'])
args=parser.parse_args()
root=args.root.resolve()
args.output.mkdir(parents=True, exist_ok=True)
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base_url=f'http://127.0.0.1:{server.server_port}/'
assets=json.loads(args.asset_cache.read_text()) if args.asset_cache else {}
def route_request(route):
    url=route.request.url
    if url.startswith(base_url):
        route.continue_()
    elif url in assets:
        item=assets[url];route.fulfill(body=Path(item['path']).read_bytes(),content_type=item['type'])
    else:route.abort()
phase=args.phase
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
    for width,height in [(320,740),(375,812),(390,844),(768,1024),(1024,768),(1440,900),(1920,1080),(844,390)]:
        page=browser.new_page(viewport={'width':width,'height':height})
        page.route('**/*',route_request)
        errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
        page.goto(base_url,wait_until='networkidle')
        page.wait_for_timeout(300)
        page.evaluate("document.querySelectorAll('.job-card').forEach(e=>{e.style.opacity='1';e.style.transform='none';e.style.contentVisibility='visible'})")
        metrics=page.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,cards:document.querySelectorAll('.job-card').length,overflow:[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&(r.left < -1||r.right>innerWidth+1)&&getComputedStyle(e).position!=='fixed'}).slice(0,15).map(e=>({tag:e.tagName,cls:e.className,id:e.id,width:e.getBoundingClientRect().width}))})''')
        metrics['height']=height;metrics['errors']=errors
        metrics['chart']=page.evaluate("typeof Chart !== 'undefined'")
        if phase != 'before':
            page.locator('.advanced-job-filters summary').click()
            page.locator('#scoreFilter').select_option('90')
            metrics['score_filter_empty']=page.locator('.job-card:visible').count()==0
            page.evaluate('resetAllFilters()')
            page.locator('#salaryFilter').select_option('job_ad')
            metrics['verified_salary_filter_empty']=page.locator('.job-card:visible').count()==0
            page.evaluate('resetAllFilters()')
            page.locator('#searchInput').fill('NO_MATCH_SYNTHETIC')
            page.wait_for_timeout(350)
            metrics['search_empty']=page.locator('.job-card:visible').count()==0
            page.evaluate('resetAllFilters()')
            page.locator('.advanced-job-filters summary').click()
        page.evaluate("document.querySelectorAll('.job-card').forEach(e=>{e.style.contentVisibility='visible'})")
        metrics['header_overlap']=page.evaluate('''() => {const elements=[...document.querySelector('.dashboard-sidebar').children].filter(e=>e.getBoundingClientRect().width>0);return elements.some((a,i)=>elements.slice(i+1).some(b=>{const x=a.getBoundingClientRect(),y=b.getBoundingClientRect();return Math.min(x.right,y.right)-Math.max(x.left,y.left)>2&&Math.min(x.bottom,y.bottom)-Math.max(x.top,y.top)>2}))}''')
        page.evaluate('scrollTo(0,0)')
        page.screenshot(path=str(args.output/f'{phase}-{width}x{height}.png'),full_page=True)
        if phase != 'before':
            page.evaluate("openJobModal('https://example.com/jobs/0')")
            metrics['modal_overflow']=page.evaluate('document.documentElement.scrollWidth > innerWidth')
            page.evaluate('closeJobModal()')
            page.evaluate("setViewMode('map')")
            metrics['map_available']=page.evaluate("typeof L !== 'undefined'")
            page.evaluate("setViewMode('grid'); switchDashboardAppMode('studio')")
            modules={}
            for module in ['ats','writer','kanban','interview','skills']:
                page.evaluate('(name)=>switchStudioModule(name)',module)
                modules[module]=page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                if width in [320,1024]:
                    page.screenshot(path=str(args.output/f'{phase}-{width}-{module}.png'),full_page=True)
            metrics['studio_modules_fit']=modules
            page.evaluate("switchDashboardAppMode('radar');localStorage.setItem('ido_job_applications_store', JSON.stringify({preserved:true}))")
            page.reload(wait_until='networkidle')
            metrics['legacy_applications_preserved']=page.evaluate("JSON.parse(localStorage.getItem('ido_job_applications_store')).preserved === true")
            page.evaluate("rawJobsData=[]; renderCards(); updateUI()")
            metrics['empty_state']=page.locator('#emptyState').is_visible()
            page.evaluate("window.fetch=async()=>{throw new Error('Synthetic offline failure')}; fetchJobsData()")
            page.wait_for_timeout(100)
            metrics['error_state']=page.locator('.jobs-error-banner').is_visible()
            page.evaluate("window.fetch=()=>new Promise(()=>{}); void fetchJobsData()")
            metrics['loading_state']=page.locator('#jobsLoadingSpinner').is_visible()
        results.append(metrics);page.close()
    browser.close()
server.shutdown()
(args.output/f'{phase}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False))

if phase == 'after':
    failed=[r for r in results if r['errors'] or r['header_overlap'] or r['scrollWidth'] > r['width'] or
            r['modal_overflow'] or not all(r['studio_modules_fit'].values()) or
            not all(r[k] for k in ['score_filter_empty','verified_salary_filter_empty','search_empty','legacy_applications_preserved','empty_state','error_state','loading_state'])]
    if failed:
        raise SystemExit('Responsive checks failed; inspect JSON report and screenshots')
