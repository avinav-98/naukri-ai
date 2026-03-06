import sqlite3

from backend.ai_engine.ranking_engine import rank_jobs
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_relevant_jobs_schema


def _ensure_relevant_table():
    conn = sqlite3.connect(DATABASE_PATHS["relevant"])
    ensure_relevant_jobs_schema(conn)
    conn.close()


def rank_and_store_jobs(user_id: int, resume_text: str, shortlist_limit: int = 20) -> int:
    _ensure_relevant_table()
    ranked_jobs = rank_jobs(resume_text, user_id=user_id, limit=shortlist_limit)

    conn = sqlite3.connect(DATABASE_PATHS["relevant"])
    cur = conn.cursor()
    cur.execute("DELETE FROM relevant_jobs WHERE user_id = ?", (user_id,))
    inserted = 0

    for score, job in ranked_jobs:
        job_title, company, location, job_url = job
        cur.execute(
            """
            INSERT INTO relevant_jobs
            (user_id, job_title, company, location, job_url, score)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, job_title, company, location, job_url, float(score)),
        )
        inserted += 1

    conn.commit()
    conn.close()
    return inserted
