"""Authentication endpoints — login, logout, current user."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app import db
from app.auth.deps import CurrentUser, get_current_user
from app.auth.passwords import verify_password
from app.auth.sessions import COOKIE_NAME, hash_token, new_session_token
from app.config import settings
from app.schemas import AuthUser, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.session_max_age_days)


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.session_max_age_days * 86400,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


@router.post("/login", response_model=AuthUser)
def login(body: LoginRequest, response: Response) -> AuthUser:
    """Authenticate with username/password; sets an HttpOnly session cookie."""
    user = db.get_user_by_username(body.username)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    db.cleanup_expired_sessions()
    token = new_session_token()
    db.create_session(user["id"], hash_token(token), _session_expiry())
    _set_session_cookie(response, token)

    return AuthUser(
        id=user["id"],
        username=user["username"],
        display_name=user["display_name"],
    )


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    session_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> None:
    """End the current session and clear the cookie."""
    if session_token:
        db.delete_session_by_token_hash(hash_token(session_token))
    _clear_session_cookie(response)


@router.get("/me", response_model=AuthUser)
def me(user: CurrentUser = Depends(get_current_user)) -> AuthUser:
    """Return the authenticated user."""
    return AuthUser(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
    )
