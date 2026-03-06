import sqlite3
from pathlib import Path


DB_DIR = Path("database")


def ensure_db_dir():
    DB_DIR.mkdir(parents=True, exist_ok=True)


def create_users_db():
    conn = sqlite3.connect(DB_DIR / "users.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            naukri_id TEXT,
            naukri_password_enc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def create_jobs_directory_db():
    conn = sqlite3.connect(DB_DIR / "jobs_directory.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs_directory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            experience TEXT,
            salary TEXT,
            job_url TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_user_url
        ON jobs_directory(user_id, job_url)
        """
    )
    conn.commit()
    conn.close()


def create_relevant_jobs_db():
    conn = sqlite3.connect(DB_DIR / "relevant_jobs.db")
    cur = conn.cursor()
    cur.execute(
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
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_relevant_user_url
        ON relevant_jobs(user_id, job_url)
        """
    )
    conn.commit()
    conn.close()


def create_applied_jobs_db():
    conn = sqlite3.connect(DB_DIR / "applied_jobs.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applied_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            job_url TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_applied_user_url
        ON applied_jobs(user_id, job_url)
        """
    )
    conn.commit()
    conn.close()


def create_standard_jobs_db():
    conn = sqlite3.connect(DB_DIR / "standard_jobs.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS standard_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            job_url TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_standard_user_url
        ON standard_jobs(user_id, job_url)
        """
    )
    conn.commit()
    conn.close()


def create_settings_db():
    conn = sqlite3.connect(DB_DIR / "settings.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            job_role TEXT,
            preferred_location TEXT,
            experience TEXT,
            salary TEXT,
            pages_to_scrape INTEGER DEFAULT 5,
            auto_apply_limit INTEGER DEFAULT 10,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def create_automation_runs_db():
    conn = sqlite3.connect(DB_DIR / "automation_runs.db")
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


def main():
    ensure_db_dir()
    create_users_db()
    create_jobs_directory_db()
    create_relevant_jobs_db()
    create_applied_jobs_db()
    create_standard_jobs_db()
    create_settings_db()
    create_automation_runs_db()
    print("Database initialization completed.")


if __name__ == "__main__":
    main()
