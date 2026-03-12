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
import sqlite3


router = APIRouter(prefix="/api/session")


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


@router.get("")
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
    log_admin_event("user_login", f"Session API login success: {saved_email}", user_id=user_id)
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
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax", secure=False)
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

    log_admin_event("user_signup", f"Session API signup: {normalized_email} as {role}", user_id=user_id)
    token = create_token(user_id, role=role)
    row = get_user_by_id(user_id)
    response = JSONResponse(
        {
            "status": "success",
            "user": _user_payload(row),
            "ui_preferences": get_ui_preferences(user_id=user_id),
        }
    )
    response.set_cookie(key="session", value=token, httponly=True, samesite="lax", secure=False)
    return response


@router.post("/logout")
def logout(request: Request):
    if getattr(request.state, "user_id", None):
        log_admin_event("user_logout", "Session API logout", user_id=request.state.user_id)
    response = JSONResponse({"status": "success"})
    response.delete_cookie("session")
    return response


@router.post("/forgot-password")
def forgot_password(email: str = Form(...)):
    token = create_password_reset_token(email=email.strip().lower())
    if token:
        log_admin_event("password_reset_requested", f"Reset token generated for {email}: {token}")
    return {"status": "success", "message": "If this email exists, a reset link has been generated."}


@router.post("/reset-password/{token}")
def reset_password(token: str, new_password: str = Form(...)):
    if len(new_password or "") < 6:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Password must be at least 6 characters"})
    user_id = use_password_reset_token(token)
    if not user_id:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid or expired token"})
    update_user_password_hash(user_id, hash_password(new_password))
    log_admin_event("password_reset_completed", f"Reset completed for user {user_id}", user_id=user_id)
    return {"status": "success"}
