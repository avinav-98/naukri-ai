import sqlite3

from fastapi import APIRouter, Request

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import (
    ensure_applied_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_relevant_jobs_schema,
)

router = APIRouter(prefix="/api")


@router.get("/jobs-directory")
def jobs_directory(request: Request):
    user_id = request.state.user_id
    try:
        conn = sqlite3.connect(DATABASE_PATHS["jobs"])
        ensure_jobs_directory_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url
            FROM jobs_directory
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return []

    return [
        {"title": r[0], "company": r[1], "location": r[2], "url": r[3]}
        for r in rows
    ]


@router.get("/relevant-jobs")
def relevant_jobs(request: Request):
    user_id = request.state.user_id
    try:
        conn = sqlite3.connect(DATABASE_PATHS["relevant"])
        ensure_relevant_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url, score
            FROM relevant_jobs
            WHERE user_id = ?
            ORDER BY score DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return []

    return [
        {
            "title": r[0],
            "company": r[1],
            "location": r[2],
            "url": r[3],
            "score": r[4],
        }
        for r in rows
    ]


@router.get("/applied-jobs")
def applied_jobs(request: Request):
    user_id = request.state.user_id
    try:
        conn = sqlite3.connect(DATABASE_PATHS["applied"])
        ensure_applied_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url, applied_at
            FROM applied_jobs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        return []

    return [
        {
            "title": r[0],
            "company": r[1],
            "location": r[2],
            "url": r[3],
            "applied_at": r[4],
        }
        for r in rows
    ]
