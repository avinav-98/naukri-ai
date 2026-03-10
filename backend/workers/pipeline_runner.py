from backend.models.pipeline_run_model import update_run
from backend.services.automation_pipeline_service import execute_fetch_rank_apply_pipeline


def run_pipeline_task(
    run_id: int,
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    scan_mode: str | None,
    shortlist_limit: int,
):
    update_run(run_id=run_id, status="running", message="Pipeline started")
    try:
        counts = execute_fetch_rank_apply_pipeline(
            user_id=user_id,
            resume_text=resume_text,
            pages=pages,
            auto_apply_limit=auto_apply_limit,
            scan_mode=scan_mode,
            shortlist_limit=shortlist_limit,
        )
    except Exception as exc:
        update_run(run_id=run_id, status="failed", message=str(exc))
        raise

    update_run(
        run_id=run_id,
        status="completed",
        message=(
            f"Fetch + rank + apply completed (query: {counts['search_query']}; "
            f"companies: {', '.join(counts.get('top_companies', [])) or 'N/A'}; "
            f"fetch_filtered: {counts.get('fetch_filtered_count', 0)}; "
            f"applied: {counts.get('apply_summary', {}).get('applied_count', 0)}, "
            f"external: {counts.get('apply_summary', {}).get('external_count', 0)}, "
            f"skipped: {counts.get('apply_summary', {}).get('skipped_count', 0)}, "
            f"failed: {counts.get('apply_summary', {}).get('failed_count', 0)}, "
            f"filtered_out: {counts.get('apply_summary', {}).get('filtered_out_count', 0)})"
        ),
        fetched_count=counts["fetched_count"],
        shortlisted_count=counts["shortlisted_count"],
        applied_count=counts["applied_count"],
    )
