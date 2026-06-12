"""
API contract — shared data shapes for requests and responses.

Both the mock endpoints (Milestone 1) and the real RAG pipeline (later)
must return JSON that matches these models. The React client mirrors
these types in client/src/types/api.ts.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Indexing lifecycle for an uploaded document."""

    PENDING = "pending"      # uploaded, waiting for worker
    INDEXING = "indexing"    # worker is chunking + embedding
    READY = "ready"          # searchable in the vector DB
    FAILED = "failed"        # ingestion error


class Document(BaseModel):
    """One row in the document dashboard list."""

    id: str
    filename: str
    status: DocumentStatus
    updated_at: datetime


class Citation(BaseModel):
    """A source chunk the AI used to ground its answer."""

    document_id: str
    filename: str
    chunk_text: str
    page: int | None = None  # PDFs may have a page; Markdown/HTML may not


class ChatRequest(BaseModel):
    """Body sent when the user submits a chat message."""

    message: str = Field(..., min_length=1)
    conversation_id: str | None = None  # None = start a new conversation


class ChatResponse(BaseModel):
    """Non-streaming chat reply (Milestone 1 mock; streaming added in M3)."""

    answer: str
    citations: list[Citation]


class HealthResponse(BaseModel):
    """Simple liveness check — confirms the API is running."""

    status: str = "ok"
