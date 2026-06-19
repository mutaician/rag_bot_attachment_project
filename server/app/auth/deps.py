"""FastAPI auth dependencies."""

from dataclasses import dataclass

from fastapi import Cookie, HTTPException, status

from app import db
from app.auth.sessions import COOKIE_NAME, hash_token


@dataclass(frozen=True)
class CurrentUser:
    id: str
    username: str
    display_name: str


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> CurrentUser:
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    user = db.get_user_by_session_hash(hash_token(session_token))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return CurrentUser(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
    )
