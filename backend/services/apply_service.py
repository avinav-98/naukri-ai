from backend.ai_engine.resume_parser import load_resume_text
from backend.ai_engine.ranking_engine import rank_jobs
from backend.naukri.apply_jobs import apply_to_job
from backend.utils.logger import log


def auto_apply(user_id, resume_path, limit=5, settings=None):

    resume_text = load_resume_text(resume_path)

    ranked_jobs = rank_jobs(resume_text, user_id=user_id, limit=limit, settings=settings)

    count = 0
    summary = {
        "applied_count": 0,
        "skipped_count": 0,
        "external_count": 0,
        "failed_count": 0,
        "filtered_out_count": 0,
        "processed_count": 0,
    }

    for score, job in ranked_jobs:

        job_title = job["job_title"]
        company = job["company"]
        location = job["location"]
        job_url = job["job_url"]
        job_id = job.get("job_id")

        try:
            result = apply_to_job(
                user_id,
                job_title,
                company,
                location,
                job.get("experience", ""),
                job_url,
                job_id=job_id,
                resume_match_score=job.get("resume_match_score", 0.0),
            )
        except Exception as exc:
            result = {
                "status": "failed",
                "apply_button_type": "unknown",
                "error_message": str(exc) or "Unhandled exception in apply_to_job",
            }

        status = (result or {}).get("status", "failed")
        if status == "applied":
            summary["applied_count"] += 1
        elif status == "external":
            summary["external_count"] += 1
            summary["skipped_count"] += 1
        elif status == "skipped":
            summary["skipped_count"] += 1
        elif status == "filtered_out":
            summary["filtered_out_count"] += 1
        else:
            summary["failed_count"] += 1

        log(
            "[APPLY_DEBUG] "
            f"job_id={job_id if job_id is not None else '-'} | "
            f"job_title={job_title or '-'} | "
            f"apply_button_type={(result or {}).get('apply_button_type', 'unknown')} | "
            f"apply_result={status} | "
            f"error_message={(result or {}).get('error_message', '-') or '-'}"
        )

        summary["processed_count"] += 1
        count += 1

        if count >= limit:
            break

    print("Auto apply completed for user:", user_id)
    return summary
