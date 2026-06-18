"""
Hybrid retrieval: dense vectors (pgvector) + keyword search (tsvector) fused with RRF(Reciprocal Rank Fusion).

Only searches active, ready documents (deleted_at IS NULL).
When multiple versions of the same filename match, keeps the latest version only.
"""

from dataclasses import dataclass

from app import db
from app.ingestion.embed import embed_text

# Reciprocal rank fusion constant (standard default k=60).
RRF_K = 60
CANDIDATE_LIMIT = 20

_ACTIVE_DOC = """
    d.deleted_at IS NULL
    AND d.status = 'ready'
"""


@dataclass(frozen=True)
class SearchHit:
    """One chunk returned from hybrid search."""

    chunk_id: str
    document_id: str
    filename: str
    version: int
    chunk_text: str
    page: int | None
    score: float


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


def _vector_search(cur, query_vector: str) -> list[tuple]:
    cur.execute(
        f"""
        SELECT
            c.id,
            c.document_id,
            c.chunk_text,
            c.page,
            c.version,
            d.filename
        FROM document_chunks c
        INNER JOIN documents d ON d.id = c.document_id
        WHERE {_ACTIVE_DOC}
          AND c.embedding IS NOT NULL
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
        """,
        (query_vector, CANDIDATE_LIMIT),
    )
    return cur.fetchall()


def _keyword_search(cur, query: str) -> list[tuple]:
    cur.execute(
        f"""
        SELECT
            c.id,
            c.document_id,
            c.chunk_text,
            c.page,
            c.version,
            d.filename,
            ts_rank(c.search_vector, plainto_tsquery('english', %s)) AS rank
        FROM document_chunks c
        INNER JOIN documents d ON d.id = c.document_id
        WHERE {_ACTIVE_DOC}
          AND c.search_vector @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC
        LIMIT %s
        """,
        (query, query, CANDIDATE_LIMIT),
    )
    return cur.fetchall()


def _rrf_merge(
    vector_rows: list[tuple],
    keyword_rows: list[tuple],
) -> dict[str, tuple[float, tuple]]:
    """
    Fuse rank lists with RRF: score += 1 / (RRF_K + rank).

    Returns chunk_id -> (score, row_without_rank_column).
    """
    scores: dict[str, float] = {}
    rows: dict[str, tuple] = {}

    for rank, row in enumerate(vector_rows, start=1):
        chunk_id = str(row[0])
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        rows[chunk_id] = row

    for rank, row in enumerate(keyword_rows, start=1):
        chunk_id = str(row[0])
        scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
        # Keyword rows include rank as last column; store base tuple shape.
        rows[chunk_id] = row[:6]

    return {cid: (scores[cid], rows[cid]) for cid in scores}


def _prefer_latest_version(hits: list[SearchHit]) -> list[SearchHit]:
    """Drop older versions when the same filename appears more than once."""
    max_version: dict[str, int] = {}
    for hit in hits:
        current = max_version.get(hit.filename, 0)
        if hit.version > current:
            max_version[hit.filename] = hit.version

    return [h for h in hits if h.version == max_version[h.filename]]


def _rows_to_hits(merged: dict[str, tuple[float, tuple]]) -> list[SearchHit]:
    hits = [
        SearchHit(
            chunk_id=chunk_id,
            document_id=str(row[1]),
            chunk_text=row[2],
            page=row[3],
            version=row[4],
            filename=row[5],
            score=score,
        )
        for chunk_id, (score, row) in merged.items()
    ]
    hits.sort(key=lambda h: h.score, reverse=True)
    return _prefer_latest_version(hits)


def hybrid_search_sync(query: str, query_vector: list[float], top_k: int = 5) -> list[SearchHit]:
    """
    Run hybrid search with a precomputed query embedding.

    Useful for tests; chat path should call async hybrid_search().
    """
    if not query.strip():
        return []

    vector_literal = _vector_literal(query_vector)

    with db.get_connection() as conn:
        with conn.cursor() as cur:
            vector_rows = _vector_search(cur, vector_literal)
            keyword_rows = _keyword_search(cur, query)

    merged = _rrf_merge(vector_rows, keyword_rows)
    hits = _rows_to_hits(merged)
    return hits[:top_k]


async def hybrid_search(query: str, top_k: int = 5) -> list[SearchHit]:
    """Embed the query locally, then run vector + keyword search with RRF."""
    if not query.strip():
        return []

    query_vector = await embed_text(query)
    return hybrid_search_sync(query, query_vector, top_k=top_k)
