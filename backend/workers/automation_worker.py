import sqlite3
from backend.services.apply_service import auto_apply


def get_all_users():

    conn = sqlite3.connect("database/users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users")

    users = cursor.fetchall()

    conn.close()

    return [u[0] for u in users]


def run_worker():

    users = get_all_users()

    for user_id in users:

        print(f"\nRunning automation for user {user_id}")

        resume_path = f"storage/users/{user_id}/resumes/resume.txt"

        auto_apply(
            user_id=user_id,
            resume_path=resume_path,
            limit=5
        )
