import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

REJECTED_FILE = os.path.join(DATA_DIR, 'rejected_jobs.json')
SAVED_FILE = os.path.join(DATA_DIR, 'saved_jobs.json')
ARCHIVE_FILE = os.path.join(DATA_DIR, 'weekly_archive.json')

sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
from src.interactive_app_builder import build_and_save_docs_app

class SyncHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            resp = json.dumps({'status': 'ok', 'project': 'job_search_automation'}).encode('utf-8')
            self.wfile.write(resp)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/sync':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(body)
            except Exception as e:
                self.send_response(400)
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Invalid JSON', 'details': str(e)}).encode('utf-8'))
                return

            saved_ids = set(payload.get('saved', []))
            rejected_ids = set(payload.get('rejected', []))

            # 1. Update rejected_jobs.json (merge with existing)
            existing_rejected = set()
            if os.path.exists(REJECTED_FILE):
                try:
                    with open(REJECTED_FILE, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        existing_rejected = set(data if isinstance(data, list) else data.keys())
                except Exception:
                    pass
            all_rejected = sorted(list(existing_rejected.union(rejected_ids)))
            with open(REJECTED_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_rejected, f, ensure_ascii=False, indent=2)

            # 2. Read weekly_archive.json to map details
            all_archive_jobs = []
            if os.path.exists(ARCHIVE_FILE):
                try:
                    with open(ARCHIVE_FILE, 'r', encoding='utf-8') as f:
                        all_archive_jobs = json.load(f)
                except Exception:
                    pass

            # 3. Update saved_jobs.json (full job objects)
            existing_saved_dict = {}
            if os.path.exists(SAVED_FILE):
                try:
                    with open(SAVED_FILE, 'r', encoding='utf-8') as f:
                        saved_data = json.load(f)
                        for sj in saved_data:
                            link = sj.get('link') or sj.get('id')
                            if link:
                                existing_saved_dict[link] = sj
                except Exception:
                    pass

            for job in all_archive_jobs:
                link = job.get('link') or job.get('id')
                if link in saved_ids:
                    existing_saved_dict[link] = job

            # Remove any job that was un-saved
            current_saved_list = [j for link, j in existing_saved_dict.items() if link in saved_ids or not saved_ids]
            # If explicit saved_ids provided, filter to strictly those
            if payload.get('strict_sync', False):
                current_saved_list = [j for link, j in existing_saved_dict.items() if link in saved_ids]

            with open(SAVED_FILE, 'w', encoding='utf-8') as f:
                json.dump(current_saved_list, f, ensure_ascii=False, indent=2)

            # 4. Filter weekly_archive.json to exclude rejected jobs
            cleaned_archive = [j for j in all_archive_jobs if (j.get('link') or j.get('id')) not in all_rejected]
            with open(ARCHIVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cleaned_archive, f, ensure_ascii=False, indent=2)

            # 5. Rebuild docs/index.html
            build_and_save_docs_app(cleaned_archive, is_weekly=False)

            response_data = {
                'success': True,
                'rejected_count': len(all_rejected),
                'saved_count': len(current_saved_list),
                'active_count': len(cleaned_archive)
            }

            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=8765):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SyncHandler)
    print(f'[+] Job Search Dashboard Sync Server running on http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    port = 8765
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
