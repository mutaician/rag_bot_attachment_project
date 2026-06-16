"""
FastAPI application entry point.

Run from the server/ directory:
    uv run uvicorn app.main:app --reload --port 8000

Starts the HTTP API and the background indexing worker in one process.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, documents
from app.schemas import HealthResponse
from app.worker import start_background_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan — runs once at startup and once at shutdown.

    Starts the indexing worker thread when the server boots.
    """
    worker_thread, stop_event = start_background_worker()
    yield
    stop_event.set()
    worker_thread.join(timeout=10)


app = FastAPI(
    title="RAG Knowledge Base API",
    version="0.1.0",
    lifespan=lifespan,
)

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
