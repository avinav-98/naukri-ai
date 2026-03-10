from pathlib import Path

from backend.ai_engine.resume_parser import infer_search_query, load_resume_text
from backend.models.pipeline_run_model import start_run, update_run
from backend.models.settings_model import get_settings, save_keywords
from backend.models.user_model import get_naukri_credentials
from backend.naukri.naukri_login import login_with_credentials
from backend.services.apply_service import auto_apply
from backend.services.fetch_jobs_service import fetch_jobs_with_details, get_top_companies
from backend.services.job_ranking_service import rank_and_store_jobs


def ensure_user_resume(user_id: int, resume_text: str):
    resume_dir = Path(f"storage/users/{user_id}/resumes")
    resume_dir.mkdir(parents=True, exist_ok=True)
    resume_path = resume_dir / "resume.txt"
    resume_path.write_text(resume_text, encoding="utf-8")
    return str(resume_path)


def get_user_resume_path(user_id: int) -> Path:
    return Path(f"storage/users/{user_id}/resumes/resume.txt")


def has_user_resume(user_id: int) -> bool:
    return get_user_resume_path(user_id).exists()


def load_user_resume_text(user_id: int) -> str:
    resume_path = get_user_resume_path(user_id)
    if not resume_path.exists():
        legacy_path = Path(f"storage/users/{user_id}/resumes/my_resume.txt")
        if legacy_path.exists():
            resume_path = legacy_path

    if not resume_path.exists():
        raise FileNotFoundError("Resume file not found. Upload resume.txt in Control Panel first.")

    resume_text = resume_path.read_text(encoding="utf-8", errors="ignore").strip()
    if not resume_text:
        raise ValueError("Saved resume.txt is empty. Re-upload a valid resume file in Control Panel.")
    return resume_text


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
    scan_mode: str | None = None,
    shortlist_limit: int = 20,
):
    resume_path = ensure_user_resume(user_id, resume_text)
    settings = get_settings(user_id=user_id)
    if scan_mode:
        settings["scan_mode"] = scan_mode
    keywords = settings.get("keywords", "") or ""
    save_keywords(user_id=user_id, raw_keywords=keywords)
    configured_role = (settings.get("job_role") or "").strip()
    search_query = configured_role if configured_role else infer_search_query(resume_text)
    fetch_stats = fetch_jobs_with_details(
        pages=pages,
        user_id=user_id,
        search_query=search_query,
        clear_existing=False,
        filter_settings=settings,
        resume_text=resume_text,
        keywords=keywords,
    )
    fetched_count = int(fetch_stats.get("added_count", 0))
    fetch_filtered_count = int(fetch_stats.get("filtered_out_count", 0))
    top_companies = get_top_companies(user_id=user_id, limit=3)

    parsed_resume_text = load_resume_text(resume_path)
    shortlisted_count = rank_and_store_jobs(
        user_id=user_id,
        resume_text=parsed_resume_text,
        shortlist_limit=shortlist_limit,
        settings=settings,
    )

    apply_summary = auto_apply(
        user_id=user_id,
        resume_path=resume_path,
        limit=auto_apply_limit,
        settings=settings,
    )
    applied_count = int(apply_summary.get("applied_count", 0))

    return {
        "search_query": search_query,
        "top_companies": top_companies,
        "fetched_count": fetched_count,
        "fetch_filtered_count": fetch_filtered_count,
        "shortlisted_count": shortlisted_count,
        "applied_count": applied_count,
        "apply_summary": apply_summary,
    }


def run_fetch_rank_apply_pipeline(
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    scan_mode: str | None = None,
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
            scan_mode=scan_mode,
            shortlist_limit=shortlist_limit,
        )
        update_run(
            run_id=run_id,
            status="completed",
            message=(
                f"Fetch + rank + apply completed (query: {counts['search_query']}; "
                f"companies: {', '.join(counts.get('top_companies', [])) or 'N/A'}; "
                f"fetch_filtered: {counts.get('fetch_filtered_count', 0)}; "
                f"applied: {counts.get('apply_summary', {}).get('applied_count', 0)}, "
                f"skipped: {counts.get('apply_summary', {}).get('skipped_count', 0)}, "
                f"failed: {counts.get('apply_summary', {}).get('failed_count', 0)}, "
                f"filtered_out: {counts.get('apply_summary', {}).get('filtered_out_count', 0)})"
            ),
            fetched_count=counts["fetched_count"],
            shortlisted_count=counts["shortlisted_count"],
            applied_count=counts["applied_count"],
        )
        return {"run_id": run_id, "status": "completed", **counts}
    except Exception as exc:
        update_run(run_id=run_id, status="failed", message=str(exc))
        return {"run_id": run_id, "status": "failed", "error": str(exc)}
