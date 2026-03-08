import os
import sqlite3
from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse

from backend.auth.password_hash import hash_password
from backend.config import DATABASE_PATHS
from backend.models.admin_log_model import list_admin_logs, log_admin_event
from backend.models.admin_settings_model import get_admin_settings, save_admin_setting
from backend.models.settings_model import get_settings, save_settings
from backend.models.ui_preferences_model import get_ui_preferences
from backend.models.pipeline_run_model import init_runs_table
from backend.models.user_model import (
    delete_user,
    get_user_by_id,
    list_users,
    update_account_status,
    update_user_password_hash,
    update_user_profile_and_naukri,
    update_user_role,
)
from backend.utils.db_migrations import (
    ensure_users_schema,
    ensure_admin_logs_schema,
    ensure_admin_settings_schema,
    ensure_applied_jobs_schema,
    ensure_ext_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_relevant_jobs_schema,
    ensure_standard_jobs_schema,
)


router = APIRouter(prefix="/api/admin")


def _deny(message: str = "Forbidden"):
    return JSONResponse(status_code=403, content={"status": "error", "error": message})


def _is_admin(request: Request) -> bool:
    return getattr(request.state, "role", "user") == "admin"


def _is_admin_or_coadmin(request: Request) -> bool:
    return getattr(request.state, "role", "user") in {"admin", "co_admin"}


def _table_count(db_path: Path, ensure_fn, table: str, where: str = "", params=()):
    conn = sqlite3.connect(db_path)
    ensure_fn(conn)
    cur = conn.cursor()
    q = f"SELECT COUNT(*) FROM {table}"
    if where:
        q += f" WHERE {where}"
    cur.execute(q, params)
    n = int(cur.fetchone()[0] or 0)
    conn.close()
    return n


@router.get("/overview")
def admin_overview(request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()
    total_users = len(list_users(limit=5000))
    active_users = _table_count(DATABASE_PATHS["users"], ensure_users_schema, "users", "lower(account_status) = 'active'")
    total_jobs_scraped = _table_count(DATABASE_PATHS["jobs"], ensure_jobs_directory_schema, "jobs_directory")
    total_jobs_applied = _table_count(DATABASE_PATHS["applied"], ensure_applied_jobs_schema, "applied_jobs", "lower(status) = 'applied'")
    external_jobs_count = _table_count(DATABASE_PATHS["ext"], ensure_ext_jobs_schema, "ext_jobs")
    init_runs_table()
    pipeline_runs_today = _table_count(DATABASE_PATHS["runs"], lambda c: None, "automation_runs", "date(started_at) = date('now')")
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_jobs_scraped": total_jobs_scraped,
        "total_jobs_applied": total_jobs_applied,
        "external_jobs_count": external_jobs_count,
        "pipeline_runs_today": pipeline_runs_today,
    }


@router.get("/users")
def admin_users(request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()
    rows = list_users(limit=2000)
    return [
        {
            "id": r[0],
            "full_name": r[1],
            "email": r[2],
            "role": r[3] or "user",
            "account_status": r[4] or "active",
            "last_login": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]


@router.get("/users/{target_user_id}/profile")
def admin_user_profile(target_user_id: int, request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()
    row = get_user_by_id(target_user_id)
    if not row:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})
    return {
        "id": row[0],
        "full_name": row[1],
        "email": row[2],
        "naukri_id": row[3] or "",
        "role": row[4] or "user",
        "account_status": row[5] or "active",
        "last_login": row[6],
        "created_at": row[7],
        "settings": get_settings(user_id=target_user_id),
        "ui_preferences": get_ui_preferences(user_id=target_user_id),
    }


@router.post("/users/{target_user_id}/profile")
def admin_update_user_profile(
    target_user_id: int,
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    naukri_id: str = Form(""),
    naukri_password: str = Form(""),
):
    if not _is_admin_or_coadmin(request):
        return _deny()
    update_user_profile_and_naukri(
        user_id=target_user_id,
        full_name=full_name.strip(),
        email=email.strip().lower(),
        naukri_id=naukri_id.strip(),
        naukri_password=naukri_password.strip() if naukri_password else None,
    )
    log_admin_event("admin_user_update", f"Profile updated for user {target_user_id}", user_id=request.state.user_id)
    return {"status": "success"}


@router.post("/users/{target_user_id}/reset-password")
def admin_reset_user_password(target_user_id: int, request: Request, new_password: str = Form(...)):
    if not _is_admin_or_coadmin(request):
        return _deny()
    target = get_user_by_id(target_user_id)
    if not target:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})
    if len(new_password or "") < 6:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Password must be at least 6 characters"})
    update_user_password_hash(target_user_id, hash_password(new_password))
    log_admin_event("admin_password_reset", f"Password reset for user {target_user_id}", user_id=request.state.user_id)
    return {"status": "success"}


@router.post("/users/{target_user_id}/role")
def admin_change_user_role(target_user_id: int, request: Request, role: str = Form(...)):
    if not _is_admin_or_coadmin(request):
        return _deny()
    role = (role or "user").strip().lower()
    if role not in {"admin", "co_admin", "user"}:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid role"})
    actor_role = request.state.role
    target = get_user_by_id(target_user_id)
    if not target:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})
    target_role = (target[4] or "user").strip().lower()
    if actor_role != "admin":
        return _deny("Only admin can change roles")
    if target_role == "admin" and target_user_id != request.state.user_id:
        return _deny("Cannot change another admin role")
    update_user_role(target_user_id, role)
    log_admin_event("admin_role_change", f"User {target_user_id} role -> {role}", user_id=request.state.user_id)
    return {"status": "success"}


@router.post("/users/{target_user_id}/status")
def admin_change_user_status(target_user_id: int, request: Request, account_status: str = Form(...)):
    if not _is_admin_or_coadmin(request):
        return _deny()
    status = (account_status or "active").strip().lower()
    if status not in {"active", "disabled"}:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid account status"})
    target = get_user_by_id(target_user_id)
    if not target:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})
    target_role = (target[4] or "user").strip().lower()
    if request.state.role == "co_admin" and target_role in {"admin", "co_admin"}:
        return _deny("Co-admin cannot disable admin/co-admin")
    update_account_status(target_user_id, status)
    log_admin_event("admin_status_change", f"User {target_user_id} status -> {status}", user_id=request.state.user_id)
    return {"status": "success"}


@router.delete("/users/{target_user_id}")
def admin_delete_user(target_user_id: int, request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()
    target = get_user_by_id(target_user_id)
    if not target:
        return JSONResponse(status_code=404, content={"status": "error", "error": "User not found"})
    target_role = (target[4] or "user").strip().lower()
    if request.state.role == "co_admin":
        return _deny("Co-admin cannot delete users")
    if target_role == "admin":
        return _deny("Cannot delete admin user")
    delete_user(target_user_id)
    log_admin_event("admin_delete_user", f"Deleted user {target_user_id}", user_id=request.state.user_id)
    return {"status": "success"}


@router.get("/users/{target_user_id}/data")
def admin_user_data(target_user_id: int, request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()

    counts = {
        "jobs_directory": _table_count(DATABASE_PATHS["jobs"], ensure_jobs_directory_schema, "jobs_directory", "user_id = ?", (target_user_id,)),
        "relevant_jobs": _table_count(DATABASE_PATHS["relevant"], ensure_relevant_jobs_schema, "relevant_jobs", "user_id = ?", (target_user_id,)),
        "applied_jobs": _table_count(DATABASE_PATHS["applied"], ensure_applied_jobs_schema, "applied_jobs", "user_id = ?", (target_user_id,)),
        "ext_jobs": _table_count(DATABASE_PATHS["ext"], ensure_ext_jobs_schema, "ext_jobs", "user_id = ?", (target_user_id,)),
        "standard_jobs": _table_count(DATABASE_PATHS["standard"], ensure_standard_jobs_schema, "standard_jobs", "user_id = ?", (target_user_id,)),
    }
    try:
        conn = sqlite3.connect(DATABASE_PATHS["settings"])
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM keywords_store WHERE user_id = ?", (target_user_id,))
        counts["keywords"] = int(cur.fetchone()[0] or 0)
        conn.close()
    except Exception:
        counts["keywords"] = 0
    resume_path = Path(f"storage/users/{target_user_id}/resumes/resume.txt")
    resume_exists = resume_path.exists()
    return {
        "counts": counts,
        "settings": get_settings(user_id=target_user_id),
        "resume_exists": resume_exists,
        "resume_path": str(resume_path),
    }


@router.post("/users/{target_user_id}/settings")
def admin_update_user_settings(
    target_user_id: int,
    request: Request,
    job_role: str = Form(""),
    preferred_location: str = Form(""),
    experience: str = Form(""),
    salary: str = Form(""),
    keywords: str = Form(""),
    scan_mode: str = Form("basic"),
    pages_to_scrape: int = Form(5),
    auto_apply_limit: int = Form(10),
):
    if not _is_admin_or_coadmin(request):
        return _deny()
    save_settings(
        data={
            "job_role": job_role,
            "preferred_location": preferred_location,
            "experience": experience,
            "salary": salary,
            "keywords": keywords,
            "scan_mode": scan_mode,
            "pages_to_scrape": pages_to_scrape,
            "auto_apply_limit": auto_apply_limit,
        },
        user_id=target_user_id,
    )
    log_admin_event("admin_user_settings_update", f"Settings updated for user {target_user_id}", user_id=request.state.user_id)
    return {"status": "success"}


@router.delete("/users/{target_user_id}/data/{bucket}")
def admin_delete_user_data(target_user_id: int, bucket: str, request: Request):
    if not _is_admin_or_coadmin(request):
        return _deny()
    mapping = {
        "jobs_directory": (DATABASE_PATHS["jobs"], ensure_jobs_directory_schema),
        "relevant_jobs": (DATABASE_PATHS["relevant"], ensure_relevant_jobs_schema),
        "applied_jobs": (DATABASE_PATHS["applied"], ensure_applied_jobs_schema),
        "ext_jobs": (DATABASE_PATHS["ext"], ensure_ext_jobs_schema),
        "standard_jobs": (DATABASE_PATHS["standard"], ensure_standard_jobs_schema),
    }
    if bucket == "resume_file":
        resume_path = Path(f"storage/users/{target_user_id}/resumes/resume.txt")
        if resume_path.exists():
            os.remove(resume_path)
        return {"status": "success", "deleted": 1}
    if bucket == "keywords":
        conn = sqlite3.connect(DATABASE_PATHS["settings"])
        cur = conn.cursor()
        cur.execute("DELETE FROM keywords_store WHERE user_id = ?", (target_user_id,))
        deleted = int(cur.rowcount or 0)
        conn.commit()
        conn.close()
        log_admin_event("admin_data_delete", f"Deleted {deleted} keywords for user {target_user_id}", user_id=request.state.user_id)
        return {"status": "success", "deleted": deleted}
    pair = mapping.get(bucket)
    if not pair:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid data bucket"})
    db_path, ensure_fn = pair
    conn = sqlite3.connect(db_path)
    ensure_fn(conn)
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {bucket} WHERE user_id = ?", (target_user_id,))
    deleted = int(cur.rowcount or 0)
    conn.commit()
    conn.close()
    log_admin_event("admin_data_delete", f"Deleted {deleted} from {bucket} for user {target_user_id}", user_id=request.state.user_id)
    return {"status": "success", "deleted": deleted}


@router.get("/users/{target_user_id}/records/{bucket}")
def admin_list_user_records(target_user_id: int, bucket: str, request: Request, limit: int = 100):
    if not _is_admin_or_coadmin(request):
        return _deny()
    limit = max(1, min(500, int(limit)))
    if bucket == "keywords":
        conn = sqlite3.connect(DATABASE_PATHS["settings"])
        cur = conn.cursor()
        cur.execute("SELECT keyword, created_at FROM keywords_store WHERE user_id = ? ORDER BY id DESC LIMIT ?", (target_user_id, limit))
        rows = cur.fetchall()
        conn.close()
        return [{"keyword": r[0], "created_at": r[1]} for r in rows]

    mapping = {
        "jobs_directory": (DATABASE_PATHS["jobs"], ensure_jobs_directory_schema),
        "relevant_jobs": (DATABASE_PATHS["relevant"], ensure_relevant_jobs_schema),
        "applied_jobs": (DATABASE_PATHS["applied"], ensure_applied_jobs_schema),
        "ext_jobs": (DATABASE_PATHS["ext"], ensure_ext_jobs_schema),
        "standard_jobs": (DATABASE_PATHS["standard"], ensure_standard_jobs_schema),
    }
    pair = mapping.get(bucket)
    if not pair:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Invalid records bucket"})
    db_path, ensure_fn = pair
    conn = sqlite3.connect(db_path)
    ensure_fn(conn)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {bucket} WHERE user_id = ? ORDER BY id DESC LIMIT ?", (target_user_id, limit))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@router.get("/settings")
def admin_settings_get(request: Request):
    if not _is_admin(request):
        return _deny("Only admin can access system settings")
    conn = sqlite3.connect(DATABASE_PATHS["settings"])
    ensure_admin_settings_schema(conn)
    conn.close()
    return get_admin_settings()


@router.post("/settings")
def admin_settings_save(request: Request, setting_key: str = Form(...), setting_value: str = Form("")):
    if not _is_admin(request):
        return _deny("Only admin can update system settings")
    save_admin_setting(setting_key.strip(), setting_value)
    log_admin_event("admin_setting_update", f"{setting_key} updated", user_id=request.state.user_id)
    return {"status": "success"}


@router.get("/logs")
def admin_logs(request: Request, limit: int = 200):
    if not _is_admin_or_coadmin(request):
        return _deny()
    rows = list_admin_logs(limit=max(1, min(1000, int(limit))))
    return [
        {"id": r[0], "user_id": r[1], "event_type": r[2], "details": r[3], "level": r[4], "created_at": r[5]}
        for r in rows
    ]
