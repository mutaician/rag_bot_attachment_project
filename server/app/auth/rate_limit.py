"""In-memory login rate limiting (per IP and per username)."""

import time
from threading import Lock

from fastapi import HTTPException, Request, status

from app.config import settings

_lock = Lock()
_attempts: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _prune(key: str, now: float) -> list[float]:
    window_start = now - settings.login_rate_window_seconds
    return [ts for ts in _attempts.get(key, []) if ts >= window_start]


def check_login_allowed(request: Request, username: str) -> None:
    """Raise 429 if IP or username is locked out from too many failures."""
    now = time.time()
    keys = (f"ip:{_client_ip(request)}", f"user:{username.lower()}")

    with _lock:
        for key in keys:
            recent = _prune(key, now)
            _attempts[key] = recent
            if len(recent) >= settings.login_max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many login attempts. Try again later.",
                )


def record_login_failure(request: Request, username: str) -> None:
    now = time.time()
    keys = (f"ip:{_client_ip(request)}", f"user:{username.lower()}")

    with _lock:
        for key in keys:
            recent = _prune(key, now)
            recent.append(now)
            _attempts[key] = recent


def clear_login_failures(request: Request, username: str) -> None:
    keys = (f"ip:{_client_ip(request)}", f"user:{username.lower()}")
    with _lock:
        for key in keys:
            _attempts.pop(key, None)


def reset_all_rate_limits() -> None:
    """Test helper — clear all tracked login failures."""
    with _lock:
        _attempts.clear()
