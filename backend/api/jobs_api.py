import sqlite3

from fastapi import APIRouter, Request

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import (
    ensure_applied_jobs_schema,
    ensure_ext_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_relevant_jobs_schema,
    ensure_standard_jobs_schema,
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
    merged = {}
    try:
        conn = sqlite3.connect(DATABASE_PATHS["applied"])
        ensure_applied_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, experience, job_url, applied_at, status
            FROM applied_jobs
            WHERE user_id = ? AND lower(status) = 'applied'
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
        for r in rows:
            key = r[4] or f"{r[0]}::{r[1]}::{r[2]}"
            merged[key] = {
                "title": r[0],
                "company": r[1],
                "location": r[2],
                "experience": r[3],
                "url": r[4],
                "applied_at": r[5],
                "status": (r[6] or "applied").title(),
            }
    except Exception:
        pass

    try:
        conn = sqlite3.connect(DATABASE_PATHS["standard"])
        ensure_standard_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url, created_at, status
            FROM standard_jobs
            WHERE user_id = ? AND lower(status) = 'applied'
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        srows = cur.fetchall()
        conn.close()
        for r in srows:
            key = r[3] or f"{r[0]}::{r[1]}::{r[2]}"
            if key in merged:
                continue
            merged[key] = {
                "title": r[0],
                "company": r[1],
                "location": r[2],
                "experience": "",
                "url": r[3],
                "applied_at": r[4],
                "status": (r[5] or "applied").title(),
            }
    except Exception:
        pass

    items = list(merged.values())
    items.sort(key=lambda x: str(x.get("applied_at") or ""), reverse=True)
    return items[:200]


@router.get("/ext-jobs")
def ext_jobs(request: Request):
    user_id = request.state.user_id
    try:
        conn = sqlite3.connect(DATABASE_PATHS["ext"])
        ensure_ext_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, experience, job_url, external_apply_url, captured_at
            FROM ext_jobs
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
            "experience": r[3],
            "job_url": r[4],
            "external_apply_url": r[5],
            "captured_at": r[6],
        }
        for r in rows
    ]
