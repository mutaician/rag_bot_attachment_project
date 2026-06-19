"""Session token generation and hashing."""

import hashlib
import secrets


COOKIE_NAME = "session_token"


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
