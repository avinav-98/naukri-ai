import base64
import hashlib
import os

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    # Derive a deterministic key from env secret for local/dev simplicity.
    secret = os.getenv("NAUKRI_CREDENTIALS_SECRET", "change-this-in-production")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_text(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_text(value: str) -> str:
    return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
