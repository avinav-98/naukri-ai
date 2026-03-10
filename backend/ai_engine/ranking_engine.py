import sqlite3
from backend.config import DATABASE_PATHS
from backend.ai_engine.job_matcher import calculate_match_score
from backend.models.settings_model import get_settings
from backend.utils.db_migrations import ensure_jobs_directory_schema


def ensure_jobs_table(conn):
    ensure_jobs_directory_schema(conn)


def score_by_mode(semantic_score: float, resume_match_score: float, scan_mode: str) -> float:
    if scan_mode == "advance":
        return (0.50 * semantic_score) + (0.50 * resume_match_score)
    if scan_mode == "extreme":
        return (0.35 * semantic_score) + (0.65 * resume_match_score)
    return (0.65 * semantic_score) + (0.35 * resume_match_score)


def rank_jobs(resume_text, user_id=None, limit=20, settings=None):

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])

    # Ensure table exists
    ensure_jobs_table(conn)

    cursor = conn.cursor()

    if settings is None:
        settings = get_settings(user_id=user_id) if user_id is not None else {}
    scan_mode = (settings.get("scan_mode", "basic") or "basic").strip().lower()
    if scan_mode not in {"basic", "advance", "extreme"}:
        scan_mode = "basic"

    if user_id is None:
        cursor.execute(
            """
            SELECT id, job_title, company, location, experience, salary, job_description, resume_match_score, job_url
            FROM jobs_directory
            """
        )
    else:
        cursor.execute(
            """
            SELECT id, job_title, company, location, experience, salary, job_description, resume_match_score, job_url
            FROM jobs_directory
            WHERE user_id = ?
            """,
            (user_id,),
        )

    jobs = cursor.fetchall()

    ranked = []

    for job in jobs:

        job_text = f"{job[1]} {job[2]} {job[3]} {job[4]} {job[5]} {job[6]}"
        semantic_score = max(0.0, float(calculate_match_score(resume_text, job_text)) * 100.0)
        resume_match_score = float(job[7] or 0.0)
        score = round(score_by_mode(semantic_score, resume_match_score, scan_mode), 2)
        ranked.append(
            (
                score,
                {
                    "job_id": job[0],
                    "job_title": job[1],
                    "company": job[2],
                    "location": job[3],
                    "experience": job[4],
                    "salary": job[5],
                    "job_description": job[6],
                    "resume_match_score": resume_match_score,
                    "job_url": job[8],
                },
            )
        )

    ranked.sort(key=lambda item: item[0], reverse=True)

    conn.close()

    return ranked[:limit]
