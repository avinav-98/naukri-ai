from backend.ai_engine.resume_parser import load_resume_text
from backend.ai_engine.ranking_engine import rank_jobs
from backend.naukri.apply_jobs import apply_to_job


def auto_apply(user_id, resume_path, limit=5):

    resume_text = load_resume_text(resume_path)

    ranked_jobs = rank_jobs(resume_text, user_id=user_id, limit=limit)

    count = 0

    for score, job in ranked_jobs:

        job_title, company, location, job_url = job

        apply_to_job(
            user_id,
            job_title,
            company,
            location,
            job_url
        )

        count += 1

        if count >= limit:
            break

    print("Auto apply completed for user:", user_id)
    return count
