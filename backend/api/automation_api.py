from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from backend.models.pipeline_run_model import get_latest_runs, get_run_by_id
from backend.services.automation_pipeline_service import (
    link_naukri_profile,
)
from backend.workers.pipeline_worker import enqueue_fetch_rank_apply

router = APIRouter(prefix="/api")


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
async def fetch_rank_apply(
    request: Request,
    resume_file: UploadFile = File(...),
    pages: int = Form(5),
    auto_apply_limit: int = Form(10),
):
    user_id = request.state.user_id
    content = await resume_file.read()
    if not content:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Resume file is empty"})

    resume_text = content.decode("utf-8", errors="ignore").strip()
    if not resume_text:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Resume text could not be parsed"})

    run_id = enqueue_fetch_rank_apply(
        user_id=user_id,
        resume_text=resume_text,
        pages=max(1, min(20, pages)),
        auto_apply_limit=max(1, min(20, auto_apply_limit)),
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
