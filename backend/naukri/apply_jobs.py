import sqlite3
import random
from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_applied_jobs_schema, ensure_standard_jobs_schema
from backend.utils.activity_logger import log_activity


def save_applied_job(user_id, job_title, company, location, job_url):

    conn = sqlite3.connect(DATABASE_PATHS["applied"])
    ensure_applied_jobs_schema(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO applied_jobs
        (user_id, job_title, company, location, job_url)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, job_title, company, location, job_url)
    )

    conn.commit()
    conn.close()


def save_standard_job(user_id, job_title, company, location, job_url):

    conn = sqlite3.connect("database/standard_jobs.db")
    ensure_standard_jobs_schema(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO standard_jobs
        (user_id, job_title, company, location, job_url)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, job_title, company, location, job_url)
    )

    conn.commit()
    conn.close()


def apply_to_job(user_id, job_title, company, location, job_url):

    browser = get_browser()

    context = browser.new_context()

    load_session(context, user_id)

    page = context.new_page()

    print(f"\nOpening job: {job_title}")

    page.goto("https://www.naukri.com")
    page.wait_for_timeout(random.randint(2000, 4000))

    page.goto(job_url)
    page.wait_for_timeout(random.randint(3000, 5000))

    apply_btn = page.query_selector(
        "button:has-text('Apply'), button:has-text('Easy Apply')"
    )

    external_apply = page.query_selector(
        "a:has-text('Apply on company site'), a:has-text('Company Website'), a:has-text('Apply on company website')"
    )

    if external_apply:

        print("External apply detected:", job_title)

        save_standard_job(user_id, job_title, company, location, job_url)

        log_activity("External Apply", job_title)
        context.close()

        return


    if apply_btn:

        try:
            apply_btn.click()

            page.wait_for_timeout(random.randint(2000, 4000))

            print("Applied successfully:", job_title)

            save_applied_job(user_id, job_title, company, location, job_url)

            log_activity("Job Applied", job_title)
            context.close()

        except Exception as e:

            print("Apply failed:", job_title, str(e))
            context.close()

    else:

        print("No apply button found:", job_title)
        context.close()
