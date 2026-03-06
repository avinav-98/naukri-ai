from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_PATHS = {
    "users": BASE_DIR / "database" / "users.db",
    "jobs": BASE_DIR / "database" / "jobs_directory.db",
    "applied": BASE_DIR / "database" / "applied_jobs.db",
    "relevant": BASE_DIR / "database" / "relevant_jobs.db",
    "settings": BASE_DIR / "database" / "settings.db",
    "standard": BASE_DIR / "database" / "standard_jobs.db",
    "runs": BASE_DIR / "database" / "automation_runs.db",
}
