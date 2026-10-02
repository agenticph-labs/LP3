"""Tests for the orchestration / pipeline layer (src/analyzer.py, src/prompt.py).

Covers all documented use cases from the spec:
- RPFAnalyzer initialization (api_key, model, client injection)
- analyze() orchestrator: PDF → LLM → validated RFPParseResult
- Error handling: empty text, LLM failures, invalid JSON
- analyze_batch() for multiple PDFs
- build_user_prompt() with and without metadata
- SYSTEM_PROMPT content requirements
- Mock-based verification of the LLM call path
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.analyzer import RPFAnalyzer
from src.models import RFPParseResult
from src.prompt import SYSTEM_PROMPT, build_user_prompt

HERE = Path(__file__).resolve().parent
SAMPLE_PDF = HERE.parent / "sample_docs" / "rfp_sample.pdf"


# ── SYSTEM_PROMPT ─────────────────────────────────────────────────────────


class TestSystemPrompt:
    def test_contains_procurement_role(self):
        assert "procurement" in SYSTEM_PROMPT.lower() or "RFP" in SYSTEM_PROMPT

    def test_contains_extraction_instructions(self):
        assert "extract" in SYSTEM_PROMPT.lower()

    def test_contains_key_fields(self):
        keywords = ["deadlines", "eligibility", "deliverables", "evaluation", "risks"]
        for kw in keywords:
            assert kw in SYSTEM_PROMPT.lower(), f"Keyword '{kw}' missing from SYSTEM_PROMPT"

    def test_no_hallucination_instruction(self):
        assert "omit" in SYSTEM_PROMPT.lower() or "guess" not in SYSTEM_PROMPT


# ── build_user_prompt ─────────────────────────────────────────────────────


class TestBuildUserPrompt:
    def test_with_metadata(self):
        text = "Sample procurement document text."
        metadata = {"Pages": 5, "Words": 1200}
        prompt = build_user_prompt(text, metadata)

        assert "Pages: 5" in prompt
        assert "Words: 1200" in prompt
        assert text in prompt

    def test_without_metadata(self):
        text = "Just the doc text."
        prompt = build_user_prompt(text)

        assert text in prompt
        assert "Document metadata" not in prompt

    def test_with_none_metadata(self):
        text = "More text."
        prompt = build_user_prompt(text, None)
        assert text in prompt
        assert "Document metadata" not in prompt

    def test_includes_json_instruction(self):
        prompt = build_user_prompt("Some text")
        assert "JSON" in prompt or "json" in prompt
        assert "RFPParseResult" in prompt or "schema" in prompt

    def test_large_text_truncation_not_required(self):
        """The prompt builder handles any text length — no implicit truncation."""
        long_text = "word " * 10_000
        prompt = build_user_prompt(long_text)
        assert len(prompt) > len(long_text)


# ── RPFAnalyzer Initialization ────────────────────────────────────────────


class TestRPFAnalyzerInit:
    def test_default_construction(self):
        """Default construction reads from env (which may be empty in CI)."""
        analyzer = RPFAnalyzer()
        assert analyzer.model == "gpt-4o-mini"  # default

    def test_custom_api_key(self):
        analyzer = RPFAnalyzer(api_key="sk-test")
        assert analyzer.api_key == "sk-test"

    def test_custom_model(self):
        analyzer = RPFAnalyzer(model="gpt-4o")
        assert analyzer.model == "gpt-4o"

    def test_client_injection(self):
        mock_client = MagicMock()
        analyzer = RPFAnalyzer(client=mock_client)
        assert analyzer.client is mock_client

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
        monkeypatch.setenv("LLM_MODEL", "gpt-3.5-turbo")
        analyzer = RPFAnalyzer()
        assert analyzer.api_key == "sk-env-key"
        assert analyzer.model == "gpt-3.5-turbo"

    def test_explicit_beats_env(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-env-key")
        analyzer = RPFAnalyzer(api_key="sk-explicit")
        assert analyzer.api_key == "sk-explicit"


# ── RPFAnalyzer.analyze (mocked) ──────────────────────────────────────────


class TestAnalyze:
    """Tests that exercise the orchestration path with mocked LLM."""

    @pytest.fixture
    def mock_openai(self) -> MagicMock:
        """Return a MagicMock that acts as a successful OpenAI client."""
        mock = MagicMock()
        # Build a ChatCompletion-like response
        valid_result = RFPParseResult(
            title="Test RFP",
            document_type="RFP",
            summary="A test procurement",
        )
        content = json.dumps(valid_result.model_dump(mode="json"))
        mock.chat.completions.create.return_value = _make_fake_response(content)
        return mock

    def test_analyze_success(self, mock_openai: MagicMock):
        analyzer = RPFAnalyzer(client=mock_openai)
        result = analyzer.analyze(SAMPLE_PDF)

        assert isinstance(result, RFPParseResult)
        assert result.title == "Test RFP"
        assert result.summary == "A test procurement"
        assert result.raw_pages > 0  # set from extraction
        assert result.raw_word_count > 0

    def test_analyze_sends_correct_messages(self, mock_openai: MagicMock):
        analyzer = RPFAnalyzer(client=mock_openai)
        analyzer.analyze(SAMPLE_PDF)

        call_kwargs = mock_openai.chat.completions.create.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs[1]
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["response_format"] == {"type": "json_object"}
        assert kwargs["temperature"] == 0.1

        messages = kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert SYSTEM_PROMPT in messages[0]["content"]

    def test_analyze_empty_text_raises(self):
        """Raise ValueError when PDF has no extractable text."""
        mock_client = MagicMock()
        analyzer = RPFAnalyzer(client=mock_client)

        with (
            patch("src.analyzer.extract_text", return_value=("", 0)),
            pytest.raises(ValueError, match="No extractable text found"),
        ):
            analyzer.analyze(SAMPLE_PDF)

    def test_analyze_llm_empty_response_raises(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_fake_response(None)
        analyzer = RPFAnalyzer(client=mock_client)

        with pytest.raises(RuntimeError, match="empty response"):
            analyzer.analyze(SAMPLE_PDF)

    def test_analyze_llm_invalid_json_raises(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_fake_response(
            "not valid json{{{"
        )
        analyzer = RPFAnalyzer(client=mock_client)

        with pytest.raises(json.JSONDecodeError):
            analyzer.analyze(SAMPLE_PDF)

    def test_analyze_llm_invalid_schema_raises(self):
        """LLM returns valid JSON that doesn't match RFPParseResult schema."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_fake_response(
            json.dumps({"invalid": "data"})
        )
        analyzer = RPFAnalyzer(client=mock_client)

        with pytest.raises(Exception):
            analyzer.analyze(SAMPLE_PDF)

    def test_analyze_passes_metadata_in_prompt(self, mock_openai: MagicMock):
        analyzer = RPFAnalyzer(client=mock_openai)
        analyzer.analyze(SAMPLE_PDF)

        call_kwargs = mock_openai.chat.completions.create.call_args
        assert call_kwargs is not None
        user_msg = call_kwargs[1]["messages"][1]["content"]
        # Metadata about pages and words should be included
        assert "Pages" in user_msg
        assert "Words" in user_msg

    def test_analyze_sets_raw_page_and_word_count(self, mock_openai: MagicMock):
        analyzer = RPFAnalyzer(client=mock_openai)
        result = analyzer.analyze(SAMPLE_PDF)

        assert isinstance(result.raw_pages, int)
        assert result.raw_pages > 0
        assert isinstance(result.raw_word_count, int)
        assert result.raw_word_count > 0


# ── analyze_batch ─────────────────────────────────────────────────────────


class TestAnalyzeBatch:
    def test_batch_processes_all_pdfs(self):
        mock_client = MagicMock()
        valid_result = RFPParseResult(
            title="Batch Test",
            document_type="RFP",
            summary="Batched analysis",
        )
        content = json.dumps(valid_result.model_dump(mode="json"))
        mock_client.chat.completions.create.return_value = _make_fake_response(content)
        analyzer = RPFAnalyzer(client=mock_client)

        paths = [SAMPLE_PDF, SAMPLE_PDF]  # same doc twice
        results = analyzer.analyze_batch(paths)

        assert len(results) == 2
        assert all(isinstance(r, RFPParseResult) for r in results)
        assert results[0].title == "Batch Test"
        assert results[1].title == "Batch Test"

    def test_batch_propagates_first_failure(self):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = RuntimeError("API failure")
        analyzer = RPFAnalyzer(client=mock_client)

        with pytest.raises(RuntimeError, match="API failure"):
            analyzer.analyze_batch([SAMPLE_PDF])


# ── Helpers ───────────────────────────────────────────────────────────────


def _make_fake_response(content: str | None) -> MagicMock:
    """Build a mock ChatCompletion response object."""
    fake_choice = MagicMock()
    fake_choice.message.content = content
    fake_response = MagicMock()
    fake_response.choices = [fake_choice]
    return fake_response
