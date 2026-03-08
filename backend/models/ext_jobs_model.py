import sqlite3

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_ext_jobs_schema


def upsert_ext_job(
    user_id: int,
    job_title: str,
    company: str,
    location: str,
    experience: str,
    job_url: str,
    external_apply_url: str,
):
    conn = sqlite3.connect(DATABASE_PATHS["ext"])
    ensure_ext_jobs_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ext_jobs
        (user_id, job_title, company, location, experience, job_url, external_apply_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, job_url) DO UPDATE SET
            job_title=excluded.job_title,
            company=excluded.company,
            location=excluded.location,
            experience=excluded.experience,
            external_apply_url=excluded.external_apply_url,
            captured_at=CURRENT_TIMESTAMP
        """,
        (user_id, job_title, company, location, experience, job_url, external_apply_url),
    )
    conn.commit()
    conn.close()


def get_ext_jobs(user_id: int, limit: int = 200):
    conn = sqlite3.connect(DATABASE_PATHS["ext"])
    ensure_ext_jobs_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT job_title, company, location, experience, job_url, external_apply_url, captured_at
        FROM ext_jobs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
