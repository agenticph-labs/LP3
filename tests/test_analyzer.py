"""Tests for the RFP Analyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pdf_parser import extract_text

HERE = Path(__file__).resolve().parent
SAMPLE_PDF = HERE.parent / "sample_docs" / "rfp_sample.pdf"


def test_extract_text_sample():
    """We can extract text from the bundled sample PDF."""
    text, pages = extract_text(SAMPLE_PDF)
    assert len(text) > 100
    assert pages >= 1
    assert "RFP" in text or "Request for" in text


def test_extract_text_missing():
    """Non-existent PDF raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_text("/nonexistent/path.pdf")
