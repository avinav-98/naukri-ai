from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from backend.models.settings_model import get_settings, save_settings
from backend.models.ui_preferences_model import get_ui_preferences, save_ui_preferences
from backend.services.automation_pipeline_service import ensure_user_resume, has_user_resume

router = APIRouter(prefix="/api")


@router.post("/settings")
async def update_settings(
    request: Request,
    job_role: str = Form(""),
    preferred_location: str = Form(""),
    experience: str = Form(""),
    salary: str = Form(""),
    keywords: str = Form(""),
    scan_mode: str = Form("basic"),
    pages_to_scrape: int = Form(5),
    auto_apply_limit: int = Form(10),
    max_job_age_days: int = Form(10),
    resume_file: UploadFile | None = File(default=None),
):
    user_id = request.state.user_id
    has_existing_resume = has_user_resume(user_id)

    if (resume_file is None or not resume_file.filename) and not has_existing_resume:
        return JSONResponse(status_code=400, content={"status": "error", "error": "Resume upload is mandatory before saving settings"})

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
            "max_job_age_days": max_job_age_days,
        },
        user_id=user_id,
    )

    if resume_file is not None and resume_file.filename:
        filename = resume_file.filename.lower()
        if not filename.endswith(".txt"):
            return JSONResponse(status_code=400, content={"status": "error", "error": "Only .txt resume files are allowed"})

        content = await resume_file.read()
        resume_text = content.decode("utf-8", errors="ignore").strip()
        if not resume_text:
            return JSONResponse(status_code=400, content={"status": "error", "error": "Uploaded resume file is empty"})
        ensure_user_resume(user_id=user_id, resume_text=resume_text)

    return {"status": "saved", "has_resume": has_user_resume(user_id)}


@router.get("/settings")
def read_settings(request: Request):
    user_id = request.state.user_id
    data = get_settings(user_id=user_id)
    data["has_resume"] = has_user_resume(user_id)
    return data


@router.get("/ui-preferences")
def read_ui_preferences(request: Request):
    user_id = request.state.user_id
    return get_ui_preferences(user_id=user_id)


@router.post("/ui-preferences")
def update_ui_preferences(
    request: Request,
    theme_mode: str = Form("system"),
    layout_mode: str = Form("standard"),
    accent_color: str = Form("#0b57d0"),
):
    user_id = request.state.user_id
    save_ui_preferences(user_id=user_id, theme_mode=theme_mode, layout_mode=layout_mode, accent_color=accent_color)
    return {"status": "saved"}
