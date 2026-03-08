import sqlite3
from datetime import datetime
from typing import Optional

from backend.config import DATABASE_PATHS


DB = DATABASE_PATHS["runs"]


def _table_columns(conn: sqlite3.Connection, table_name: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(conn: sqlite3.Connection, table_name: str, ddl: str):
    col_name = ddl.split()[0]
    cols = _table_columns(conn, table_name)
    if col_name not in cols:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def init_runs_table():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS automation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            run_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            pages INTEGER DEFAULT 0,
            auto_apply_limit INTEGER DEFAULT 0,
            fetched_count INTEGER DEFAULT 0,
            shortlisted_count INTEGER DEFAULT 0,
            applied_count INTEGER DEFAULT 0,
            celery_task_id TEXT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        )
        """
    )
    _ensure_column(conn, "automation_runs", "celery_task_id TEXT")
    conn.commit()
    conn.close()


def start_run(
    user_id: int,
    run_type: str,
    pages: int,
    auto_apply_limit: int,
    status: str = "running",
    message: str = "",
    celery_task_id: Optional[str] = None,
) -> int:
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO automation_runs (
            user_id, run_type, status, message, pages, auto_apply_limit, celery_task_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, run_type, status, message, pages, auto_apply_limit, celery_task_id),
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(run_id)


def update_run(
    run_id: int,
    status: str,
    message: str = "",
    fetched_count: Optional[int] = None,
    shortlisted_count: Optional[int] = None,
    applied_count: Optional[int] = None,
    celery_task_id: Optional[str] = None,
):
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    assignments = ["status = ?", "message = ?"]
    params = [status, message]

    if fetched_count is not None:
        assignments.append("fetched_count = ?")
        params.append(fetched_count)
    if shortlisted_count is not None:
        assignments.append("shortlisted_count = ?")
        params.append(shortlisted_count)
    if applied_count is not None:
        assignments.append("applied_count = ?")
        params.append(applied_count)
    if celery_task_id is not None:
        assignments.append("celery_task_id = ?")
        params.append(celery_task_id)
    if status in {"completed", "failed"}:
        assignments.append("finished_at = ?")
        params.append(datetime.utcnow().isoformat())

    params.append(run_id)
    cur.execute(f"UPDATE automation_runs SET {', '.join(assignments)} WHERE id = ?", params)
    conn.commit()
    conn.close()


def get_latest_runs(user_id: int, limit: int = 20):
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, run_type, status, message, pages, auto_apply_limit,
               fetched_count, shortlisted_count, applied_count,
               started_at, finished_at, celery_task_id
        FROM automation_runs
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_run_by_id(user_id: int, run_id: int):
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, run_type, status, message, pages, auto_apply_limit,
               fetched_count, shortlisted_count, applied_count,
               started_at, finished_at, celery_task_id
        FROM automation_runs
        WHERE user_id = ? AND id = ?
        LIMIT 1
        """,
        (user_id, run_id),
    )
    row = cur.fetchone()
    conn.close()
    return row


def clear_runs_for_user(user_id: int) -> int:
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM automation_runs WHERE user_id = ?", (user_id,))
    deleted = cur.rowcount if cur.rowcount is not None else 0
    conn.commit()
    conn.close()
    return int(deleted)
