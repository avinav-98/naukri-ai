import sqlite3
from pathlib import Path

from backend.config import DATABASE_DIR, MAIN_DATABASE_PATH
from backend.models.pipeline_run_model import init_runs_table
from backend.utils.db_migrations import (
    ensure_admin_logs_schema,
    ensure_admin_settings_schema,
    ensure_applied_jobs_schema,
    ensure_ext_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_password_reset_schema,
    ensure_relevant_jobs_schema,
    ensure_standard_jobs_schema,
    ensure_user_ui_preferences_schema,
    ensure_users_schema,
)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(db_path or MAIN_DATABASE_PATH)


def initialize_main_database():
    conn = get_connection()
    ensure_users_schema(conn)
    ensure_password_reset_schema(conn)
    ensure_user_ui_preferences_schema(conn)
    ensure_admin_settings_schema(conn)
    ensure_admin_logs_schema(conn)
    ensure_jobs_directory_schema(conn)
    ensure_relevant_jobs_schema(conn)
    ensure_applied_jobs_schema(conn)
    ensure_ext_jobs_schema(conn)
    ensure_standard_jobs_schema(conn)
    conn.close()
    init_runs_table()


def initialize_database():
    initialize_main_database()
