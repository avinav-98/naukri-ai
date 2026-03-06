import sqlite3

from backend.automation.browser_manager import get_browser
from backend.automation.session_manager import load_session
from backend.config import DATABASE_PATHS
from backend.utils.activity_logger import log_activity
from backend.utils.db_migrations import ensure_jobs_directory_schema
from backend.utils.job_deduplicator import job_exists


def _build_search_url(search_query: str) -> str:
    slug = "-".join(search_query.strip().lower().split())
    if not slug:
        slug = "data-analyst"
    return f"https://www.naukri.com/{slug}-jobs"


def scrape_jobs(user_id=1, pages=3, search_query="data analyst"):
    browser = get_browser()
    context = browser.new_context()

    session_loaded = load_session(context, user_id)
    page = context.new_page()
    page.goto("https://www.naukri.com")
    page.wait_for_timeout(3000)

    login_btn = page.query_selector("a:has-text('Login')")
    if login_btn:
        context.close()
        if not session_loaded:
            raise RuntimeError("Naukri session not found. Use 'Link Naukri Profile' first.")
        raise RuntimeError("Naukri session expired. Re-link Naukri Profile and retry.")

    page.goto(_build_search_url(search_query))
    jobs = []

    for p in range(pages):
        print(f"Scraping page {p + 1}")
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("div.srp-jobtuple-wrapper")
        for card in cards:
            title = card.query_selector("a.title")
            company = card.query_selector("a.subTitle")
            location = card.query_selector(".locWdth")

            if not title:
                continue

            job_title = title.inner_text().strip()
            job_url = title.get_attribute("href")
            if not job_url:
                continue

            company_name = company.inner_text() if company else ""
            location_name = location.inner_text() if location else ""

            if not job_exists(job_url, user_id=user_id):
                jobs.append(
                    {
                        "user_id": user_id,
                        "title": job_title,
                        "company": company_name,
                        "location": location_name,
                        "url": job_url,
                    }
                )

        next_btn = page.query_selector("a[title='Next']")
        if next_btn:
            next_btn.click()
        else:
            break

    save_jobs(jobs)
    log_activity("Jobs Scraped", f"{len(jobs)} jobs added")
    context.close()
    return len(jobs)


def save_jobs(jobs):
    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)
    cursor = conn.cursor()

    for job in jobs:
        cursor.execute(
            """
            INSERT OR IGNORE INTO jobs_directory
            (user_id, job_title, company, location, job_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                job.get("user_id", 1),
                job["title"],
                job["company"],
                job["location"],
                job["url"],
            ),
        )

    conn.commit()
    conn.close()
