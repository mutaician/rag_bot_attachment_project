"""
End-to-end ingestion for one document: extract → chunk → embed → store.
"""

import logging

from app import db
from app.ingestion.chunk import chunk_blocks
from app.ingestion.chunk_store import insert_chunks
from app.ingestion.embed import embed_text_sync
from app.ingestion.extract import extract_document

logger = logging.getLogger(__name__)


def run_job(job: db.PendingJob) -> None:
    """
    Process a single indexing job.

    Updates document status: pending → indexing → ready (or failed).
    """
    doc = db.get_document_record(job.document_id)
    if doc is None:
        logger.error("Document %s not found for job %s", job.document_id, job.job_id)
        db.finish_job(job.job_id, "failed")
        return

    db.update_document_status(doc.id, "indexing")

    try:
        blocks = extract_document(doc.storage_path)
        chunks = chunk_blocks(blocks)
        if not chunks:
            raise ValueError("No text could be extracted from the file")

        logger.info(
            "Embedding %d chunk(s) for %s v%s",
            len(chunks),
            doc.filename,
            doc.version,
        )
        embeddings = [embed_text_sync(chunk.text) for chunk in chunks]

        if not db.is_document_active(doc.id):
            logger.info("Document %s was deleted during indexing; skipping store", doc.id)
            db.finish_job(job.job_id, "failed")
            return

        count = insert_chunks(doc.id, doc.version, chunks, embeddings)
        logger.info("Stored %d chunk(s) for document %s", count, doc.id)

        db.update_document_status(doc.id, "ready")
        db.finish_job(job.job_id, "done")

    except Exception as exc:
        logger.exception("Indexing failed for document %s", doc.id)
        db.update_document_status(doc.id, "failed", error_message=str(exc)[:500])
        db.finish_job(job.job_id, "failed")
