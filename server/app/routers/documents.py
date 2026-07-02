"""
Document list and upload endpoints.

Milestone 2: PostgreSQL-backed uploads with filename versioning.
"""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app import db
from app.auth.deps import CurrentUser, get_current_user
from app.auth.policies import can_delete_document
from app.config import settings
from app.schemas import Document, UploadResponse
from app.uploads import stream_upload_to_disk

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)],
)

ALLOWED_SUFFIXES = {".pdf", ".txt", ".md"}


def _parse_document_id(document_id: str) -> str:
    try:
        return str(UUID(document_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document id (expected UUID): {document_id}",
        ) from exc


@router.get("", response_model=list[Document])
def list_documents(user: CurrentUser = Depends(get_current_user)) -> list[Document]:
    """Return all visible documents and their indexing status."""
    return db.list_documents(user.id)


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    user: CurrentUser = Depends(get_current_user),
) -> UploadResponse:
    """Accept one or more files; stream to disk with a strict size cap."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    document_ids: list[str] = []

    for upload in files:
        if not upload.filename:
            raise HTTPException(status_code=400, detail="File has no name")

        filename = Path(upload.filename).name
        suffix = Path(filename).suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported type '{suffix}'. Allowed: {sorted(ALLOWED_SUFFIXES)}",
            )

        document_id = uuid4()
        storage_path = settings.uploads_dir / f"{document_id}_{filename}"

        await stream_upload_to_disk(upload, storage_path, settings.max_upload_bytes)

        version = db.next_version_for_filename(filename)
        doc_id = db.create_document_with_job(
            document_id=document_id,
            filename=filename,
            version=version,
            storage_path=str(storage_path),
            uploaded_by_user_id=user.id,
        )
        document_ids.append(doc_id)

    return UploadResponse(document_ids=document_ids)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    user: CurrentUser = Depends(get_current_user),
    hard: bool = Query(
        False,
        description="If true, permanently delete file and database row. "
        "Default is soft delete (hide from list, keep data).",
    ),
) -> None:
    """Soft-delete by default; only the uploader may delete."""
    doc_id = _parse_document_id(document_id)
    owner_id = db.get_document_uploaded_by(doc_id)
    if owner_id is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if not can_delete_document(owner_id, user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document owner may delete this file",
        )

    if hard:
        deleted = db.hard_delete_document(doc_id)
    else:
        deleted = db.soft_delete_document(doc_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
