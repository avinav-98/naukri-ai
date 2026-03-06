import schedule
import time
from backend.workers.automation_worker import run_worker


def start_scheduler():

    print("Automation Scheduler Started")

    schedule.every(4).hours.do(run_worker)

    while True:

        schedule.run_pending()

        time.sleep(30)