from backend.workers.celery_app import celery_app
from backend.workers.pipeline_runner import run_pipeline_task


@celery_app.task(name="pipeline.fetch_rank_apply")
def fetch_rank_apply_task(
    run_id: int,
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    scan_mode: str | None,
    shortlist_limit: int,
):
    run_pipeline_task(
        run_id=run_id,
        user_id=user_id,
        resume_text=resume_text,
        pages=pages,
        auto_apply_limit=auto_apply_limit,
        scan_mode=scan_mode,
        shortlist_limit=shortlist_limit,
    )
