import sys
import os

# Add project root to Python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.services.fetch_jobs_service import fetch_jobs


fetch_jobs(5)