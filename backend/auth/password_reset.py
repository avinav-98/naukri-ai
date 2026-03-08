from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse

from backend.auth.password_hash import hash_password
from backend.models.admin_log_model import log_admin_event
from backend.models.user_model import create_password_reset_token, update_user_password_hash, use_password_reset_token


router = APIRouter()


@router.post("/forgot-password")
def forgot_password(email: str = Form(...)):
    token = create_password_reset_token(email=email.strip().lower())
    # In this local setup we log the token for manual testing/integration.
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
