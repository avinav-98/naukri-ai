import sqlite3

from backend.config import DATABASE_PATHS


DB = DATABASE_PATHS["settings"]


def init_settings_table():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
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


def save_settings(data: dict, user_id: int):
    init_settings_table()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
    cursor.execute(
        """
        INSERT INTO settings (
            user_id, job_role, preferred_location, experience, salary,
            pages_to_scrape, auto_apply_limit
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data.get("job_role", ""),
            data.get("preferred_location", ""),
            data.get("experience", ""),
            data.get("salary", ""),
            int(data.get("pages_to_scrape", 5)),
            int(data.get("auto_apply_limit", 10)),
        ),
    )
    conn.commit()
    conn.close()


def get_settings(user_id: int):
    init_settings_table()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT job_role, preferred_location, experience, salary,
               pages_to_scrape, auto_apply_limit
        FROM settings
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "job_role": "",
            "preferred_location": "",
            "experience": "",
            "salary": "",
            "pages_to_scrape": 5,
            "auto_apply_limit": 10,
        }

    return {
        "job_role": row[0],
        "preferred_location": row[1],
        "experience": row[2],
        "salary": row[3],
        "pages_to_scrape": row[4],
        "auto_apply_limit": row[5],
    }
