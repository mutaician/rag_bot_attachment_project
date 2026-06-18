"""
Ollama chat client factory (local vs ollama.com cloud).

Embeddings stay on localhost — see app.ingestion.embed.

Cloud setup per https://docs.ollama.com/cloud:
  host=https://ollama.com, Authorization: Bearer <OLLAMA_API_KEY>
"""

import logging

from ollama import Client

from app.config import settings

logger = logging.getLogger(__name__)


def get_chat_client() -> Client:
    """
    Return an Ollama Client configured for chat (not embeddings).

    - local: OLLAMA_BASE_URL (default http://localhost:11434)
    - cloud: OLLAMA_CLOUD_BASE_URL + Bearer API key
    """
    if settings.ollama_llm_mode == "cloud":
        if not settings.ollama_cloud_api_key:
            raise RuntimeError(
                "OLLAMA_LLM_MODE=cloud requires OLLAMA_CLOUD_API_KEY or OLLAMA_API_KEY"
            )
        return Client(
            host=settings.ollama_cloud_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.ollama_cloud_api_key}",
            },
        )

    return Client(host=settings.ollama_base_url.rstrip("/"))


def get_chat_model() -> str:
    """Model name passed to Client.chat() — OLLAMA_CHAT_MODEL."""
    return settings.ollama_chat_model


def log_llm_config() -> None:
    """Log LLM mode at startup; warn on missing cloud key or embed host."""
    if settings.ollama_llm_mode == "cloud":
        if settings.ollama_cloud_api_key:
            logger.info(
                "Chat LLM: cloud (%s, model=%s)",
                settings.ollama_cloud_base_url,
                settings.ollama_chat_model,
            )
        else:
            logger.warning(
                "OLLAMA_LLM_MODE=cloud but no API key set — chat will fail until "
                "OLLAMA_CLOUD_API_KEY or OLLAMA_API_KEY is configured"
            )
    else:
        logger.info(
            "Chat LLM: local (%s, model=%s)",
            settings.ollama_base_url,
            settings.ollama_chat_model,
        )

    logger.info(
        "Embeddings: local only (%s, model=%s)",
        settings.ollama_base_url,
        settings.ollama_embed_model,
    )
