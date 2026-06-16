"""
Extract plain text from uploaded files.

Milestone 2: PDF (basic text layer), .txt, and .md only.
"""

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class TextBlock:
    """A piece of extracted text, optionally tied to a PDF page number."""

    text: str
    page: int | None = None


def extract_document(path: str | Path) -> list[TextBlock]:
    """
    Read a file and return one or more text blocks.

    PDFs yield one block per page (for page citations later).
    .txt / .md yield a single block with page=None.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    if suffix in {".txt", ".md"}:
        text = file_path.read_text(encoding="utf-8").strip()
        return [TextBlock(text=text)] if text else []

    raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(path: Path) -> list[TextBlock]:
    """Pull text from each PDF page (no OCR — scanned images stay empty)."""
    reader = PdfReader(path)
    blocks: list[TextBlock] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            blocks.append(TextBlock(text=text, page=page_num))

    return blocks
