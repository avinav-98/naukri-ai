import sqlite3

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from backend.ai_engine.job_matcher import calculate_match_score
from backend.ai_engine.ranking_engine import score_by_mode
from backend.config import DATABASE_PATHS
from backend.models.pipeline_run_model import clear_runs_for_user, get_latest_runs, get_run_by_id
from backend.models.settings_model import get_settings
from backend.services.automation_pipeline_service import (
    link_naukri_profile,
    load_user_resume_text,
)
from backend.utils.db_migrations import ensure_jobs_directory_schema
from backend.utils.job_filters import evaluate_job_filters
from backend.workers.pipeline_worker import enqueue_fetch_rank_apply

router = APIRouter(prefix="/api")


def _bounded_int(value, default: int, min_v: int = 1, max_v: int = 20) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(min_v, min(max_v, parsed))


def _to_run_payload(row):
    return {
        "id": row[0],
        "run_type": row[1],
        "status": row[2],
        "message": row[3],
        "pages": row[4],
        "auto_apply_limit": row[5],
        "fetched_count": row[6],
        "shortlisted_count": row[7],
        "applied_count": row[8],
        "started_at": row[9],
        "finished_at": row[10],
        "celery_task_id": row[11],
    }


@router.post("/portal/login")
async def portal_login(request: Request):
    user_id = request.state.user_id
    try:
        ok, message = await run_in_threadpool(link_naukri_profile, user_id)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": f"Portal login failed: {str(exc)}"},
        )

    if not ok:
        return JSONResponse(status_code=400, content={"status": "error", "error": message})
    return {"status": "success", "message": message}


@router.post("/fetch-jobs")
async def fetch_rank_apply(request: Request):
    user_id = request.state.user_id
    settings = get_settings(user_id=user_id)

    try:
        resume_text = load_user_resume_text(user_id=user_id)
    except Exception as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error": str(exc)})

    pages = _bounded_int(settings.get("pages_to_scrape", 5), default=5)
    auto_apply_limit = _bounded_int(settings.get("auto_apply_limit", 10), default=10)
    scan_mode = (settings.get("scan_mode", "basic") or "basic").strip().lower()

    run_id = enqueue_fetch_rank_apply(
        user_id=user_id,
        resume_text=resume_text,
        pages=pages,
        auto_apply_limit=auto_apply_limit,
        scan_mode=scan_mode,
    )
    return JSONResponse(
        status_code=202,
        content={"status": "success", "run_id": run_id, "run_status": "queued"},
    )


@router.get("/pipeline-runs")
def pipeline_runs(request: Request):
    user_id = request.state.user_id
    rows = get_latest_runs(user_id, limit=20)
    return [_to_run_payload(r) for r in rows]


@router.get("/pipeline-runs/{run_id}")
def pipeline_run_by_id(run_id: int, request: Request):
    user_id = request.state.user_id
    row = get_run_by_id(user_id=user_id, run_id=run_id)
    if not row:
        return JSONResponse(status_code=404, content={"status": "error", "error": "Run not found"})
    return _to_run_payload(row)


@router.delete("/pipeline-runs")
def clear_pipeline_runs(request: Request):
    user_id = request.state.user_id
    deleted_count = clear_runs_for_user(user_id=user_id)
    return {"status": "success", "deleted_count": deleted_count}


@router.get("/debug/pipeline-preview")
def pipeline_preview(request: Request, limit: int = 200):
    user_id = request.state.user_id
    settings = get_settings(user_id=user_id)
    scan_mode = (settings.get("scan_mode", "basic") or "basic").strip().lower()
    if scan_mode not in {"basic", "advance", "extreme"}:
        scan_mode = "basic"
    limit = _bounded_int(limit, default=200, min_v=1, max_v=500)

    try:
        resume_text = load_user_resume_text(user_id=user_id)
    except Exception as exc:
        return JSONResponse(status_code=400, content={"status": "error", "error": str(exc)})

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])
    ensure_jobs_directory_schema(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, job_title, company, location, experience, salary, job_description, resume_match_score, job_url
        FROM jobs_directory
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cur.fetchall()
    conn.close()

    preview_rows = []
    for row in rows:
        job = {
            "id": row[0],
            "title": row[1] or "",
            "company": row[2] or "",
            "location": row[3] or "",
            "experience": row[4] or "",
            "salary": row[5] or "",
            "description": row[6] or "",
            "resume_match_score": float(row[7] or 0.0),
            "job_url": row[8] or "",
        }
        filter_ok, filter_reason = evaluate_job_filters(job, settings)
        semantic_text = (
            f"{job['title']} {job['company']} {job['location']} "
            f"{job['experience']} {job['salary']} {job['description']}"
        )
        semantic_score = round(max(0.0, float(calculate_match_score(resume_text, semantic_text)) * 100.0), 2)
        final_score = round(score_by_mode(semantic_score, job["resume_match_score"], scan_mode), 2)
        preview_rows.append(
            {
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "job_url": job["job_url"],
                "filter_passed": filter_ok,
                "filter_reason": "ok" if filter_ok else filter_reason,
                "semantic_score": semantic_score,
                "resume_match_score": round(job["resume_match_score"], 2),
                "final_score": final_score,
            }
        )

    eligible = [j for j in preview_rows if j["filter_passed"]]
    eligible.sort(key=lambda x: x["final_score"], reverse=True)
    apply_limit = _bounded_int(settings.get("auto_apply_limit", 10), default=10, min_v=1, max_v=50)
    apply_urls = {j["job_url"] for j in eligible[:apply_limit] if j["job_url"]}

    for row in preview_rows:
        row["would_auto_apply"] = row["job_url"] in apply_urls

    return {
        "status": "success",
        "scan_mode": scan_mode,
        "counts": {
            "total_considered": len(preview_rows),
            "eligible_after_filters": len(eligible),
            "would_auto_apply": len([r for r in preview_rows if r["would_auto_apply"]]),
        },
        "settings": {
            "job_role": settings.get("job_role", ""),
            "preferred_location": settings.get("preferred_location", ""),
            "experience": settings.get("experience", ""),
            "salary": settings.get("salary", ""),
            "auto_apply_limit": apply_limit,
        },
        "jobs": preview_rows,
    }
