"""
Central configuration — loads server/.env and exposes settings to the app.

Import from anywhere: `from app.config import settings`
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# server/ directory (parent of app/)
SERVER_ROOT = Path(__file__).resolve().parent.parent

# Read server/.env into os.environ (must run before we read variables below)
load_dotenv(SERVER_ROOT / ".env")

VALID_LLM_MODES = frozenset({"local", "cloud"})


def _resolve_cloud_api_key() -> str | None:
    """OLLAMA_CLOUD_API_KEY (project) or OLLAMA_API_KEY (official Ollama docs)."""
    return os.getenv("OLLAMA_CLOUD_API_KEY") or os.getenv("OLLAMA_API_KEY") or None


def _resolve_llm_mode() -> str:
    mode = os.getenv("OLLAMA_LLM_MODE", "local").strip().lower()
    if mode not in VALID_LLM_MODES:
        raise ValueError(
            f"OLLAMA_LLM_MODE must be one of {sorted(VALID_LLM_MODES)}, got {mode!r}"
        )
    return mode


@dataclass(frozen=True)
class Settings:
    """App-wide settings — one object so we don't scatter os.getenv calls."""

    database_url: str
    # Embeddings always use local Ollama (POST /api/embed) — no cloud path.
    ollama_base_url: str
    ollama_embed_model: str
    # Chat LLM: local Ollama or ollama.com cloud API (see app.llm.ollama_client).
    ollama_llm_mode: str
    ollama_local_chat_model: str
    ollama_cloud_chat_model: str
    ollama_cloud_base_url: str
    ollama_cloud_api_key: str | None
    session_secret: str
    session_max_age_days: int
    cookie_secure: bool
    uploads_dir: Path
    max_upload_bytes: int
    max_pdf_pages: int
    login_max_attempts: int
    login_rate_window_seconds: int


settings = Settings(
    database_url=os.environ["DATABASE_URL"],
    ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma:latest"),
    ollama_llm_mode=_resolve_llm_mode(),
    ollama_local_chat_model=os.getenv("OLLAMA_LOCAL_CHAT_MODEL")
    or os.getenv("OLLAMA_CHAT_MODEL", "gemma4"),
    ollama_cloud_chat_model=os.getenv("OLLAMA_CLOUD_CHAT_MODEL", "gemma4:31b"),
    ollama_cloud_base_url=os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com"),
    ollama_cloud_api_key=_resolve_cloud_api_key(),
    session_secret=os.getenv("SESSION_SECRET", "dev-insecure-change-me"),
    session_max_age_days=int(os.getenv("SESSION_MAX_AGE_DAYS", "7")),
    cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    uploads_dir=SERVER_ROOT / "data" / "uploads",
    max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024))),
    max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "200")),
    login_max_attempts=int(os.getenv("LOGIN_MAX_ATTEMPTS", "5")),
    login_rate_window_seconds=int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "300")),
)
