import sqlite3
from backend.config import DATABASE_PATHS


def get_all_jobs():

    conn = sqlite3.connect(DATABASE_PATHS["jobs"])

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM jobs_directory")

    jobs = cursor.fetchall()

    conn.close()

    return jobs