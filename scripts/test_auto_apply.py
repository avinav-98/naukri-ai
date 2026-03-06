import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from backend.services.apply_service import auto_apply


auto_apply("storage/resumes/my_resume.txt", limit=3)