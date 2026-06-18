"""
PostgreSQL access layer.

Uses psycopg (v3) — the modern Postgres driver for Python.
Each function opens a connection, runs SQL, and returns plain Python types.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Json

from app.config import settings
from app.schemas import (
    Citation,
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
    Document,
    DocumentStatus,
)


def _archived_db_filename(document_id: str, original_filename: str) -> str:
    """DB filename for a soft-deleted document (outside active versioning)."""
    return f"archive/{document_id}/{original_filename}"


def _archive_file_on_disk(document_id: str, original_filename: str, storage_path: str) -> Path:
    """Move the raw file under uploads/archive/<id>/<original name>."""
    source = Path(storage_path)
    archive_path = settings.uploads_dir / "archive" / document_id / Path(original_filename).name
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if source.is_file():
        source.rename(archive_path)
    return archive_path


def _compact_active_versions(cur: psycopg.Cursor, filename: str) -> None:
    """
    Renumber visible documents for this filename to 1..n (no gaps).

    Keeps document_chunks.version in sync for any indexed copies.
    """
    cur.execute(
        """
        SELECT id FROM documents
        WHERE filename = %s AND deleted_at IS NULL
        ORDER BY version ASC
        FOR UPDATE
        """,
        (filename,),
    )
    doc_ids = [row[0] for row in cur.fetchall()]
    for new_version, doc_id in enumerate(doc_ids, start=1):
        cur.execute(
            "UPDATE documents SET version = %s, updated_at = NOW() WHERE id = %s",
            (new_version, doc_id),
        )
        cur.execute(
            "UPDATE document_chunks SET version = %s WHERE document_id = %s",
            (new_version, doc_id),
        )


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    """
    Context manager for a database connection.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
    Connection closes automatically when the `with` block ends.
    """
    with psycopg.connect(settings.database_url) as conn:
        yield conn


def list_documents() -> list[Document]:
    """
    Return visible documents (not soft-deleted), newest first.

    Maps Postgres rows → Pydantic Document models for the API response.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, filename, version, status, updated_at
                FROM documents
                WHERE deleted_at IS NULL
                ORDER BY updated_at DESC
                """
            )
            rows = cur.fetchall()

    return [
        Document(
            id=str(row[0]),
            filename=row[1],
            version=row[2],
            status=DocumentStatus(row[3]),
            updated_at=row[4],
        )
        for row in rows
    ]


def next_version_for_filename(filename: str) -> int:
    """Next version among visible documents with this filename (1 if none)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1
                FROM documents
                WHERE filename = %s AND deleted_at IS NULL
                """,
                (filename,),
            )
            row = cur.fetchone()
    assert row is not None
    return int(row[0])


def create_document_with_job(
    document_id: UUID,
    filename: str,
    version: int,
    storage_path: str,
) -> str:
    """
    Insert a new document (status=pending) and enqueue an indexing job.

    Returns the document id as a string for the API response.
    """
    job_id = uuid4()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (
                    id, filename, version, status, storage_path, updated_at
                )
                VALUES (%s, %s, %s, 'pending', %s, NOW())
                """,
                (document_id, filename, version, storage_path),
            )
            cur.execute(
                """
                INSERT INTO indexing_jobs (id, document_id, status)
                VALUES (%s, %s, 'pending')
                """,
                (job_id, document_id),
            )
        conn.commit()
    return str(document_id)


def soft_delete_document(document_id: str) -> bool:
    """
    Soft-delete: hide from the app, archive the file, remove embeddings.

    Archives to uploads/archive/<id>/<original name> and renames the DB row
    so active documents keep compact version numbers (1..n) per filename.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT filename, storage_path
                FROM documents
                WHERE id = %s AND deleted_at IS NULL
                FOR UPDATE
                """,
                (document_id,),
            )
            row = cur.fetchone()
            if row is None:
                return False

            original_filename, storage_path = row[0], row[1]
            archived_filename = _archived_db_filename(document_id, original_filename)
            archive_path = _archive_file_on_disk(
                document_id, original_filename, storage_path
            )

            cur.execute(
                """
                UPDATE documents
                SET deleted_at = NOW(),
                    updated_at = NOW(),
                    filename = %s,
                    storage_path = %s
                WHERE id = %s
                """,
                (archived_filename, str(archive_path), document_id),
            )
            cur.execute(
                "DELETE FROM document_chunks WHERE document_id = %s",
                (document_id,),
            )
            cur.execute(
                """
                UPDATE indexing_jobs
                SET status = 'failed'
                WHERE document_id = %s AND status IN ('pending', 'processing')
                """,
                (document_id,),
            )
            _compact_active_versions(cur, original_filename)
        conn.commit()
    return True


def hard_delete_document(document_id: str) -> bool:
    """
    Permanently remove a document: DB row, chunks (cascade), and file on disk.

    Works even if the document was previously soft-deleted.
    Compacts version numbers for remaining visible docs with the same filename.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT storage_path, filename, deleted_at
                FROM documents
                WHERE id = %s
                FOR UPDATE
                """,
                (document_id,),
            )
            row = cur.fetchone()
            if row is None:
                return False
            storage_path, filename, deleted_at = row[0], row[1], row[2]
            active_filename = filename if deleted_at is None else None
            cur.execute("DELETE FROM documents WHERE id = %s", (document_id,))
            if active_filename is not None:
                _compact_active_versions(cur, active_filename)
        conn.commit()

    file_path = Path(storage_path)
    if file_path.is_file():
        file_path.unlink()
    return True


# --- Worker helpers (indexing_jobs queue) ---


@dataclass(frozen=True)
class PendingJob:
    job_id: str
    document_id: str


@dataclass(frozen=True)
class DocumentRecord:
    """Fields the ingestion worker needs to process a document."""

    id: str
    filename: str
    version: int
    storage_path: str


def claim_next_pending_job() -> PendingJob | None:
    """
    Atomically take the oldest pending job (SKIP LOCKED for safe concurrency).

    Returns None when the queue is empty.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE indexing_jobs
                SET status = 'processing'
                WHERE id = (
                    SELECT j.id
                    FROM indexing_jobs j
                    INNER JOIN documents d ON d.id = j.document_id
                    WHERE j.status = 'pending'
                      AND d.deleted_at IS NULL
                    ORDER BY j.created_at
                    LIMIT 1
                    FOR UPDATE OF j SKIP LOCKED
                )
                RETURNING id, document_id
                """
            )
            row = cur.fetchone()
        conn.commit()

    if row is None:
        return None
    return PendingJob(job_id=str(row[0]), document_id=str(row[1]))


def get_document_record(document_id: str) -> DocumentRecord | None:
    """Load document metadata for the worker (active documents only)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, filename, version, storage_path
                FROM documents
                WHERE id = %s AND deleted_at IS NULL
                """,
                (document_id,),
            )
            row = cur.fetchone()

    if row is None:
        return None
    return DocumentRecord(
        id=str(row[0]),
        filename=row[1],
        version=row[2],
        storage_path=row[3],
    )


def update_document_status(
    document_id: str,
    status: str,
    error_message: str | None = None,
) -> None:
    """Update indexing status shown on the dashboard."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE documents
                SET status = %s, error_message = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (status, error_message, document_id),
            )
        conn.commit()


def is_document_active(document_id: str) -> bool:
    """True if the document exists and is not soft-deleted."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM documents
                WHERE id = %s AND deleted_at IS NULL
                """,
                (document_id,),
            )
            return cur.fetchone() is not None


def finish_job(job_id: str, status: str) -> None:
    """Mark an indexing job done or failed."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE indexing_jobs SET status = %s WHERE id = %s",
                (status, job_id),
            )
        conn.commit()


# --- Conversations (Milestone 3) ---


def _title_from_message(message: str) -> str:
    text = message.strip().replace("\n", " ")
    if len(text) <= 80:
        return text or "New conversation"
    return text[:77] + "..."


def create_conversation(first_user_message: str | None = None) -> str:
    """Create a conversation; optional first message sets the title."""
    conv_id = uuid4()
    title = (
        _title_from_message(first_user_message)
        if first_user_message
        else "New conversation"
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (id, title)
                VALUES (%s, %s)
                """,
                (conv_id, title),
            )
        conn.commit()
    return str(conv_id)


def list_conversations() -> list[ConversationSummary]:
    """All conversations, most recently updated first."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
                """
            )
            rows = cur.fetchall()

    return [
        ConversationSummary(
            id=str(row[0]),
            title=row[1],
            created_at=row[2],
            updated_at=row[3],
        )
        for row in rows
    ]


def _parse_citations(raw: object) -> list[Citation] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [Citation(**item) for item in raw]
    return None


def get_conversation(conversation_id: str) -> ConversationDetail | None:
    """Load a conversation and its messages, or None if missing."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                WHERE id = %s
                """,
                (conversation_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None

            cur.execute(
                """
                SELECT id, role, content, citations, created_at
                FROM conversation_messages
                WHERE conversation_id = %s
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            msg_rows = cur.fetchall()

    messages = [
        ConversationMessage(
            id=str(m[0]),
            role=m[1],
            content=m[2],
            citations=_parse_citations(m[3]),
            created_at=m[4],
        )
        for m in msg_rows
    ]

    return ConversationDetail(
        id=str(row[0]),
        title=row[1],
        created_at=row[2],
        updated_at=row[3],
        messages=messages,
    )


def delete_conversation(conversation_id: str) -> bool:
    """Permanently delete a conversation and its messages."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
            deleted = cur.rowcount > 0
        conn.commit()
    return deleted


def append_message(
    conversation_id: str,
    role: str,
    content: str,
    citations: list[Citation] | None = None,
) -> str:
    """Append a user or assistant message; returns message id."""
    msg_id = uuid4()
    citations_json = (
        Json([c.model_dump(mode="json") for c in citations]) if citations else None
    )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversation_messages (
                    id, conversation_id, role, content, citations
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (msg_id, conversation_id, role, content, citations_json),
            )
            cur.execute(
                """
                UPDATE conversations
                SET updated_at = NOW()
                WHERE id = %s
                """,
                (conversation_id,),
            )
        conn.commit()
    return str(msg_id)


def get_chat_history(conversation_id: str) -> list[dict[str, str]]:
    """
    User/assistant turns for the Ollama agent (ordered oldest first).

    Tool rounds are not persisted — each new user message starts a fresh agent run.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content
                FROM conversation_messages
                WHERE conversation_id = %s
                  AND role IN ('user', 'assistant')
                ORDER BY created_at ASC
                """,
                (conversation_id,),
            )
            rows = cur.fetchall()

    return [{"role": row[0], "content": row[1]} for row in rows]
