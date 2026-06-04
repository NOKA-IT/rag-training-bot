"""Extract text from uploaded documents and split into chunks."""
import os
from typing import List

from pypdf import PdfReader
import docx

from ..config import settings


def extract_text(path: str, file_type: str) -> str:
    """Extract raw text from a PDF, DOCX, or plain text file."""
    ext = (file_type or os.path.splitext(path)[1]).lower().lstrip(".")

    if ext == "pdf":
        return _extract_pdf(path)
    if ext in ("docx", "doc"):
        return _extract_docx(path)
    if ext in ("txt", "md", "text"):
        return _extract_txt(path)

    # Fallback: try plain text
    return _extract_txt(path)


def _extract_pdf(path: str) -> str:
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(parts)


def _extract_docx(path: str) -> str:
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def _extract_txt(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk_text(text: str,
               chunk_size: int = None,
               overlap: int = None) -> List[str]:
    """Split text into overlapping chunks by character count on word boundaries."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    text = " ".join(text.split())  # normalize whitespace
    if not text:
        return []

    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        # try not to cut mid-word
        if end < length:
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks
