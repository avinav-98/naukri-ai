from pathlib import Path

from backend.ai_engine.resume_parser import infer_search_query, load_resume_text
from backend.models.pipeline_run_model import start_run, update_run
from backend.models.settings_model import get_settings
from backend.models.user_model import get_naukri_credentials
from backend.naukri.naukri_login import login_with_credentials
from backend.services.apply_service import auto_apply
from backend.services.fetch_jobs_service import fetch_jobs
from backend.services.job_ranking_service import rank_and_store_jobs


def ensure_user_resume(user_id: int, resume_text: str):
    resume_dir = Path(f"storage/users/{user_id}/resumes")
    resume_dir.mkdir(parents=True, exist_ok=True)
    resume_path = resume_dir / "my_resume.txt"
    resume_path.write_text(resume_text, encoding="utf-8")
    return str(resume_path)


def link_naukri_profile(user_id: int):
    creds = get_naukri_credentials(user_id)
    if not creds:
        return False, "Naukri credentials are missing for this account"

    return login_with_credentials(
        user_id=user_id,
        naukri_id=creds["naukri_id"],
        naukri_password=creds["naukri_password"],
    )


def execute_fetch_rank_apply_pipeline(
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    shortlist_limit: int = 20,
):
    resume_path = ensure_user_resume(user_id, resume_text)
    settings = get_settings(user_id=user_id)
    configured_role = (settings.get("job_role") or "").strip()
    search_query = configured_role if configured_role else infer_search_query(resume_text)
    fetched_count = fetch_jobs(
        pages=pages,
        user_id=user_id,
        search_query=search_query,
        clear_existing=True,
    )

    parsed_resume_text = load_resume_text(resume_path)
    shortlisted_count = rank_and_store_jobs(
        user_id=user_id,
        resume_text=parsed_resume_text,
        shortlist_limit=shortlist_limit,
    )

    applied_count = auto_apply(
        user_id=user_id,
        resume_path=resume_path,
        limit=auto_apply_limit,
    )

    return {
        "search_query": search_query,
        "fetched_count": fetched_count,
        "shortlisted_count": shortlisted_count,
        "applied_count": applied_count,
    }


def run_fetch_rank_apply_pipeline(
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    shortlist_limit: int = 20,
):
    run_id = start_run(
        user_id=user_id,
        run_type="fetch_rank_apply",
        pages=pages,
        auto_apply_limit=auto_apply_limit,
    )

    try:
        counts = execute_fetch_rank_apply_pipeline(
            user_id=user_id,
            resume_text=resume_text,
            pages=pages,
            auto_apply_limit=auto_apply_limit,
            shortlist_limit=shortlist_limit,
        )
        update_run(
            run_id=run_id,
            status="completed",
            message=f"Fetch + rank + apply completed (query: {counts['search_query']})",
            fetched_count=counts["fetched_count"],
            shortlisted_count=counts["shortlisted_count"],
            applied_count=counts["applied_count"],
        )
        return {"run_id": run_id, "status": "completed", **counts}
    except Exception as exc:
        update_run(run_id=run_id, status="failed", message=str(exc))
        return {"run_id": run_id, "status": "failed", "error": str(exc)}
