import sqlite3

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from backend.auth.jwt_handler import create_token
from backend.auth.password_hash import hash_password, verify_password
from backend.models.admin_log_model import log_admin_event
from backend.models.ui_preferences_model import get_ui_preferences
from backend.models.user_model import (
    count_users,
    create_password_reset_token,
    get_user_by_email,
    get_user_by_id,
    update_last_login,
    update_user_password_hash,
    use_password_reset_token,
)
from backend.security.credentials_crypto import encrypt_text
from backend.config import DATABASE_PATHS
from backend.utils.db_migrations import ensure_users_schema


router = APIRouter(prefix="/auth")


def _user_payload(row):
    return {
        "id": row[0],
        "full_name": row[1] or "",
        "email": row[2] or "",
        "naukri_id": row[3] or "",
        "role": row[4] or "user",
        "account_status": row[5] or "active",
        "last_login": row[6],
        "created_at": row[7],
    }


def _set_session_cookie(response: JSONResponse, token: str):
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax", secure=False)


def _log_password_reset_request(user_id: int | None, success: bool):
    log_admin_event(
        "password_reset_requested",
        f"status={'success' if success else 'ignored'}",
        user_id=user_id,
        level="info",
    )


@router.get("/session")
def read_session(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return JSONResponse(status_code=401, content={"status": "error", "error": "Authentication required"})

    row = get_user_by_id(user_id)
    if not row:
        return JSONResponse(status_code=401, content={"status": "error", "error": "Session user not found"})

    return {
        "status": "authenticated",
        "user": _user_payload(row),
        "ui_preferences": get_ui_preferences(user_id=user_id),
    }


@router.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email.strip().lower())
    if not user:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})

    user_id, full_name, saved_email, password_hash_value, _, _, role, account_status, last_login, created_at = user
    role = (role or "user").strip().lower()
    account_status = (account_status or "active").strip().lower()
    if account_status != "active":
        return JSONResponse(status_code=403, content={"status": "error", "error": "Account disabled. Contact admin."})
    if not password_hash_value or not verify_password(password, password_hash_value):
        return JSONResponse(status_code=401, content={"status": "error", "error": "Invalid email or password"})

    update_last_login(user_id)
    log_admin_event("user_login", "status=success", user_id=user_id)
    token = create_token(user_id, role=role)
    response = JSONResponse(
        {
            "status": "success",
            "user": {
                "id": user_id,
                "full_name": full_name or "",
                "email": saved_email or "",
                "naukri_id": user[4] or "",
                "role": role,
                "account_status": account_status,
                "last_login": last_login,
                "created_at": created_at,
            },
            "ui_preferences": get_ui_preferences(user_id=user_id),
        }
    )
    _set_session_cookie(response, token)
    return response


@router.post("/signup")
def signup(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    naukri_id: str = Form(""),
    naukri_password: str = Form(""),
):
    normalized_email = email.strip().lower()
    if get_user_by_email(normalized_email):
        return JSONResponse(status_code=409, content={"status": "error", "error": "Email already registered"})

    conn = sqlite3.connect(DATABASE_PATHS["users"])
    ensure_users_schema(conn)
    cursor = conn.cursor()
    role = "admin" if count_users() == 0 else "user"
    cursor.execute(
        """
        INSERT INTO users
        (full_name, email, password_hash, naukri_id, naukri_password_enc, role, account_status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        """,
        (
            full_name.strip(),
            normalized_email,
            hash_password(password),
            naukri_id.strip(),
            encrypt_text(naukri_password.strip()) if naukri_password.strip() else "",
            role,
        ),
    )
    user_id = int(cursor.lastrowid)
    conn.commit()
    conn.close()

    log_admin_event("user_signup", f"status=success role={role}", user_id=user_id)
    token = create_token(user_id, role=role)
    row = get_user_by_id(user_id)
    response = JSONResponse(
        {
            "status": "success",
            "user": _user_payload(row),
            "ui_preferences": get_ui_preferences(user_id=user_id),
        }
    )
    _set_session_cookie(response, token)
    return response


@router.post("/logout")
def logout(request: Request):
    if getattr(request.state, "user_id", None):
        log_admin_event("user_logout", "status=success", user_id=request.state.user_id)
    response = JSONResponse({"status": "success"})
    response.delete_cookie("session")
    return response


@router.post("/google")
async def google_signin(request: Request):
    data = await request.json()
    email = (data.get("email") or "").strip().lower()
    name = (data.get("name") or "").strip()
    if not email or not name:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Email and name are required"})

    conn = sqlite3.connect(DATABASE_PATHS["users"])
    ensure_users_schema(conn)
    cursor = conn.cursor()
    cursor.execute("SELECT id, role, account_status FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        role = "admin" if count_users() == 0 else "user"
        cursor.execute(
            """
            INSERT INTO users (full_name, email, password_hash, role, account_status)
            VALUES (?, ?, ?, ?, 'active')
            """,
            (name, email, "google", role),
        )
        conn.commit()
        cursor.execute("SELECT id, role, account_status FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

    conn.close()

    user_id, role, account_status = user
    role = (role or "user").strip().lower()
    account_status = (account_status or "active").strip().lower()
    if account_status != "active":
        return JSONResponse(status_code=403, content={"status": "error", "error": "Account disabled. Contact admin."})

    update_last_login(user_id)
    log_admin_event("user_login", "status=success provider=google", user_id=user_id)
    token = create_token(user_id, role=role)
    response = JSONResponse({"status": "success"})
    _set_session_cookie(response, token)
    return response


@router.post("/forgot-password")
def forgot_password(email: str = Form(...)):
    normalized_email = email.strip().lower()
    user = get_user_by_email(normalized_email)
    token = create_password_reset_token(email=normalized_email) if user else None
    _log_password_reset_request(user[0] if user else None, bool(token))
    return {"status": "success", "message": "If this email exists, a reset link has been generated."}


@router.post("/reset-password")
def reset_password(token: str = Form(...), new_password: str = Form(...)):
    if len(new_password or "") < 6:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Password must be at least 6 characters"})
    user_id = use_password_reset_token(token)
    if not user_id:
        log_admin_event("password_reset_completed", "status=failure", level="warning")
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid or expired token"})
    update_user_password_hash(user_id, hash_password(new_password))
    log_admin_event("password_reset_completed", "status=success", user_id=user_id)
    return {"status": "success"}
