import sqlite3

from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_user_ui_preferences_schema


DB = DATABASE_PATHS["settings"]


def get_ui_preferences(user_id: int) -> dict:
    conn = sqlite3.connect(DB)
    ensure_user_ui_preferences_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT theme_mode, layout_mode, accent_color
        FROM user_ui_preferences
        WHERE user_id = ?
        LIMIT 1
        """,
        (user_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"theme_mode": "system", "layout_mode": "standard", "accent_color": "#0b57d0"}
    return {"theme_mode": row[0] or "system", "layout_mode": row[1] or "standard", "accent_color": row[2] or "#0b57d0"}


def save_ui_preferences(user_id: int, theme_mode: str, layout_mode: str, accent_color: str):
    if theme_mode not in {"light", "dark", "system"}:
        theme_mode = "system"
    if layout_mode not in {"compact", "standard", "wide"}:
        layout_mode = "standard"
    accent_color = (accent_color or "#0b57d0").strip()[:20]

    conn = sqlite3.connect(DB)
    ensure_user_ui_preferences_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO user_ui_preferences (user_id, theme_mode, layout_mode, accent_color)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            theme_mode=excluded.theme_mode,
            layout_mode=excluded.layout_mode,
            accent_color=excluded.accent_color,
            updated_at=CURRENT_TIMESTAMP
        """,
        (user_id, theme_mode, layout_mode, accent_color),
    )
    conn.commit()
    conn.close()
