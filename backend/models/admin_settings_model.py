import sqlite3

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_admin_settings_schema


DB = DATABASE_PATHS["settings"]


def get_admin_settings() -> dict:
    conn = sqlite3.connect(DB)
    ensure_admin_settings_schema(conn)
    cur = conn.cursor()
    cur.execute("SELECT setting_key, setting_value FROM admin_settings ORDER BY setting_key ASC")
    rows = cur.fetchall()
    conn.close()
    return {k: v for k, v in rows}


def save_admin_setting(setting_key: str, setting_value: str):
    conn = sqlite3.connect(DB)
    ensure_admin_settings_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO admin_settings (setting_key, setting_value)
        VALUES (?, ?)
        ON CONFLICT(setting_key) DO UPDATE SET
            setting_value=excluded.setting_value,
            updated_at=CURRENT_TIMESTAMP
        """,
        (setting_key, setting_value),
    )
    conn.commit()
    conn.close()
