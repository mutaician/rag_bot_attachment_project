"""System settings — per-deployment LLM mode and capability probes."""

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.auth.deps import CurrentUser, get_current_user
from app.config import settings
from app.llm import runtime
from app.schemas import LlmModeRequest, LlmModeResponse, SystemCapabilities

router = APIRouter(prefix="/system", tags=["system"], dependencies=[Depends(get_current_user)])


def _probe_url(url: str, headers: dict[str, str] | None = None) -> bool:
    try:
        with httpx.Client(timeout=5.0) as client:
            res = client.get(url, headers=headers)
            return res.is_success
    except httpx.HTTPError:
        return False


@router.get("/capabilities", response_model=SystemCapabilities)
def capabilities() -> SystemCapabilities:
    """Probe embedding and chat backends available to this deployment."""
    embed_ok = _probe_url(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
    local_chat_ok = embed_ok

    cloud_configured = bool(settings.ollama_cloud_api_key)
    cloud_chat_ok = False
    if cloud_configured:
        cloud_chat_ok = _probe_url(
            f"{settings.ollama_cloud_base_url.rstrip('/')}/api/tags",
            headers={"Authorization": f"Bearer {settings.ollama_cloud_api_key}"},
        )

    return SystemCapabilities(
        embed=embed_ok,
        local_chat=local_chat_ok,
        cloud_chat=cloud_chat_ok,
        cloud_configured=cloud_configured,
    )


@router.get("/llm", response_model=LlmModeResponse)
def get_llm_mode() -> LlmModeResponse:
    """Current chat LLM mode for this deployment (local or cloud)."""
    return LlmModeResponse(mode=runtime.get_llm_mode())


@router.put("/llm", response_model=LlmModeResponse)
def set_llm_mode(
    body: LlmModeRequest,
    _user: CurrentUser = Depends(get_current_user),
) -> LlmModeResponse:
    """Switch chat LLM mode for all users on this deployment."""
    if body.mode == "cloud" and not settings.ollama_cloud_api_key:
        raise HTTPException(
            status_code=400,
            detail="Cloud mode requires OLLAMA_CLOUD_API_KEY or OLLAMA_API_KEY",
        )
    return LlmModeResponse(mode=runtime.set_llm_mode(body.mode))
