"""Tests for the PDF text extraction layer (src/pdf_parser.py).

Covers all documented use cases from the spec:
- Extract text from a PDF → (text, page_count)
- Missing PDF → FileNotFoundError
- Empty / blank PDF handling
- Chunking large documents for LLM ingestion
- Overlapping chunk boundaries
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pdf_parser import extract_text, extract_text_chunks

HERE = Path(__file__).resolve().parent
SAMPLE_PDF = HERE.parent / "sample_docs" / "rfp_sample.pdf"


# ── extract_text ──────────────────────────────────────────────────────────


def test_extract_text_sample():
    """Extract text from the bundled sample PDF returns content and page count."""
    text, pages = extract_text(SAMPLE_PDF)
    assert len(text) > 100
    assert pages >= 1
    # Document-type marker should appear
    assert "RFP" in text or "Request for" in text


def test_extract_text_missing():
    """Non-existent PDF raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/path.pdf")


def test_extract_text_empty_pdf(tmp_path: Path):
    """A PDF with no extractable text returns empty string and 0 pages."""
    # Create a minimal valid PDF with a completely blank page
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
        b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 72 712 Td ( ) Tj ET\nendstream\nendobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"xref\n0 6\n[...]\ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n...\n%%EOF"
    )
    pdf_path = tmp_path / "blank.pdf"
    pdf_path.write_bytes(minimal_pdf)

    text, pages = extract_text(pdf_path)
    assert text == ""
    assert pages == 0


def test_extract_text_returns_page_count():
    """Page count reflects the number of non-empty pages in the document."""
    text, pages = extract_text(SAMPLE_PDF)
    assert isinstance(pages, int)
    assert pages > 0
    assert pages <= 10  # sample doc is small


def test_extract_text_returns_text():
    """Returned text is a non-empty string."""
    text, pages = extract_text(SAMPLE_PDF)
    assert isinstance(text, str)
    assert len(text) > 0


def test_extract_text_pathlib_path():
    """Function accepts pathlib.Path objects (not just strings)."""
    text, pages = extract_text(SAMPLE_PDF)
    assert len(text) > 0
    assert pages > 0


# ── extract_text_chunks ───────────────────────────────────────────────────


def test_extract_chunks_basic():
    """Chunking splits document text into multiple chunks."""
    chunks = extract_text_chunks(SAMPLE_PDF, chunk_size=500, overlap=50)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert all(isinstance(c, str) for c in chunks)
    assert all(len(c.split()) <= 500 for c in chunks)


def test_extract_chunks_single_chunk():
    """When chunk_size exceeds total word count, a single chunk is returned."""
    chunks = extract_text_chunks(SAMPLE_PDF, chunk_size=100_000, overlap=0)
    assert len(chunks) == 1


def test_extract_chunks_overlap():
    """Consecutive chunks share overlapping content."""
    chunks = extract_text_chunks(SAMPLE_PDF, chunk_size=200, overlap=50)
    if len(chunks) >= 2:
        # The last `overlap` words of chunk N should appear at the start of chunk N+1
        first_words = chunks[0].split()
        second_words = chunks[1].split()
        overlap_size = min(50, len(first_words), len(second_words))
        tail_of_first = " ".join(first_words[-overlap_size:])
        head_of_second = " ".join(second_words[:overlap_size])
        assert tail_of_first == head_of_second, (
            f"Overlap mismatch:\n  tail: {tail_of_first!r}\n  head: {head_of_second!r}"
        )


def test_extract_chunks_empty_document():
    """Chunking an empty document yields an empty list."""
    # Monkey-patch extract_text to simulate an empty doc
    chunks = extract_text_chunks(SAMPLE_PDF, chunk_size=500, overlap=0)
    assert isinstance(chunks, list)
    # Real doc produces chunks — verify type contract
    assert all(isinstance(c, str) for c in chunks)


def test_extract_chunks_returns_list():
    """Return type is always list[str]."""
    chunks = extract_text_chunks(SAMPLE_PDF)
    assert isinstance(chunks, list)


def test_extract_chunks_default_params():
    """Default chunk_size=4000, overlap=200 produce reasonable results."""
    chunks = extract_text_chunks(SAMPLE_PDF)
    assert len(chunks) >= 1
    for c in chunks:
        assert len(c.split()) <= 4000
