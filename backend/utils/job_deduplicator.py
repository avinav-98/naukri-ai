import sqlite3
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_jobs_directory_schema


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def job_exists(job_url, user_id=1, job_title="", company="", location=""):

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)

    cursor = conn.cursor()
    result = None

    if job_url:
        cursor.execute(
            "SELECT id FROM jobs_directory WHERE user_id = ? AND job_url = ?",
            (user_id, job_url),
        )
        result = cursor.fetchone()

    if not result and _norm(job_title):
        norm_company = _norm(company) or _norm(job_url) or "unknown"
        norm_location = _norm(location) or "unknown"
        cursor.execute(
            """
            SELECT id
            FROM jobs_directory
            WHERE user_id = ?
              AND normalized_title = ?
              AND normalized_company = ?
              AND normalized_location = ?
            """,
            (user_id, _norm(job_title), norm_company, norm_location),
        )
        result = cursor.fetchone()

    conn.close()

    return result is not None
