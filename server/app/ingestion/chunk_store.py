"""
Persist chunks + embeddings into PostgreSQL (pgvector + tsvector).
"""

from uuid import UUID, uuid4

from app import db
from app.ingestion.chunk import Chunk


def insert_chunks(
    document_id: str,
    version: int,
    chunks: list[Chunk],
    embeddings: list[list[float]],
) -> int:
    """
    Insert all chunks for a document in one transaction.

    Returns the number of rows inserted.
    """
    if len(chunks) != len(embeddings):
        raise ValueError("chunks and embeddings length mismatch")
    if not chunks:
        return 0

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                chunk_id = uuid4()
                cur.execute(
                    """
                    INSERT INTO document_chunks (
                        id, document_id, version, chunk_index,
                        chunk_text, page, embedding, search_vector
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s::vector,
                        to_tsvector('english', %s)
                    )
                    """,
                    (
                        chunk_id,
                        UUID(document_id),
                        version,
                        chunk.chunk_index,
                        chunk.text,
                        chunk.page,
                        _vector_literal(embedding),
                        chunk.text,
                    ),
                )
        conn.commit()

    return len(chunks)


def delete_chunks_for_document(document_id: str) -> None:
    """Remove all chunks for a document (used on hard delete — also cascades)."""
    with db.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM document_chunks WHERE document_id = %s",
                (document_id,),
            )
        conn.commit()


def _vector_literal(values: list[float]) -> str:
    """Format a Python list as a pgvector literal: '[0.1, 0.2, ...]'."""
    return "[" + ",".join(str(v) for v in values) + "]"
