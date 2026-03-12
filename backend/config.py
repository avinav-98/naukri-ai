from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
MAIN_DATABASE_PATH = DATABASE_DIR / "main.db"

LEGACY_DATABASE_PATHS = {
    "users": DATABASE_DIR / "users.db",
    "jobs": DATABASE_DIR / "jobs_directory.db",
    "applied": DATABASE_DIR / "applied_jobs.db",
    "relevant": DATABASE_DIR / "relevant_jobs.db",
    "settings": DATABASE_DIR / "settings.db",
    "standard": DATABASE_DIR / "standard_jobs.db",
    "ext": DATABASE_DIR / "ext_jobs.db",
    "runs": DATABASE_DIR / "automation_runs.db",
}

DATABASE_PATHS = {
    "main": MAIN_DATABASE_PATH,
    "users": MAIN_DATABASE_PATH,
    "jobs": MAIN_DATABASE_PATH,
    "applied": MAIN_DATABASE_PATH,
    "relevant": MAIN_DATABASE_PATH,
    "settings": MAIN_DATABASE_PATH,
    "standard": MAIN_DATABASE_PATH,
    "ext": MAIN_DATABASE_PATH,
    "runs": MAIN_DATABASE_PATH,
}
