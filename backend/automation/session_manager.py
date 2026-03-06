import json
from pathlib import Path


def get_session_file(user_id):

    return Path(f"storage/users/{user_id}/session/naukri_session.json")


def save_session(context, user_id):

    cookies = context.cookies()

    session_file = get_session_file(user_id)

    session_file.parent.mkdir(parents=True, exist_ok=True)

    with open(session_file, "w") as f:
        json.dump(cookies, f, indent=4)

    print(f"Session saved for user {user_id}")


def load_session(context, user_id):

    session_file = get_session_file(user_id)

    if not session_file.exists():

        print("Session not found for user:", user_id)

        return False

    with open(session_file, "r") as f:
        cookies = json.load(f)

    context.add_cookies(cookies)

    print(f"Session loaded for user {user_id}")

    return True