import sqlite3
from backend.config import DATABASE_PATHS
from backend.ai_engine.job_matcher import calculate_match_score
from backend.utils.db_migrations import ensure_jobs_directory_schema


def ensure_jobs_table(conn):
    ensure_jobs_directory_schema(conn)


def rank_jobs(resume_text, user_id=None, limit=20):

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])

    # Ensure table exists
    ensure_jobs_table(conn)

    cursor = conn.cursor()

    if user_id is None:
        cursor.execute("SELECT job_title, company, location, job_url FROM jobs_directory")
    else:
        cursor.execute(
            """
            SELECT job_title, company, location, job_url
            FROM jobs_directory
            WHERE user_id = ?
            """,
            (user_id,),
        )

    jobs = cursor.fetchall()

    ranked = []

    for job in jobs:

        job_text = f"{job[0]} {job[1]} {job[2]}"

        score = calculate_match_score(resume_text, job_text)

        ranked.append((score, job))

    ranked.sort(reverse=True)

    conn.close()

    return ranked[:limit]
