"""
Backward-compatible root entrypoint for ats_scraper.
Core implementation resides in src/ats_scraper.py.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from src.ats_scraper import *
