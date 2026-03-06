import sqlite3
from datetime import datetime

from backend.config import DATABASE_PATHS


DB = DATABASE_PATHS["runs"]


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
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def start_run(
    user_id: int,
    run_type: str,
    pages: int,
    auto_apply_limit: int,
    status: str = "running",
    message: str = "",
) -> int:
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO automation_runs (
            user_id, run_type, status, message, pages, auto_apply_limit
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, run_type, status, message, pages, auto_apply_limit),
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(run_id)


def update_run(
    run_id: int,
    status: str,
    message: str = "",
    fetched_count: int = 0,
    shortlisted_count: int = 0,
    applied_count: int = 0,
):
    init_runs_table()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    finished_at = datetime.utcnow().isoformat() if status in {"completed", "failed"} else None
    cur.execute(
        """
        UPDATE automation_runs
        SET status = ?,
            message = ?,
            fetched_count = ?,
            shortlisted_count = ?,
            applied_count = ?,
            finished_at = COALESCE(?, finished_at)
        WHERE id = ?
        """,
        (status, message, fetched_count, shortlisted_count, applied_count, finished_at, run_id),
    )
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
               started_at, finished_at
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
               started_at, finished_at
        FROM automation_runs
        WHERE user_id = ? AND id = ?
        LIMIT 1
        """,
        (user_id, run_id),
    )
    row = cur.fetchone()
    conn.close()
    return row
