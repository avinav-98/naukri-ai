import os
from pathlib import Path


BASE_STORAGE = Path("storage/users")


def create_user_workspace(user_id):

    user_dir = BASE_STORAGE / str(user_id)

    session_dir = user_dir / "session"
    db_dir = user_dir / "databases"
    resume_dir = user_dir / "resumes"

    session_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)
    resume_dir.mkdir(parents=True, exist_ok=True)

    return {
        "base": user_dir,
        "session": session_dir,
        "databases": db_dir,
        "resumes": resume_dir
    }