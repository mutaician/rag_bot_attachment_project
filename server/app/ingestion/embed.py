"""
Call Ollama to turn text into embedding vectors.

Uses POST /api/embed (current Ollama API).
Legacy /api/embeddings is removed in recent Ollama versions.
"""

import httpx

from app.config import settings

# embeddinggemma outputs 768-dimensional vectors (must match init.sql vector(768))
EMBEDDING_DIMENSION = 768


def _embed_url() -> str:
    return f"{settings.ollama_base_url.rstrip('/')}/api/embed"


def _embed_payload(text: str) -> dict:
    return {
        "model": settings.ollama_embed_model,
        "input": text,
    }


def _parse_embed_response(data: dict) -> list[float]:
    """Extract one vector from Ollama's batched embed response."""
    # Response shape: {"embeddings": [[0.1, 0.2, ...]], ...}
    embeddings = data.get("embeddings")
    if not embeddings or not embeddings[0]:
        raise RuntimeError(f"Ollama returned no embedding: {data}")

    vector = embeddings[0]
    if len(vector) != EMBEDDING_DIMENSION:
        raise RuntimeError(
            f"Expected {EMBEDDING_DIMENSION} dims, got {len(vector)}. "
            "Update EMBEDDING_DIMENSION and init.sql vector(N)."
        )
    return vector


def _raise_for_ollama_error(response: httpx.Response) -> None:
    """Turn Ollama JSON errors into readable messages."""
    if response.is_success:
        return
    try:
        detail = response.json().get("error", response.text)
    except Exception:
        detail = response.text
    raise RuntimeError(
        f"Ollama embed failed ({response.status_code}): {detail}. "
        f"Is the model pulled? Try: ollama pull {settings.ollama_embed_model}"
    )


async def embed_text(text: str) -> list[float]:
    """Request a single embedding from the local Ollama server."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(_embed_url(), json=_embed_payload(text))
        _raise_for_ollama_error(response)
        return _parse_embed_response(response.json())


def embed_text_sync(text: str) -> list[float]:
    """Sync wrapper for the worker process (no async event loop needed)."""
    with httpx.Client(timeout=120.0) as client:
        response = client.post(_embed_url(), json=_embed_payload(text))
        _raise_for_ollama_error(response)
        return _parse_embed_response(response.json())
