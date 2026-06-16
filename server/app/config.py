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


@dataclass(frozen=True)
class Settings:
    """App-wide settings — one object so we don't scatter os.getenv calls."""

    database_url: str
    ollama_base_url: str
    ollama_embed_model: str
    uploads_dir: Path


settings = Settings(
    database_url=os.environ["DATABASE_URL"],
    ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    ollama_embed_model=os.getenv("OLLAMA_EMBED_MODEL", "embeddinggemma:latest"),
    uploads_dir=SERVER_ROOT / "data" / "uploads",
)
