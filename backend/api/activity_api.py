from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter()

LOG_FILE = Path("storage/logs/activity_log.json")


@router.get("/activity")
def get_activity():

    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, "r") as f:
        data = json.load(f)

    # Return latest first
    return data[::-1]