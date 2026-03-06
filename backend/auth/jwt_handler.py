import datetime
import os

import jwt


JWT_SECRET = os.getenv("JWT_SECRET", "naukri_auto_apply_secret_min_32_chars_2026")
JWT_ALGO = "HS256"
JWT_EXP_DAYS = int(os.getenv("JWT_EXP_DAYS", "7"))


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except jwt.PyJWTError:
        return None
