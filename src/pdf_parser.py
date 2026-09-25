"""PDF text extraction using PyMuPDF (fitz)."""

from __future__ import annotations

import logging
from pathlib import Path

import pymupdf  # PyMuPDF

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str | Path) -> tuple[str, int]:
    """Extract all text from a PDF, returning (text, page_count)."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = pymupdf.open(str(path))
    pages: list[str] = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        if text.strip():
            pages.append(text)
        else:
            logger.warning("Page %d appears empty — skipping", page_num)

    full_text = "\n\n".join(pages)
    logger.info("Extracted %d chars from %d pages", len(full_text), len(pages))
    return full_text, len(pages)


def extract_text_chunks(
    pdf_path: str | Path,
    chunk_size: int = 4_000,
    overlap: int = 200,
) -> list[str]:
    """Extract text and split into overlapping chunks for LLM ingestion."""
    text, _ = extract_text(pdf_path)
    words = text.split()
    chunks: list[str] = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    return chunks
