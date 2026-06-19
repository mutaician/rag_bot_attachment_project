"""
Chat endpoint — agentic RAG with SSE streaming (Milestone 3).
"""

import json
import logging
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app import db
from app.auth.deps import CurrentUser, get_current_user
from app.rag.agent import run_agent_stream
from app.schemas import ChatRequest, Citation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)],
)


def _parse_conversation_id(conversation_id: str) -> str:
    try:
        return str(UUID(conversation_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid conversation id (expected UUID): {conversation_id}",
        ) from exc


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _resolve_conversation(request: ChatRequest, user_id: str) -> str:
    """Create or validate conversation; does not persist the user message yet."""
    if request.conversation_id:
        conv_id = _parse_conversation_id(request.conversation_id)
        if db.get_conversation(conv_id) is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conv_id
    return db.create_conversation(request.message, started_by_user_id=user_id)


async def _chat_events(
    request: ChatRequest,
    conv_id: str,
    user_id: str,
) -> AsyncIterator[str]:
    answer_parts: list[str] = []
    citations: list[Citation] = []

    try:
        db.append_message(conv_id, "user", request.message, author_user_id=user_id)
        history = db.get_chat_history(conv_id)

        async for event in run_agent_stream(history):
            if event.type == "token":
                answer_parts.append(event.data.get("content", ""))
                yield _sse("token", event.data)
            elif event.type == "tool":
                yield _sse("tool", event.data)
            elif event.type == "citations":
                citations = [
                    Citation(**c) for c in event.data.get("citations", [])
                ]
                yield _sse("citations", event.data)
            elif event.type == "error":
                yield _sse("error", event.data)

        answer = "".join(answer_parts)
        if answer:
            db.append_message(
                conv_id,
                "assistant",
                answer,
                citations=citations or None,
            )

        yield _sse("done", {"conversation_id": conv_id})

    except Exception as exc:
        logger.exception("Chat stream failed")
        yield _sse("error", {"message": str(exc)})
        yield _sse("done", {"conversation_id": conv_id})


@router.post("")
async def chat(
    request: ChatRequest,
    user: CurrentUser = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream an agentic RAG reply as Server-Sent Events.

    Events: token, tool, citations, done, error
    """
    conv_id = _resolve_conversation(request, user.id)
    return StreamingResponse(
        _chat_events(request, conv_id, user.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
