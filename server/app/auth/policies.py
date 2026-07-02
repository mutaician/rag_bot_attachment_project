"""Authorization policies — team vs private conversations, document ownership."""

VALID_CONVERSATION_VISIBILITY = frozenset({"team", "private"})


def can_read_conversation(
    visibility: str,
    started_by_user_id: str | None,
    user_id: str,
) -> bool:
    """Team threads are visible to all; private threads only to the starter."""
    if visibility == "team":
        return True
    return started_by_user_id is not None and started_by_user_id == user_id


def can_write_conversation(
    visibility: str,
    started_by_user_id: str | None,
    user_id: str,
) -> bool:
    """Anyone may post in team threads; private threads only for the starter."""
    return can_read_conversation(visibility, started_by_user_id, user_id)


def can_delete_conversation(started_by_user_id: str | None, user_id: str) -> bool:
    """Only the conversation starter may delete a thread."""
    return started_by_user_id is not None and started_by_user_id == user_id


def can_delete_document(uploaded_by_user_id: str | None, user_id: str) -> bool:
    """Only the uploader may delete a document."""
    return uploaded_by_user_id is not None and uploaded_by_user_id == user_id
