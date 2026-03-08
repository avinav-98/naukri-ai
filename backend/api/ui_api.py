import sqlite3
from datetime import datetime
from datetime import timedelta, timezone
from io import StringIO

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from backend.config import DATABASE_PATHS
from backend.models.pipeline_run_model import clear_runs_for_user, get_latest_runs
from backend.models.settings_model import get_keywords, get_settings, save_settings
from backend.services.automation_pipeline_service import (
    ensure_user_resume,
    has_user_resume,
    link_naukri_profile,
    load_user_resume_text,
)
from backend.services.resume_analyzer_service import analyze_resume_matches
from backend.utils.db_migrations import (
    ensure_applied_jobs_schema,
    ensure_ext_jobs_schema,
    ensure_jobs_directory_schema,
    ensure_relevant_jobs_schema,
)
from backend.workers.pipeline_worker import enqueue_fetch_rank_apply


router = APIRouter(prefix="/ui")
templates = Jinja2Templates(directory="frontend/templates")
UTC_PLUS_530 = timezone(timedelta(hours=5, minutes=30))


def _status_payload(message: str, kind: str = "info"):
    return {"message": message, "kind": kind}


def _bounded_int(value, default: int, min_v: int = 1, max_v: int = 20) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_v, min(max_v, parsed))


def _count_rows(db_path, table, user_id):
    conn = sqlite3.connect(db_path)
    if table == "jobs_directory":
        ensure_jobs_directory_schema(conn)
    elif table == "relevant_jobs":
        ensure_relevant_jobs_schema(conn)
    elif table == "applied_jobs":
        ensure_applied_jobs_schema(conn)
    elif table == "ext_jobs":
        ensure_ext_jobs_schema(conn)
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = ?", (user_id,))
    result = cur.fetchone()[0]
    conn.close()
    return result


def _to_utc_plus_530_text(raw_dt):
    if not raw_dt:
        return "-"
    text = str(raw_dt).strip()
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(UTC_PLUS_530).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Fallback for sqlite timestamps like "YYYY-MM-DD HH:MM:SS"
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            return dt.astimezone(UTC_PLUS_530).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return text


@router.get("/dashboard-stats", response_class=HTMLResponse)
def dashboard_stats_fragment(request: Request):
    user_id = request.state.user_id
    try:
        stats = {
            "scraped": _count_rows(DATABASE_PATHS["jobs"], "jobs_directory", user_id),
            "relevant": _count_rows(DATABASE_PATHS["relevant"], "relevant_jobs", user_id),
            "applied": _count_rows(DATABASE_PATHS["applied"], "applied_jobs", user_id),
        }
    except Exception:
        stats = {"scraped": 0, "relevant": 0, "applied": 0}
    return templates.TemplateResponse("partials/dashboard_stats.html", {"request": request, "stats": stats})


@router.get("/jobs-directory-rows", response_class=HTMLResponse)
def jobs_directory_rows(request: Request):
    user_id = request.state.user_id
    rows = []
    try:
        conn = sqlite3.connect(DATABASE_PATHS["jobs"])
        ensure_jobs_directory_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url
            FROM jobs_directory
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        rows = []
    jobs = [{"title": r[0], "company": r[1], "location": r[2], "url": r[3]} for r in rows]
    return templates.TemplateResponse("partials/jobs_directory_rows.html", {"request": request, "jobs": jobs})


@router.get("/relevant-jobs-rows", response_class=HTMLResponse)
def relevant_jobs_rows(request: Request):
    user_id = request.state.user_id
    rows = []
    try:
        conn = sqlite3.connect(DATABASE_PATHS["relevant"])
        ensure_relevant_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url, score
            FROM relevant_jobs
            WHERE user_id = ?
            ORDER BY score DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        rows = []
    jobs = [
        {
            "title": r[0],
            "company": r[1],
            "location": r[2],
            "url": r[3],
            "score": r[4],
        }
        for r in rows
    ]
    return templates.TemplateResponse("partials/relevant_jobs_rows.html", {"request": request, "jobs": jobs})


@router.get("/applied-jobs-rows", response_class=HTMLResponse)
def applied_jobs_rows(request: Request):
    user_id = request.state.user_id
    rows = []
    try:
        conn = sqlite3.connect(DATABASE_PATHS["applied"])
        ensure_applied_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, job_url, applied_at, status
            FROM applied_jobs
            WHERE user_id = ? AND lower(status) = 'applied'
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        rows = []
    jobs = [
        {
            "title": r[0],
            "company": r[1],
            "location": r[2],
            "job_url": r[3],
            "applied_at": _to_utc_plus_530_text(r[4]),
            "status": (r[5] or "applied").title(),
        }
        for r in rows
    ]
    return templates.TemplateResponse("partials/applied_jobs_rows.html", {"request": request, "jobs": jobs})


@router.get("/ext-jobs-rows", response_class=HTMLResponse)
def ext_jobs_rows(request: Request):
    user_id = request.state.user_id
    rows = []
    try:
        conn = sqlite3.connect(DATABASE_PATHS["ext"])
        ensure_ext_jobs_schema(conn)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_title, company, location, experience, job_url, external_apply_url, captured_at
            FROM ext_jobs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT 200
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        conn.close()
    except Exception:
        rows = []
    jobs = [
        {
            "title": r[0],
            "company": r[1],
            "location": r[2],
            "experience": r[3],
            "job_url": r[4],
            "external_apply_url": r[5],
            "captured_at": _to_utc_plus_530_text(r[6]),
        }
        for r in rows
    ]
    return templates.TemplateResponse("partials/ext_jobs_rows.html", {"request": request, "jobs": jobs})


@router.get("/pipeline-runs-rows", response_class=HTMLResponse)
def pipeline_runs_rows(request: Request):
    user_id = request.state.user_id
    rows = get_latest_runs(user_id, limit=20)
    runs = []
    for r in rows:
        dt = r[9] or r[10]
        formatted = _to_utc_plus_530_text(dt)
        runs.append(
            {
                "date": formatted or "-",
                "pages": r[4],
                "apply_limit": r[5],
                "fetched": r[6],
                "shortlisted": r[7],
                "message": f"{r[2]}: {r[3] or '-'}",
            }
        )
    return templates.TemplateResponse("partials/pipeline_runs_rows.html", {"request": request, "runs": runs})


@router.post("/portal-login", response_class=HTMLResponse)
async def portal_login_action(request: Request):
    user_id = request.state.user_id
    try:
        ok, message = await run_in_threadpool(link_naukri_profile, user_id)
    except Exception as exc:
        payload = _status_payload(f"Portal login failed: {exc}", kind="error")
        return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})

    payload = _status_payload(message if ok else "Portal login failed", kind="success" if ok else "error")
    return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})


@router.post("/run-pipeline", response_class=HTMLResponse)
def run_pipeline_action(request: Request, scan_mode: str = Form("basic")):
    user_id = request.state.user_id
    scan_mode = (scan_mode or "basic").strip().lower()
    if scan_mode not in {"basic", "advance", "extreme"}:
        scan_mode = "basic"
    settings = get_settings(user_id=user_id)
    try:
        resume_text = load_user_resume_text(user_id=user_id)
    except Exception as exc:
        payload = _status_payload(str(exc), kind="error")
        return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})

    pages = _bounded_int(settings.get("pages_to_scrape", 5), default=5)
    auto_apply_limit = _bounded_int(settings.get("auto_apply_limit", 10), default=10)
    run_id = enqueue_fetch_rank_apply(
        user_id=user_id,
        resume_text=resume_text,
        pages=pages,
        auto_apply_limit=auto_apply_limit,
        scan_mode=scan_mode,
    )
    payload = _status_payload(f"Run #{run_id} queued. Tracking live updates below.", kind="success")
    return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})


@router.delete("/clear-pipeline-runs", response_class=HTMLResponse)
def clear_pipeline_runs_action(request: Request):
    user_id = request.state.user_id
    deleted = clear_runs_for_user(user_id)
    payload = _status_payload(f"Cleared {deleted} run records.", kind="success")
    return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})


@router.post("/settings-save", response_class=HTMLResponse)
async def settings_save_action(
    request: Request,
    job_role: str = Form(""),
    preferred_location: str = Form(""),
    experience: str = Form(""),
    salary: str = Form(""),
    keywords: str = Form(""),
    scan_mode: str = Form("basic"),
    pages_to_scrape: int = Form(5),
    auto_apply_limit: int = Form(10),
    resume_file: UploadFile | None = File(default=None),
):
    user_id = request.state.user_id
    has_existing_resume = has_user_resume(user_id)
    if (resume_file is None or not resume_file.filename) and not has_existing_resume:
        payload = _status_payload("Resume upload is mandatory before saving settings.", kind="error")
        return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})

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
        user_id=user_id,
    )

    if resume_file is not None and resume_file.filename:
        name = resume_file.filename.lower()
        if not name.endswith(".txt"):
            payload = _status_payload("Only .txt resume files are allowed.", kind="error")
            return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})
        content = await resume_file.read()
        text = content.decode("utf-8", errors="ignore").strip()
        if not text:
            payload = _status_payload("Uploaded resume file is empty.", kind="error")
            return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})
        ensure_user_resume(user_id=user_id, resume_text=text)

    resume_msg = "Resume.txt saved" if has_user_resume(user_id) else "No resume uploaded"
    payload = _status_payload(f"Settings saved. {resume_msg}.", kind="success")
    return templates.TemplateResponse("partials/status_message.html", {"request": request, **payload})


@router.get("/fetch-go-directory", response_class=HTMLResponse)
def fetch_go_directory_button(request: Request):
    user_id = request.state.user_id
    rows = get_latest_runs(user_id=user_id, limit=1)
    show = bool(rows and rows[0][2] == "completed")
    return templates.TemplateResponse("partials/fetch_go_directory.html", {"request": request, "show": show})


@router.get("/resume-analyzer-rows", response_class=HTMLResponse)
def resume_analyzer_rows(request: Request):
    user_id = request.state.user_id
    settings = get_settings(user_id=user_id)
    try:
        resume_text = load_user_resume_text(user_id=user_id)
    except Exception:
        return templates.TemplateResponse("partials/resume_analyzer_rows.html", {"request": request, "rows": []})

    rows = analyze_resume_matches(
        user_id=user_id,
        resume_text=resume_text,
        keywords_raw=settings.get("keywords", ""),
        limit=200,
    )
    return templates.TemplateResponse("partials/resume_analyzer_rows.html", {"request": request, "rows": rows})


@router.get("/keywords-rows", response_class=HTMLResponse)
def keywords_rows(request: Request):
    user_id = request.state.user_id
    keywords = get_keywords(user_id=user_id)
    return templates.TemplateResponse("partials/keywords_rows.html", {"request": request, "keywords": keywords})


@router.get("/keywords-download")
def download_keywords(request: Request):
    user_id = request.state.user_id
    keywords = get_keywords(user_id=user_id)
    out = StringIO()
    for kw in keywords:
        out.write(f"{kw}\n")
    return Response(
        content=out.getvalue(),
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=keywords.txt"},
    )
