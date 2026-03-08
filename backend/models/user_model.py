import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

from backend.config import DATABASE_PATHS
from backend.security.credentials_crypto import decrypt_text, encrypt_text
from backend.utils.db_migrations import ensure_password_reset_schema, ensure_users_schema


DB = DATABASE_PATHS["users"]


def _conn():
    conn = sqlite3.connect(DB)
    ensure_users_schema(conn)
    ensure_password_reset_schema(conn)
    return conn


def create_users_table():
    conn = _conn()
    conn.close()


def count_users() -> int:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    n = int(cur.fetchone()[0] or 0)
    conn.close()
    return n


def get_user_by_email(email):
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, full_name, email, password_hash, naukri_id, naukri_password_enc, role, account_status, last_login, created_at
        FROM users
        WHERE email = ?
        """,
        (email,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, full_name, email, naukri_id, role, account_status, last_login, created_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def create_user(full_name: str, email: str, password_hash: str, naukri_id: str = "", naukri_password: str = "", role: str = "user") -> int:
    enc = encrypt_text(naukri_password) if naukri_password else ""
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (full_name, email, password_hash, naukri_id, naukri_password_enc, role, account_status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        """,
        (full_name, email, password_hash, naukri_id, enc, role),
    )
    user_id = int(cur.lastrowid)
    conn.commit()
    conn.close()
    return user_id


def update_last_login(user_id: int):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def update_user_role(user_id: int, role: str):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
    conn.commit()
    conn.close()


def update_account_status(user_id: int, status: str):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET account_status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()


def update_user_password_hash(user_id: int, password_hash: str):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    conn.commit()
    conn.close()


def update_user_profile_and_naukri(user_id: int, full_name: str, email: str, naukri_id: str, naukri_password: str | None = None):
    conn = _conn()
    cur = conn.cursor()
    if naukri_password is None or naukri_password == "":
        cur.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, naukri_id = ?
            WHERE id = ?
            """,
            (full_name, email, naukri_id, user_id),
        )
    else:
        cur.execute(
            """
            UPDATE users
            SET full_name = ?, email = ?, naukri_id = ?, naukri_password_enc = ?
            WHERE id = ?
            """,
            (full_name, email, naukri_id, encrypt_text(naukri_password), user_id),
        )
    conn.commit()
    conn.close()


def delete_user(user_id: int):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def list_users(limit: int = 500):
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, full_name, email, role, account_status, last_login, created_at
        FROM users
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_naukri_credentials(user_id):
    conn = _conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT naukri_id, naukri_password_enc FROM users WHERE id = ?",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    naukri_id, encrypted_password = row
    if not naukri_id or not encrypted_password:
        return None

    try:
        password = decrypt_text(encrypted_password)
    except Exception:
        password = encrypted_password

    return {"naukri_id": naukri_id, "naukri_password": password}


def create_password_reset_token(email: str, ttl_minutes: int = 30) -> str | None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    user_id = int(row[0])
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)).isoformat()
    cur.execute("UPDATE password_resets SET used = 1 WHERE user_id = ? AND used = 0", (user_id,))
    cur.execute(
        """
        INSERT INTO password_resets (user_id, token, expires_at, used)
        VALUES (?, ?, ?, 0)
        """,
        (user_id, token, expires_at),
    )
    conn.commit()
    conn.close()
    return token


def use_password_reset_token(token: str) -> int | None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, expires_at, used
        FROM password_resets
        WHERE token = ?
        LIMIT 1
        """,
        (token,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    reset_id, user_id, expires_at, used = row
    if int(used or 0) == 1:
        conn.close()
        return None
    try:
        exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except Exception:
        conn.close()
        return None
    if datetime.now(timezone.utc) > exp:
        conn.close()
        return None
    cur.execute("UPDATE password_resets SET used = 1 WHERE id = ?", (reset_id,))
    conn.commit()
    conn.close()
    return int(user_id)
