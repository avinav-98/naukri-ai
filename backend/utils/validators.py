import re

def validate_email(email: str) -> bool:

    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"

    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:

    if len(password) < 6:
        return False

    return True