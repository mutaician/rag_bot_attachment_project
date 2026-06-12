"""
Chat endpoints.

Milestone 1: returns a static mock answer + citation (ignores the question).
Milestone 3: will stream real LLM responses with RAG retrieval.
"""

from fastapi import APIRouter

from app.schemas import ChatRequest, ChatResponse, Citation

router = APIRouter(prefix="/chat", tags=["chat"])

# Hardcoded reply for Milestone 1 — proves the request/response contract works
_MOCK_RESPONSE = ChatResponse(
    answer="Employees receive 20 days of PTO per year.",
    citations=[
        Citation(
            document_id="doc-2",
            filename="hr-handbook.pdf",
            chunk_text="Full-time employees accrue 20 days of PTO annually.",
            page=12,
        )
    ],
)


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Accept a user message and return an AI reply with source citations.

    For now we ignore request.message and always return the same mock data.
    """
    # request.conversation_id is accepted but unused until Milestone 3
    _ = request
    return _MOCK_RESPONSE
