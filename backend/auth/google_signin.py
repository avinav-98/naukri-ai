from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import sqlite3
from backend.auth.jwt_handler import create_token
from backend.models.admin_log_model import log_admin_event
from backend.models.user_model import count_users, update_last_login
from backend.utils.db_migrations import ensure_users_schema

router = APIRouter()

@router.post("/signin-google")
async def google_signin(request: Request):

    data = await request.json()

    email = data.get("email")
    name = data.get("name")

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()
    ensure_users_schema(conn)

    cursor.execute("SELECT id, role, account_status FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    if not user:
        role = "admin" if count_users() == 0 else "user"

        cursor.execute("""
            INSERT INTO users (full_name,email,password_hash,role,account_status)
            VALUES (?,?,?,?, 'active')
        """,(name,email,"google", role))

        conn.commit()

        cursor.execute("SELECT id, role, account_status FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

    conn.close()

    user_id, role, account_status = user
    role = (role or "user").strip().lower()
    account_status = (account_status or "active").strip().lower()
    if account_status != "active":
        return JSONResponse(status_code=403, content={"status": "error", "error": "Account disabled. Contact admin."})

    update_last_login(user_id)
    log_admin_event("user_login", f"Google login success: {email}", user_id=user_id)
    token = create_token(user_id, role=role)
    response = JSONResponse({"status":"success"})
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False
    )

    return response
