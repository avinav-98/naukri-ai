import sqlite3
import random
from urllib.parse import urlparse
from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session
from backend.config import DATABASE_PATHS
from backend.models.ext_jobs_model import upsert_ext_job
from backend.utils.db_migrations import ensure_applied_jobs_schema, ensure_standard_jobs_schema
from backend.utils.activity_logger import log_activity


def _contains_any_text(page, selectors):
    for sel in selectors:
        try:
            if page.query_selector(sel):
                return True
        except Exception:
            continue
    return False


def _is_naukri_url(url: str) -> bool:
    if not url:
        return True
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return True
    return "naukri.com" in host


def save_applied_job(user_id, job_title, company, location, experience, job_url):

    conn = sqlite3.connect(DATABASE_PATHS["applied"])
    ensure_applied_jobs_schema(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO applied_jobs
        (user_id, job_title, company, location, experience, job_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            experience=excluded.experience,
            status='applied',
            applied_at=CURRENT_TIMESTAMP
        """,
        (user_id, job_title, company, location, experience, job_url, "applied")
    )

    conn.commit()
    conn.close()


def save_standard_job(user_id, job_title, company, location, job_url):
    conn = sqlite3.connect(DATABASE_PATHS["standard"])
    ensure_standard_jobs_schema(conn)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO standard_jobs
        (user_id, job_title, company, location, job_url, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            status=excluded.status
        """,
        (user_id, job_title, company, location, job_url, "pending"),
    )

    conn.commit()
    conn.close()


def save_external_job(user_id, job_title, company, location, experience, job_url, external_apply_url):
    upsert_ext_job(
        user_id=user_id,
        job_title=job_title,
        company=company,
        location=location,
        experience=experience,
        job_url=job_url,
        external_apply_url=external_apply_url,
    )


def save_job_status(user_id, job_title, company, location, job_url, status):
    conn = sqlite3.connect(DATABASE_PATHS["standard"])
    ensure_standard_jobs_schema(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO standard_jobs
        (user_id, job_title, company, location, job_url, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            status=excluded.status
        """,
        (user_id, job_title, company, location, job_url, status),
    )
    conn.commit()
    conn.close()


def apply_to_job(user_id, job_title, company, location, experience, job_url):

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
        "button:has-text('Apply'), button:has-text('Easy Apply'), a:has-text('Apply'), a:has-text('Easy Apply')"
    )

    if apply_btn:

        try:
            before_pages = len(context.pages)
            apply_btn.click()

            page.wait_for_timeout(random.randint(2000, 4000))

            current_url = page.url or ""
            external_url = ""
            if len(context.pages) > before_pages:
                popup = context.pages[-1]
                try:
                    popup.wait_for_timeout(1200)
                    external_url = popup.url or ""
                except Exception:
                    external_url = popup.url or ""
                finally:
                    try:
                        popup.close()
                    except Exception:
                        pass
            if not external_url:
                external_apply = page.query_selector(
                    "a:has-text('Apply on company site'), a:has-text('Company Website'), a:has-text('Apply on company website')"
                )
                if external_apply:
                    external_url = external_apply.get_attribute("href") or ""
            if not external_url and current_url and not _is_naukri_url(current_url):
                external_url = current_url

            if external_url and not _is_naukri_url(external_url):
                print("External redirect detected:", job_title, external_url)
                save_external_job(
                    user_id=user_id,
                    job_title=job_title,
                    company=company,
                    location=location,
                    experience=experience,
                    job_url=job_url,
                    external_apply_url=external_url,
                )
                save_job_status(user_id, job_title, company, location, job_url, "skipped")
                log_activity("External Apply", job_title)
                context.close()
                return {"status": "skipped", "external_apply_url": external_url}

            if _contains_any_text(
                page,
                [
                    "text=Successfully applied",
                    "text=Application submitted",
                    "text=Applied",
                    "text=You have already applied",
                    "text=Already Applied",
                ],
            ):
                print("Applied successfully:", job_title)

                save_applied_job(user_id, job_title, company, location, experience, job_url)
                save_job_status(user_id, job_title, company, location, job_url, "applied")

                log_activity("Job Applied", job_title)
                context.close()
                return {"status": "applied"}

            print("Apply click did not confirm success:", job_title)
            save_job_status(user_id, job_title, company, location, job_url, "failed")
            context.close()
            return {"status": "failed"}

        except Exception as e:

            print("Apply failed:", job_title, str(e))
            save_job_status(user_id, job_title, company, location, job_url, "failed")
            context.close()
            return {"status": "failed"}

    else:

        print("No apply button found:", job_title)
        save_job_status(user_id, job_title, company, location, job_url, "filtered_out")
        context.close()
        return {"status": "filtered_out"}
