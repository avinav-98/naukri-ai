import sqlite3

from backend.config import DATABASE_PATHS


DB = DATABASE_PATHS["settings"]


def _bounded_int(value, default: int, min_v: int = 1, max_v: int = 20) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_v, min(max_v, parsed))


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
            keywords TEXT DEFAULT '',
            scan_mode TEXT DEFAULT 'basic',
            pages_to_scrape INTEGER DEFAULT 5,
            auto_apply_limit INTEGER DEFAULT 10,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS keywords_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, keyword)
        )
        """
    )
    # Lightweight runtime migrations for older settings table.
    cursor.execute("PRAGMA table_info(settings)")
    cols = {r[1] for r in cursor.fetchall()}
    if "keywords" not in cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN keywords TEXT DEFAULT ''")
    if "scan_mode" not in cols:
        cursor.execute("ALTER TABLE settings ADD COLUMN scan_mode TEXT DEFAULT 'basic'")
    conn.commit()
    conn.close()


def parse_keywords(raw_keywords: str):
    items = []
    for part in (raw_keywords or "").replace("\n", ",").split(","):
        token = part.strip()
        if token:
            items.append(token)
    # Preserve order while deduplicating.
    unique = []
    seen = set()
    for kw in items:
        key = kw.lower()
        if key not in seen:
            seen.add(key)
            unique.append(kw)
    return unique


def save_keywords(user_id: int, raw_keywords: str):
    init_settings_table()
    keywords = parse_keywords(raw_keywords)
    if not keywords:
        return
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    for kw in keywords:
        cursor.execute(
            """
            INSERT OR IGNORE INTO keywords_store (user_id, keyword)
            VALUES (?, ?)
            """,
            (user_id, kw),
        )
    conn.commit()
    conn.close()


def save_keyword_list(user_id: int, keywords: list[str]):
    save_keywords(user_id=user_id, raw_keywords=",".join(keywords or []))


def get_keywords(user_id: int):
    init_settings_table()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT keyword
        FROM keywords_store
        WHERE user_id = ?
        ORDER BY keyword COLLATE NOCASE ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]


def save_settings(data: dict, user_id: int):
    init_settings_table()
    pages_to_scrape = _bounded_int(data.get("pages_to_scrape", 5), default=5)
    auto_apply_limit = _bounded_int(data.get("auto_apply_limit", 10), default=10)
    keywords_raw = data.get("keywords", "") or ""
    scan_mode = (data.get("scan_mode", "basic") or "basic").strip().lower()
    if scan_mode not in {"basic", "advance", "extreme"}:
        scan_mode = "basic"

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
    cursor.execute(
        """
        INSERT INTO settings (
            user_id, job_role, preferred_location, experience, salary, keywords, scan_mode,
            pages_to_scrape, auto_apply_limit
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data.get("job_role", ""),
            data.get("preferred_location", ""),
            data.get("experience", ""),
            data.get("salary", ""),
            keywords_raw,
            scan_mode,
            pages_to_scrape,
            auto_apply_limit,
        ),
    )
    conn.commit()
    conn.close()
    save_keywords(user_id=user_id, raw_keywords=keywords_raw)


def get_settings(user_id: int):
    init_settings_table()
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT job_role, preferred_location, experience, salary, keywords, scan_mode,
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
            "keywords": "",
            "scan_mode": "basic",
            "pages_to_scrape": 5,
            "auto_apply_limit": 10,
        }

    return {
        "job_role": row[0],
        "preferred_location": row[1],
        "experience": row[2],
        "salary": row[3],
        "keywords": row[4] or "",
        "scan_mode": row[5] or "basic",
        "pages_to_scrape": row[6],
        "auto_apply_limit": row[7],
    }
