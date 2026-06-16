"""
Split extracted text into overlapping chunks for embedding.

Uses character counts as a rough stand-in for tokens (~4 chars ≈ 1 token).
"""

from dataclasses import dataclass

from app.ingestion.extract import TextBlock

# ~500 tokens and ~50-token overlap (implementation.md defaults)
DEFAULT_CHUNK_SIZE = 2000
DEFAULT_CHUNK_OVERLAP = 200


@dataclass(frozen=True)
class Chunk:
    """One segment ready to be embedded and stored."""

    text: str
    page: int | None
    chunk_index: int


def chunk_blocks(
    blocks: list[TextBlock],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Turn text blocks into numbered chunks, preserving PDF page numbers."""
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[Chunk] = []
    index = 0

    for block in blocks:
        for piece in _split_with_overlap(block.text, chunk_size, overlap):
            chunks.append(
                Chunk(text=piece, page=block.page, chunk_index=index)
            )
            index += 1

    return chunks


def _split_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    """Slide a window across text with overlap between consecutive chunks."""
    if not text:
        return []

    pieces: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        piece = text[start:end].strip()
        if piece:
            pieces.append(piece)
        if end >= len(text):
            break
        start = end - overlap

    return pieces
