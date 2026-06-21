"""
Document list and upload endpoints.

Milestone 2: PostgreSQL-backed uploads with filename versioning.
"""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app import db
from app.auth.deps import get_current_user
from app.config import settings
from app.schemas import Document, UploadResponse

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)],
)

# Allowed extensions for Milestone 2 (PDF + plain text formats)
ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}


def _parse_document_id(document_id: str) -> str:
    """Reject malformed ids with 400 instead of letting Postgres 500."""
    try:
        return str(UUID(document_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document id (expected UUID): {document_id}",
        ) from exc


@router.get("", response_model=list[Document])
def list_documents() -> list[Document]:
    """Return all visible documents and their indexing status."""
    return db.list_documents()


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
) -> UploadResponse:
    """
    Accept one or more files via multipart form field name `files`.

    Saves each file to disk, creates a DB row (pending), and enqueues indexing.
    Same filename → new version among visible documents; soft-deleting compacts versions.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    document_ids: list[str] = []

    for upload in files:
        if not upload.filename:
            raise HTTPException(status_code=400, detail="File has no name")

        # Path("dir/report.PDF").suffix → ".pdf"
        filename = Path(upload.filename).name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported type '{suffix}'. Allowed: {sorted(ALLOWED_SUFFIXES)}",
            )

        content = await upload.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"Empty file: {filename}")

        document_id = uuid4()
        storage_path = settings.uploads_dir / f"{document_id}_{filename}"
        storage_path.write_bytes(content)

        version = db.next_version_for_filename(filename)
        doc_id = db.create_document_with_job(
            document_id=document_id,
            filename=filename,
            version=version,
            storage_path=str(storage_path),
        )
        document_ids.append(doc_id)

    return UploadResponse(document_ids=document_ids)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    hard: bool = Query(
        False,
        description="If true, permanently delete file and database row. "
        "Default is soft delete (hide from list, keep data).",
    ),
) -> None:
    """Soft-delete by default; pass ?hard=true to purge permanently."""
    doc_id = _parse_document_id(document_id)
    if hard:
        deleted = db.hard_delete_document(doc_id)
    else:
        deleted = db.soft_delete_document(doc_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
