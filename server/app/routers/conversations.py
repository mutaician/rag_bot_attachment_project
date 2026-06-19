"""
Conversation list and history endpoints (Milestone 3).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import db
from app.auth.deps import get_current_user
from app.schemas import ConversationDetail, ConversationSummary

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
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


@router.get("", response_model=list[ConversationSummary])
def list_conversations() -> list[ConversationSummary]:
    """Return all conversations, newest activity first."""
    return db.list_conversations()


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str) -> ConversationDetail:
    """Return one conversation with full message history."""
    conv_id = _parse_conversation_id(conversation_id)
    conversation = db.get_conversation(conv_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str) -> None:
    """Permanently delete a conversation and its messages."""
    conv_id = _parse_conversation_id(conversation_id)
    if not db.delete_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
