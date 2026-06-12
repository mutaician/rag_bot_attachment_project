"""
Document list endpoints.

Milestone 1: returns hardcoded mock data.
Milestone 2: will read from SQLite + real indexing status.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas import Document, DocumentStatus

# APIRouter keeps routes modular — main.py mounts this under a URL prefix
router = APIRouter(prefix="/documents", tags=["documents"])

# Static mock data for Milestone 1 (replaced by a database in Milestone 2)
_MOCK_DOCUMENTS: list[Document] = [
    Document(
        id="doc-1",
        filename="onboarding.md",
        status=DocumentStatus.READY,
        updated_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    ),
    Document(
        id="doc-2",
        filename="hr-handbook.pdf",
        status=DocumentStatus.INDEXING,
        updated_at=datetime(2026, 6, 2, 9, 30, 0, tzinfo=timezone.utc),
    ),
    Document(
        id="doc-3",
        filename="security-policy.docx",
        status=DocumentStatus.PENDING,
        updated_at=datetime(2026, 6, 3, 14, 15, 0, tzinfo=timezone.utc),
    ),
]


@router.get("", response_model=list[Document])
def list_documents() -> list[Document]:
    """Return all documents and their indexing status."""
    return _MOCK_DOCUMENTS
