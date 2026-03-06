import sqlite3


def _table_columns(conn: sqlite3.Connection, table_name: str):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cur.fetchall()}


def _ensure_column(conn: sqlite3.Connection, table_name: str, ddl: str):
    col_name = ddl.split()[0]
    cols = _table_columns(conn, table_name)
    if col_name not in cols:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def ensure_users_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            email TEXT UNIQUE,
            password_hash TEXT,
            naukri_id TEXT,
            naukri_password_enc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    _ensure_column(conn, "users", "full_name TEXT")
    _ensure_column(conn, "users", "password_hash TEXT")
    _ensure_column(conn, "users", "naukri_id TEXT")
    _ensure_column(conn, "users", "naukri_password_enc TEXT")

    # Legacy column backfill
    cols = _table_columns(conn, "users")
    if "password" in cols:
        cursor.execute(
            """
            UPDATE users
            SET password_hash = COALESCE(password_hash, password)
            """
        )
    if "naukri_email" in cols:
        cursor.execute(
            """
            UPDATE users
            SET naukri_id = COALESCE(naukri_id, naukri_email)
            """
        )
    if "naukri_password" in cols:
        cursor.execute(
            """
            UPDATE users
            SET naukri_password_enc = COALESCE(naukri_password_enc, naukri_password)
            """
        )

    conn.commit()


def ensure_jobs_directory_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT,
            company TEXT,
            location TEXT,
            experience TEXT,
            salary TEXT,
            job_url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column(conn, "jobs_directory", "user_id INTEGER NOT NULL DEFAULT 1")
    _ensure_column(conn, "jobs_directory", "experience TEXT")
    _ensure_column(conn, "jobs_directory", "salary TEXT")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_user_url
        ON jobs_directory(user_id, job_url)
        """
    )
    conn.commit()


def ensure_relevant_jobs_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS relevant_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            job_url TEXT,
            score REAL NOT NULL DEFAULT 0,
            ranked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column(conn, "relevant_jobs", "user_id INTEGER NOT NULL DEFAULT 1")
    _ensure_column(conn, "relevant_jobs", "score REAL NOT NULL DEFAULT 0")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relevant_user_url
        ON relevant_jobs(user_id, job_url)
        """
    )
    conn.commit()


def ensure_applied_jobs_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT,
            company TEXT,
            location TEXT,
            job_url TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column(conn, "applied_jobs", "user_id INTEGER NOT NULL DEFAULT 1")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_applied_user_url
        ON applied_jobs(user_id, job_url)
        """
    )
    conn.commit()


def ensure_standard_jobs_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS standard_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT,
            company TEXT,
            location TEXT,
            job_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    _ensure_column(conn, "standard_jobs", "user_id INTEGER NOT NULL DEFAULT 1")
    _ensure_column(conn, "standard_jobs", "status TEXT DEFAULT 'pending'")
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_standard_user_url
        ON standard_jobs(user_id, job_url)
        """
    )
    conn.commit()
