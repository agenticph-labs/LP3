"""Core RFP analysis orchestration — PDF → LLM → structured output."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from openai import OpenAI

from src.models import RFPParseResult
from src.pdf_parser import extract_text
from src.prompt import SYSTEM_PROMPT, build_user_prompt

logger = logging.getLogger(__name__)


class RPFAnalyzer:
    """Orchestrates PDF parsing + LLM extraction for a single document."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: OpenAI | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def analyze(self, pdf_path: str | Path) -> RFPParseResult:
        """Analyze a single RFP PDF and return structured extraction."""
        text, page_count = extract_text(pdf_path)

        if len(text.strip()) == 0:
            raise ValueError(f"No extractable text found in {pdf_path}")

        word_count = len(text.split())

        logger.info(
            "Extracted %d words from %d pages — sending to LLM (%s)",
            word_count,
            page_count,
            self.model,
        )

        result_json = self._llm_extract(text, {"Pages": page_count, "Words": word_count})
        result = RFPParseResult.model_validate(result_json)
        result.raw_pages = page_count
        result.raw_word_count = word_count

        logger.info("Analysis complete: %s", result.title)
        return result

    def _llm_extract(self, text: str, metadata: dict) -> dict:
        """Call the LLM and return parsed JSON dict."""
        user_prompt = build_user_prompt(text, metadata)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw = response.choices[0].message.content
        if not raw:
            raise RuntimeError("LLM returned empty response")

        return json.loads(raw)

    def analyze_batch(self, pdf_paths: list[Path]) -> list[RFPParseResult]:
        """Analyze multiple PDFs sequentially."""
        return [self.analyze(p) for p in pdf_paths]
