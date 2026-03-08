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


def get_top_companies(user_id: int, limit: int = 3):
    try:
        conn = sqlite3.connect(DATABASE_PATHS["jobs"])
        ensure_jobs_directory_schema(conn)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT company, COUNT(*) AS cnt
            FROM jobs_directory
            WHERE user_id = ? AND company IS NOT NULL AND TRIM(company) != ''
            GROUP BY company
            ORDER BY cnt DESC, company ASC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0]]
    except Exception:
        return []


def fetch_jobs_with_details(
    pages=3,
    user_id=1,
    search_query="data analyst",
    clear_existing=False,
    filter_settings=None,
    resume_text="",
    keywords="",
):

    print("Starting job fetch...")
    if clear_existing:
        _clear_user_jobs(user_id)
    before = _count_jobs(user_id)

    scrape_result = scrape_jobs(
        user_id=user_id,
        pages=pages,
        search_query=search_query,
        filter_settings=filter_settings or {},
        resume_text=resume_text,
        keywords=keywords,
    )
    after = _count_jobs(user_id)
    added_count = max(0, after - before)
    filtered_out_count = 0
    if isinstance(scrape_result, dict):
        filtered_out_count = int(scrape_result.get("filtered_out_count", 0))

    print("Job fetching completed.")
    return {
        "added_count": added_count,
        "filtered_out_count": filtered_out_count,
    }


def fetch_jobs(pages=3, user_id=1, search_query="data analyst", clear_existing=False):
    details = fetch_jobs_with_details(
        pages=pages,
        user_id=user_id,
        search_query=search_query,
        clear_existing=clear_existing,
    )
    return int(details["added_count"])
