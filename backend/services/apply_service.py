from backend.ai_engine.resume_parser import load_resume_text
from backend.ai_engine.ranking_engine import rank_jobs
from backend.naukri.apply_jobs import apply_to_job


def auto_apply(user_id, resume_path, limit=5, settings=None):

    resume_text = load_resume_text(resume_path)

    ranked_jobs = rank_jobs(resume_text, user_id=user_id, limit=limit, settings=settings)

    count = 0
    summary = {
        "applied_count": 0,
        "skipped_count": 0,
        "failed_count": 0,
        "filtered_out_count": 0,
        "processed_count": 0,
    }

    for score, job in ranked_jobs:

        job_title = job["job_title"]
        company = job["company"]
        location = job["location"]
        job_url = job["job_url"]

        result = apply_to_job(
            user_id,
            job_title,
            company,
            location,
            job.get("experience", ""),
            job_url
        )

        status = (result or {}).get("status", "failed")
        if status == "applied":
            summary["applied_count"] += 1
        elif status == "skipped":
            summary["skipped_count"] += 1
        elif status == "filtered_out":
            summary["filtered_out_count"] += 1
        else:
            summary["failed_count"] += 1

        summary["processed_count"] += 1
        count += 1

        if count >= limit:
            break

    print("Auto apply completed for user:", user_id)
    return summary
