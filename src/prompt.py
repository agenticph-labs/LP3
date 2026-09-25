"""LLM prompts for RFP extraction."""

from __future__ import annotations

SYSTEM_PROMPT = """You are an expert procurement analyst. Your job is to extract structured
information from government and corporate RFP (Request for Proposal), RFQ (Request for Quote),
and tender documents.

Extract every relevant field you can find. Be precise — use the exact dates, names, and
numbers as they appear in the document. If a piece of information is not present in the
text, omit it rather than guessing.

Pay special attention to:
- Submission deadlines and key dates
- Eligibility requirements (financial, experience, certifications)
- Deliverables with due dates
- Evaluation criteria and their weights
- Any red flags, unusual clauses, or risks
"""


def build_user_prompt(text: str, metadata: dict | None = None) -> str:
    """Build the user-turn prompt with document text and optional metadata."""
    meta_block = ""
    if metadata:
        lines = [f"- {k}: {v}" for k, v in metadata.items()]
        meta_block = "Document metadata:\n" + "\n".join(lines) + "\n\n"

    return f"""{meta_block}Below is the full text of a procurement document. Extract every
field from the schema — even partial extractions are valuable.

DOCUMENT TEXT:
---
{text}
---

Return ONLY valid JSON matching the RFPParseResult schema."""
