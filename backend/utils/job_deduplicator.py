import sqlite3
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_jobs_directory_schema


def job_exists(job_url, user_id=1):

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)

    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM jobs_directory WHERE user_id = ? AND job_url = ?",
        (user_id, job_url)
    )

    result = cursor.fetchone()

    conn.close()

    return result is not None
