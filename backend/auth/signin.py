from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import sqlite3
from backend.auth.password_hash import verify_password
from backend.auth.jwt_handler import create_token
from backend.models.admin_log_model import log_admin_event
from backend.models.user_model import update_last_login
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

    cursor.execute("SELECT id, password_hash, role, account_status FROM users WHERE email=?", (email,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "error": "User not found"}

    user_id, password_hash, role, account_status = user
    role = (role or "user").strip().lower()
    account_status = (account_status or "active").strip().lower()
    if account_status != "active":
        return {"status": "error", "error": "Account disabled. Contact admin."}
    if not password_hash:
        return {"status": "error", "error": "Password login unavailable for this account"}

    if not verify_password(password, password_hash):
        return {"status": "error", "error": "Invalid password"}

    update_last_login(user_id)
    log_admin_event("user_login", f"Email login success: {email}", user_id=user_id)
    token = create_token(user_id, role=role)

    response = JSONResponse({"status": "success"})
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response
