"""
Background indexing worker — polls Postgres for pending jobs.

Started automatically when FastAPI boots (see app/main.py).
Can still run standalone: uv run python -m app.worker
"""

import logging
import threading

from app import db
from app.ingestion.pipeline import run_job

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 2


def run_worker_loop(stop_event: threading.Event) -> None:
    """
    Poll for pending jobs until stop_event is set.

    Runs in a background thread so the API stays responsive.
    """
    logger.info("Indexing worker started (poll every %ss)", POLL_INTERVAL_SECONDS)

    while not stop_event.is_set():
        job = db.claim_next_pending_job()
        if job is None:
            # wait() returns early if stop_event is set during shutdown
            stop_event.wait(POLL_INTERVAL_SECONDS)
            continue

        logger.info("Processing job %s (document %s)", job.job_id, job.document_id)
        run_job(job)

    logger.info("Indexing worker stopped")


def start_background_worker() -> tuple[threading.Thread, threading.Event]:
    """Start the worker on a daemon thread; returns (thread, stop_event)."""
    stop_event = threading.Event()
    thread = threading.Thread(
        target=run_worker_loop,
        args=(stop_event,),
        name="indexing-worker",
        daemon=True,
    )
    thread.start()
    return thread, stop_event


def main() -> None:
    """Standalone entry point (same loop, blocks until Ctrl+C)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [worker] %(message)s",
        datefmt="%H:%M:%S",
    )
    stop_event = threading.Event()
    try:
        run_worker_loop(stop_event)
    except KeyboardInterrupt:
        stop_event.set()
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
