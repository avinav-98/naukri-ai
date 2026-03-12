import sqlite3
from pathlib import Path

from backend.config import DATABASE_DIR, DATABASE_PATHS, LEGACY_DATABASE_PATHS, MAIN_DATABASE_PATH
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


def _mark_migration_applied(conn: sqlite3.Connection, key: str):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _system_migrations (
            migration_key TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO _system_migrations (migration_key)
        VALUES (?)
        """,
        (key,),
    )
    conn.commit()


def _is_migration_applied(conn: sqlite3.Connection, key: str) -> bool:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _system_migrations (
            migration_key TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM _system_migrations WHERE migration_key = ? LIMIT 1", (key,))
    return cur.fetchone() is not None


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


def _copy_rows(src_path: Path, main_conn: sqlite3.Connection, table: str, insert_sql: str, select_sql: str):
    if not src_path.exists() or src_path.resolve() == MAIN_DATABASE_PATH.resolve():
        return
    src_conn = sqlite3.connect(src_path)
    try:
        src_cur = src_conn.cursor()
        src_cur.execute(select_sql)
        rows = src_cur.fetchall()
        if rows:
            main_conn.executemany(insert_sql, rows)
            main_conn.commit()
    except sqlite3.Error:
        pass
    finally:
        src_conn.close()


def migrate_legacy_databases():
    migration_key = "legacy_split_db_to_main_v1"
    main_conn = get_connection()
    initialize_main_database()
    if _is_migration_applied(main_conn, migration_key):
        main_conn.close()
        return

    _copy_rows(
        LEGACY_DATABASE_PATHS["users"],
        main_conn,
        "users",
        """
        INSERT OR IGNORE INTO users
        (id, full_name, email, password_hash, naukri_id, naukri_password_enc, role, account_status, last_login, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, full_name, email, password_hash, naukri_id, naukri_password_enc,
               COALESCE(role, 'user'), COALESCE(account_status, 'active'), last_login, created_at
        FROM users
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["settings"],
        main_conn,
        "settings",
        """
        INSERT OR IGNORE INTO settings
        (id, user_id, job_role, preferred_location, experience, salary, keywords, scan_mode, pages_to_scrape, auto_apply_limit, max_job_age_days, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_role, preferred_location, experience, salary,
               COALESCE(keywords, ''), COALESCE(scan_mode, 'basic'),
               COALESCE(pages_to_scrape, 5), COALESCE(auto_apply_limit, 10),
               COALESCE(max_job_age_days, 10), updated_at
        FROM settings
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["settings"],
        main_conn,
        "keywords_store",
        """
        INSERT OR IGNORE INTO keywords_store
        (id, user_id, keyword, created_at)
        VALUES (?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, keyword, created_at
        FROM keywords_store
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["jobs"],
        main_conn,
        "jobs_directory",
        """
        INSERT OR IGNORE INTO jobs_directory
        (id, user_id, job_title, company, location, experience, salary, job_description, key_skills_text, resume_match_score, posted_date_text, posted_ts, normalized_title, normalized_company, normalized_location, job_url, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_title, company, location, experience, salary, job_description,
               COALESCE(key_skills_text, ''), COALESCE(resume_match_score, 0),
               posted_date_text, COALESCE(posted_ts, 0), normalized_title, normalized_company, normalized_location, job_url, scraped_at
        FROM jobs_directory
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["relevant"],
        main_conn,
        "relevant_jobs",
        """
        INSERT OR IGNORE INTO relevant_jobs
        (id, user_id, job_title, company, location, job_url, score, ranked_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_title, company, location, job_url, score, ranked_at
        FROM relevant_jobs
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["applied"],
        main_conn,
        "applied_jobs",
        """
        INSERT OR IGNORE INTO applied_jobs
        (id, user_id, job_title, company, location, experience, job_url, status, applied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_title, company, location, COALESCE(experience, ''), job_url,
               COALESCE(status, 'applied'), applied_at
        FROM applied_jobs
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["ext"],
        main_conn,
        "ext_jobs",
        """
        INSERT OR IGNORE INTO ext_jobs
        (id, user_id, job_title, company, location, experience, resume_match_score, job_url, external_apply_url, captured_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_title, company, location, experience, COALESCE(resume_match_score, 0), job_url, external_apply_url, captured_at
        FROM ext_jobs
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["standard"],
        main_conn,
        "standard_jobs",
        """
        INSERT OR IGNORE INTO standard_jobs
        (id, user_id, job_title, company, location, job_url, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, job_title, company, location, job_url, COALESCE(status, 'pending'), created_at
        FROM standard_jobs
        """,
    )
    _copy_rows(
        LEGACY_DATABASE_PATHS["runs"],
        main_conn,
        "automation_runs",
        """
        INSERT OR IGNORE INTO automation_runs
        (id, user_id, run_type, status, message, pages, auto_apply_limit, fetched_count, shortlisted_count, applied_count, celery_task_id, started_at, finished_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        """
        SELECT id, user_id, run_type, status, message, pages, auto_apply_limit,
               fetched_count, shortlisted_count, applied_count, celery_task_id, started_at, finished_at
        FROM automation_runs
        """,
    )

    _mark_migration_applied(main_conn, migration_key)
    main_conn.close()


def initialize_database():
    initialize_main_database()
    migrate_legacy_databases()
