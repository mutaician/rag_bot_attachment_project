"""
Tools available to the chat agent.

search_documents wraps hybrid_search and collects citations for the API response.
"""

import json
from dataclasses import dataclass, field

from app.retrieval.hybrid_search import SearchHit, hybrid_search
from app.schemas import Citation

MAX_TOOL_RESULT_CHARS = 8000

SEARCH_DOCUMENTS_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "search_documents",
        "description": (
            "Search uploaded company documents for passages relevant to the query. "
            "Use when you need facts from the knowledge base."
        ),
        "parameters": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of text chunks to return (1-10, default 5)",
                },
            },
        },
    },
}


@dataclass
class CitationStore:
    """Accumulates unique chunks cited across one agent run."""

    citations: list[Citation] = field(default_factory=list)
    _seen_chunk_ids: set[str] = field(default_factory=set)

    def add_hits(self, hits: list[SearchHit]) -> None:
        for hit in hits:
            if hit.chunk_id in self._seen_chunk_ids:
                continue
            self._seen_chunk_ids.add(hit.chunk_id)
            self.citations.append(
                Citation(
                    document_id=hit.document_id,
                    filename=hit.filename,
                    chunk_text=hit.chunk_text,
                    page=hit.page,
                )
            )


def _hits_to_payload(hits: list[SearchHit]) -> list[dict]:
    return [
        {
            "document_id": h.document_id,
            "filename": h.filename,
            "version": h.version,
            "chunk_text": h.chunk_text,
            "page": h.page,
            "score": round(h.score, 4),
        }
        for h in hits
    ]


async def execute_search_documents(
    query: str,
    top_k: int = 5,
    *,
    store: CitationStore,
) -> str:
    """Run hybrid search and return JSON for the model (truncated if huge)."""
    top_k = max(1, min(top_k, 10))
    hits = await hybrid_search(query, top_k=top_k)
    store.add_hits(hits)

    payload = _hits_to_payload(hits)
    if not payload:
        return json.dumps({"results": [], "message": "No matching chunks found."})

    text = json.dumps({"results": payload})
    if len(text) > MAX_TOOL_RESULT_CHARS:
        text = text[:MAX_TOOL_RESULT_CHARS] + '..."}'
    return text


async def dispatch_tool_call(
    name: str,
    arguments: dict,
    *,
    store: CitationStore,
) -> str:
    """Execute a tool requested by the model."""
    if name == "search_documents":
        return await execute_search_documents(
            query=str(arguments.get("query", "")),
            top_k=int(arguments.get("top_k", 5)),
            store=store,
        )
    return json.dumps({"error": f"Unknown tool: {name}"})
