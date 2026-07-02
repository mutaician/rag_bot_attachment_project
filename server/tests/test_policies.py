"""Unit tests for authorization policies."""

from app.auth.policies import (
    can_delete_conversation,
    can_delete_document,
    can_read_conversation,
    can_write_conversation,
)


def test_team_conversation_readable_by_anyone() -> None:
    assert can_read_conversation("team", "user-a", "user-b") is True
    assert can_write_conversation("team", "user-a", "user-b") is True


def test_private_conversation_only_for_starter() -> None:
    assert can_read_conversation("private", "user-a", "user-b") is False
    assert can_read_conversation("private", "user-a", "user-a") is True
    assert can_write_conversation("private", "user-a", "user-b") is False


def test_only_starter_deletes_conversation() -> None:
    assert can_delete_conversation("user-a", "user-a") is True
    assert can_delete_conversation("user-a", "user-b") is False
    assert can_delete_conversation(None, "user-a") is False


def test_only_owner_deletes_document() -> None:
    assert can_delete_document("user-a", "user-a") is True
    assert can_delete_document("user-a", "user-b") is False
    assert can_delete_document(None, "user-a") is False
