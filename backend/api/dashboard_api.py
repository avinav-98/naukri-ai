import sqlite3

from fastapi import APIRouter, Request

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import (
    ensure_applied_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_relevant_jobs_schema,
)

router = APIRouter(prefix="/api")


def count_rows(db_path, table, user_id):
    try:
        conn = sqlite3.connect(db_path)
        if table == "jobs_directory":
            ensure_jobs_directory_schema(conn)
        elif table == "relevant_jobs":
            ensure_relevant_jobs_schema(conn)
        elif table == "applied_jobs":
            ensure_applied_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (user_id,))
        result = cur.fetchone()[0]
        conn.close()
        return result
    except Exception:
        return 0


@router.get("/dashboard-stats")
def dashboard_data(request: Request):
    user_id = request.state.user_id
    jobs = count_rows(DATABASE_PATHS["jobs"], "jobs_directory", user_id)
    relevant = count_rows(DATABASE_PATHS["relevant"], "relevant_jobs", user_id)
    applied = count_rows(DATABASE_PATHS["applied"], "applied_jobs", user_id)

    return {"scraped": jobs, "relevant": relevant, "applied": applied}
