import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.services.job_ranking_service import get_relevant_jobs


jobs = get_relevant_jobs("storage/resumes/my_resume.txt")

for score, job in jobs:

    print(score, job)