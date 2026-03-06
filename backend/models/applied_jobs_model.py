import sqlite3
from backend.config import DATABASE_PATHS


def get_applied_jobs():

    conn = sqlite3.connect(DATABASE_PATHS["applied"])

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM applied_jobs")

    jobs = cursor.fetchall()

    conn.close()

    return jobs