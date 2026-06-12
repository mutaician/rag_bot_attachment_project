"""
FastAPI application entry point.

Run from the server/ directory:
    uv run uvicorn app.main:app --reload --port 8000

`app` (lowercase) is the FastAPI instance uvicorn looks for.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import HealthResponse
from app.routers import documents, chat 

# Create the ASGI application — uvicorn imports this `app` object
app = FastAPI(
    title="RAG Knowledge Base API",
    version="0.1.0",
)

# Allow the React dev server (Vite default port) to call this API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check — hit this first to confirm the server is up."""
    return HealthResponse()

app.include_router(documents.router)
app.include_router(chat.router)

