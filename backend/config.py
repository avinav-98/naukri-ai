from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
MAIN_DATABASE_PATH = DATABASE_DIR / "main.db"

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
