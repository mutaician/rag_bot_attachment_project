"""Runtime LLM mode — one setting per deployment, toggled via /system/llm."""

import threading

from app.config import VALID_LLM_MODES, settings

_lock = threading.Lock()
_mode: str = settings.ollama_llm_mode


def get_llm_mode() -> str:
    with _lock:
        return _mode


def set_llm_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in VALID_LLM_MODES:
        raise ValueError(
            f"mode must be one of {sorted(VALID_LLM_MODES)}, got {mode!r}"
        )
    global _mode
    with _lock:
        _mode = normalized
    return _mode
