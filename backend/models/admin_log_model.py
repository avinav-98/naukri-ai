import sqlite3

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_admin_logs_schema


DB = DATABASE_PATHS["runs"]


def log_admin_event(event_type: str, details: str = "", user_id: int | None = None, level: str = "info"):
    conn = sqlite3.connect(DB)
    ensure_admin_logs_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO admin_logs (user_id, event_type, details, level)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, event_type, details, level),
    )
    conn.commit()
    conn.close()


def list_admin_logs(limit: int = 500):
    conn = sqlite3.connect(DB)
    ensure_admin_logs_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, event_type, details, level, created_at
        FROM admin_logs
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows
