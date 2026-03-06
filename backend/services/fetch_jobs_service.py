from backend.naukri.job_scraper import scrape_jobs
import sqlite3
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_jobs_directory_schema


def _count_jobs(user_id):
    try:
        conn = sqlite3.connect(DATABASE_PATHS["jobs"])
        ensure_jobs_directory_schema(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs_directory WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception:
        return 0


def _clear_user_jobs(user_id):
    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs_directory WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def fetch_jobs(pages=3, user_id=1, search_query="data analyst", clear_existing=False):

    print("Starting job fetch...")
    if clear_existing:
        _clear_user_jobs(user_id)
    before = _count_jobs(user_id)

    scrape_jobs(user_id=user_id, pages=pages, search_query=search_query)
    after = _count_jobs(user_id)

    print("Job fetching completed.")
    return max(0, after - before)
