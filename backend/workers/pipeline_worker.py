from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from backend.models.pipeline_run_model import start_run, update_run
from backend.services.automation_pipeline_service import execute_fetch_rank_apply_pipeline


# Keep single worker for browser automation stability.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline-worker")
_lock = Lock()
_active_futures = {}


def _cleanup_future(run_id):
    with _lock:
        _active_futures.pop(run_id, None)


def _run_pipeline_task(run_id, user_id, resume_text, pages, auto_apply_limit, shortlist_limit):
    try:
        update_run(run_id=run_id, status="running", message="Pipeline started")
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
    except Exception as exc:
        update_run(run_id=run_id, status="failed", message=str(exc))


def enqueue_fetch_rank_apply(
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
        status="queued",
        message="Queued for execution",
    )

    future = _executor.submit(
        _run_pipeline_task,
        run_id,
        user_id,
        resume_text,
        pages,
        auto_apply_limit,
        shortlist_limit,
    )
    future.add_done_callback(lambda _f: _cleanup_future(run_id))

    with _lock:
        _active_futures[run_id] = future

    return run_id
