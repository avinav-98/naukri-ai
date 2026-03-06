import schedule
import time
from backend.services.apply_service import auto_apply


def run_scheduler():

    schedule.every(6).hours.do(
        auto_apply,
        resume_path="storage/resumes/my_resume.txt",
        limit=5
    )

    while True:
        schedule.run_pending()
        time.sleep(60)