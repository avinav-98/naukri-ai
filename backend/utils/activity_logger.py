import json
from datetime import datetime
from pathlib import Path

from backend.models.admin_log_model import log_admin_event

LOG_FILE = Path("storage/logs/activity_log.json")

def log_activity(event, details="", user_id=None, level="info"):

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "details": details
    }

    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            data = json.load(f)
    else:
        data = []

    data.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data[-50:], f, indent=2)
    try:
        log_admin_event(event_type=event, details=str(details), user_id=user_id, level=level)
    except Exception:
        pass
