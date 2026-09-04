"""
Backward-compatible root entrypoint for interactive_app_builder.
Core implementation resides in src/interactive_app_builder.py.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from src.interactive_app_builder import *

if __name__ == '__main__':
    import json
    archive_file = os.path.join(BASE_DIR, 'data', 'weekly_archive.json')
    if not os.path.exists(archive_file):
        archive_file = os.path.join(BASE_DIR, 'weekly_archive.json')
    
    if os.path.exists(archive_file):
        with open(archive_file, 'r', encoding='utf-8') as f:
            archived_jobs = json.load(f)
        build_and_save_docs_app(archived_jobs, is_weekly=False)
        print(f'[+] Rebuilt docs/index.html with {len(archived_jobs)} jobs.')
