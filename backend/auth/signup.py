from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import sqlite3
from backend.auth.password_hash import hash_password
from backend.security.credentials_crypto import encrypt_text
from backend.utils.db_migrations import ensure_users_schema

router = APIRouter()

@router.post("/signup")
async def signup(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    naukri_id: str = Form(...),
    naukri_password: str = Form(...)
):

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()
    ensure_users_schema(conn)

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse(
            status_code=409,
            content={"status": "error", "error": "Email already registered"},
        )

    password_hash = hash_password(password)
    encrypted_naukri_password = encrypt_text(naukri_password)

    cursor.execute("""
        INSERT INTO users
        (full_name, email, password_hash, naukri_id, naukri_password_enc)
        VALUES (?, ?, ?, ?, ?)
    """, (full_name, email, password_hash, naukri_id, encrypted_naukri_password))

    conn.commit()
    conn.close()

    return {"status": "success"}
