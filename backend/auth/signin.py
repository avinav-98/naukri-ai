from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import sqlite3
from backend.auth.password_hash import verify_password
from backend.auth.jwt_handler import create_token
from backend.utils.db_migrations import ensure_users_schema

router = APIRouter()

@router.post("/signin")
async def signin(
    email: str = Form(...),
    password: str = Form(...)
):

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()
    ensure_users_schema(conn)

    cursor.execute(
        "SELECT id, password_hash FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "error": "User not found"}

    user_id, password_hash = user
    if not password_hash:
        return {"status": "error", "error": "Password login unavailable for this account"}

    if not verify_password(password, password_hash):
        return {"status": "error", "error": "Invalid password"}

    token = create_token(user_id)

    response = JSONResponse({"status": "success"})
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response
