import sqlite3

from backend.config import DATABASE_PATHS
from backend.security.credentials_crypto import decrypt_text
from backend.utils.db_migrations import ensure_users_schema


DB = DATABASE_PATHS["users"]


def create_users_table():
    conn = sqlite3.connect(DB)
    ensure_users_schema(conn)
    conn.close()


def get_user_by_email(email):
    conn = sqlite3.connect(DB)
    ensure_users_schema(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, full_name, email, password_hash, naukri_id, naukri_password_enc
        FROM users
        WHERE email = ?
        """,
        (email,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = sqlite3.connect(DB)
    ensure_users_schema(conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, full_name, email, naukri_id
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_naukri_credentials(user_id):
    conn = sqlite3.connect(DB)
    ensure_users_schema(conn)
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
        # Backward compatibility for older plaintext records.
        password = encrypted_password

    return {"naukri_id": naukri_id, "naukri_password": password}
