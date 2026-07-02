"""
Conversation list and history endpoints (Milestone 3).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.auth.deps import CurrentUser, get_current_user
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
def list_conversations(
    user: CurrentUser = Depends(get_current_user),
) -> list[ConversationSummary]:
    """Return conversations visible to the user (team + own private)."""
    return db.list_conversations(user.id)


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> ConversationDetail:
    """Return one conversation if the user may read it."""
    conv_id = _parse_conversation_id(conversation_id)
    conversation = db.get_conversation(conv_id, user.id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    """Delete a conversation only if the current user started it."""
    conv_id = _parse_conversation_id(conversation_id)
    result = db.delete_conversation(conv_id, user.id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Conversation not found")
    if result == "forbidden":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the conversation starter may delete this thread",
        )
