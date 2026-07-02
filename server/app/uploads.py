"""Streaming file upload helpers with size enforcement."""

from pathlib import Path

from fastapi import HTTPException, UploadFile

CHUNK_SIZE = 1024 * 1024  # 1 MiB


async def stream_upload_to_disk(
    upload: UploadFile,
    dest: Path,
    max_bytes: int,
) -> int:
    """Write upload to disk in chunks; reject if total size exceeds max_bytes."""
    total = 0
    try:
        with dest.open("wb") as handle:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB",
                    )
                handle.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise

    if total == 0:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Empty file")

    return total
