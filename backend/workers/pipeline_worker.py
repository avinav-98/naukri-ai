import os
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from backend.models.pipeline_run_model import start_run, update_run
from backend.workers.pipeline_runner import run_pipeline_task


# Keep single local worker for Playwright stability when in-process fallback is used.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pipeline-worker")
_lock = Lock()
_active_futures = {}
PIPELINE_EXECUTOR = os.getenv("PIPELINE_EXECUTOR", "celery").strip().lower()
PIPELINE_FALLBACK_ON_FAILURE = os.getenv("PIPELINE_FALLBACK_ON_FAILURE", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "y",
}


def _cleanup_future(run_id):
    with _lock:
        _active_futures.pop(run_id, None)


def _enqueue_inprocess(run_id, user_id, resume_text, pages, auto_apply_limit, scan_mode, shortlist_limit):
    future = _executor.submit(
        run_pipeline_task,
        run_id,
        user_id,
        resume_text,
        pages,
        auto_apply_limit,
        scan_mode,
        shortlist_limit,
    )
    future.add_done_callback(lambda _f: _cleanup_future(run_id))
    with _lock:
        _active_futures[run_id] = future


def _enqueue_celery(run_id, user_id, resume_text, pages, auto_apply_limit, scan_mode, shortlist_limit):
    from backend.workers.pipeline_tasks import fetch_rank_apply_task

    task = fetch_rank_apply_task.delay(
        run_id=run_id,
        user_id=user_id,
        resume_text=resume_text,
        pages=pages,
        auto_apply_limit=auto_apply_limit,
        scan_mode=scan_mode,
        shortlist_limit=shortlist_limit,
    )
    update_run(
        run_id=run_id,
        status="queued",
        message="Queued in Celery",
        celery_task_id=task.id,
    )


def enqueue_fetch_rank_apply(
    user_id: int,
    resume_text: str,
    pages: int,
    auto_apply_limit: int,
    scan_mode: str = "basic",
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

    if PIPELINE_EXECUTOR == "celery":
        try:
            _enqueue_celery(
                run_id=run_id,
                user_id=user_id,
                resume_text=resume_text,
                pages=pages,
                auto_apply_limit=auto_apply_limit,
                scan_mode=scan_mode,
                shortlist_limit=shortlist_limit,
            )
            return run_id
        except Exception as exc:
            if PIPELINE_FALLBACK_ON_FAILURE:
                update_run(
                    run_id=run_id,
                    status="queued",
                    message=f"Celery unavailable ({exc}). Running in local worker.",
                )
                _enqueue_inprocess(
                    run_id=run_id,
                    user_id=user_id,
                    resume_text=resume_text,
                    pages=pages,
                    auto_apply_limit=auto_apply_limit,
                    scan_mode=scan_mode,
                    shortlist_limit=shortlist_limit,
                )
                return run_id

            update_run(
                run_id=run_id,
                status="failed",
                message=f"Failed to enqueue Celery task: {exc}",
            )
            raise RuntimeError(
                "Celery/Redis unavailable. Start Redis and Celery worker, or set PIPELINE_EXECUTOR=inprocess."
            ) from exc

    if PIPELINE_EXECUTOR != "inprocess":
        update_run(
            run_id=run_id,
            status="failed",
            message=f"Invalid PIPELINE_EXECUTOR value: {PIPELINE_EXECUTOR}",
        )
        raise ValueError(f"Unsupported PIPELINE_EXECUTOR: {PIPELINE_EXECUTOR}")

    _enqueue_inprocess(
        run_id=run_id,
        user_id=user_id,
        resume_text=resume_text,
        pages=pages,
        auto_apply_limit=auto_apply_limit,
        scan_mode=scan_mode,
        shortlist_limit=shortlist_limit,
    )
    return run_id
