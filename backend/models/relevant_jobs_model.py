import sqlite3
from backend.config import DATABASE_PATHS


def get_relevant_jobs():

    conn = sqlite3.connect(DATABASE_PATHS["relevant"])

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM relevant_jobs ORDER BY score DESC")

    jobs = cursor.fetchall()

    conn.close()

    return jobs