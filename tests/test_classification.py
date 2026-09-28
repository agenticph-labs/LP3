"""Tests for the Pydantic model layer (src/models.py).

Covers all documented use cases from the spec:
- DocumentType enum values (RFP, RFQ, RFI, Tender, Other)
- EligibilityCriterion with category, requirement, mandatory flag
- Deliverable with name, description, optional due_date
- EvaluationCriterion with criterion and optional weight
- Deadline with label and date alias field
- Risk with severity defaulting to "medium"
- RFPParseResult top-level model with all fields
- Omitted optional fields, default factories, validation errors
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from src.models import (
    Deadline,
    Deliverable,
    DocumentType,
    EligibilityCriterion,
    EvaluationCriterion,
    RFPParseResult,
    Risk,
)


# ── DocumentType ──────────────────────────────────────────────────────────


class TestDocumentType:
    def test_enum_values(self):
        assert DocumentType.rfp.value == "RFP"
        assert DocumentType.rfq.value == "RFQ"
        assert DocumentType.rfi.value == "RFI"
        assert DocumentType.tender.value == "Tender"
        assert DocumentType.other.value == "Other"

    def test_from_string_valid(self):
        assert DocumentType("RFP") == DocumentType.rfp
        assert DocumentType("RFQ") == DocumentType.rfq

    def test_from_string_invalid(self):
        with pytest.raises(ValueError):
            DocumentType("InvalidType")


# ── EligibilityCriterion ──────────────────────────────────────────────────


class TestEligibilityCriterion:
    def test_minimal(self):
        ec = EligibilityCriterion(category="Financial", requirement="Must have $1M insurance")
        assert ec.category == "Financial"
        assert ec.requirement == "Must have $1M insurance"
        assert ec.mandatory is True  # defaults to True

    def test_non_mandatory(self):
        ec = EligibilityCriterion(
            category="Experience",
            requirement="5+ years preferred",
            mandatory=False,
        )
        assert ec.mandatory is False

    def test_serializes_to_dict(self):
        ec = EligibilityCriterion(category="Certification", requirement="ISO 9001")
        data = ec.model_dump()
        assert data["category"] == "Certification"
        assert data["requirement"] == "ISO 9001"
        assert data["mandatory"] is True


# ── Deliverable ───────────────────────────────────────────────────────────


class TestDeliverable:
    def test_with_due_date(self):
        d = Deliverable(
            name="Technical Proposal",
            description="Full technical response",
            due_date="2025-03-15",
        )
        assert d.name == "Technical Proposal"
        assert d.due_date == "2025-03-15"

    def test_without_due_date(self):
        d = Deliverable(name="Final Report", description="Final deliverable")
        assert d.due_date is None

    def test_serializes_optional_fields(self):
        d = Deliverable(name="Report", description="A report")
        data = d.model_dump()
        assert data["due_date"] is None


# ── EvaluationCriterion ───────────────────────────────────────────────────


class TestEvaluationCriterion:
    def test_with_weight(self):
        ec = EvaluationCriterion(criterion="Technical Approach", weight=35.0)
        assert ec.criterion == "Technical Approach"
        assert ec.weight == 35.0

    def test_without_weight(self):
        ec = EvaluationCriterion(criterion="Past Performance")
        assert ec.weight is None

    def test_weight_zero(self):
        ec = EvaluationCriterion(criterion="Mandatory Requirements", weight=0.0)
        assert ec.weight == 0.0


# ── Deadline ──────────────────────────────────────────────────────────────


class TestDeadline:
    def test_construct_with_alias(self):
        """Deadline uses 'date' as the serialization alias for 'date_value'."""
        d = Deadline(label="Submission Deadline", date="2025-06-01")
        assert d.label == "Submission Deadline"
        assert d.date_value == "2025-06-01"

    def test_construct_with_python_name(self):
        d = Deadline(label="Submission Deadline", date_value="2025-06-01")
        assert d.date_value == "2025-06-01"

    def test_serialize_uses_alias(self):
        d = Deadline(label="Q&A Deadline", date_value="2025-05-15")
        data = d.model_dump(by_alias=True)
        assert "date" in data
        assert "date_value" not in data
        assert data["date"] == "2025-05-15"

    def test_round_trip(self):
        d = Deadline(label="Site Visit", date="2025-04-10")
        data = d.model_dump(by_alias=True)
        restored = Deadline.model_validate(data)
        assert restored.label == "Site Visit"
        assert restored.date_value == "2025-04-10"


# ── Risk ──────────────────────────────────────────────────────────────────


class TestRisk:
    def test_minimal(self):
        r = Risk(risk="Unclear Scope", detail="Scope of work is poorly defined")
        assert r.risk == "Unclear Scope"
        assert r.detail == "Scope of work is poorly defined"
        assert r.severity == "medium"  # default

    def test_custom_severity(self):
        r = Risk(risk="Budget Risk", detail="Over budget", severity="high")
        assert r.severity == "high"


# ── RFPParseResult ────────────────────────────────────────────────────────


class TestRFPParseResult:
    def test_minimal(self):
        """Only required fields are title, document_type, and summary."""
        result = RFPParseResult(
            title="RFP-2025-001",
            document_type="RFP",
            summary="A test procurement",
        )
        assert result.title == "RFP-2025-001"
        assert result.document_type == DocumentType.rfp
        assert result.summary == "A test procurement"

    def test_default_factories(self):
        """All list fields default to empty lists; optional fields to None."""
        result = RFPParseResult(
            title="Test",
            document_type="RFP",
            summary="Summary",
        )
        assert result.deadlines == []
        assert result.eligibility_criteria == []
        assert result.deliverables == []
        assert result.evaluation_criteria == []
        assert result.risks == []
        assert result.issuing_organization is None
        assert result.solicitation_number is None
        assert result.budget_range is None
        assert result.raw_pages == 0
        assert result.raw_word_count == 0

    def test_full_construction(self):
        """All fields populated."""
        result = RFPParseResult(
            title="RFP-25-ABC",
            document_type="Tender",
            issuing_organization="City of Metro",
            solicitation_number="RFP-25-ABC-001",
            summary="Full procurement for IT services",
            deadlines=[Deadline(label="Due", date="2025-07-01")],
            eligibility_criteria=[
                EligibilityCriterion(category="Financial", requirement="Bond required"),
            ],
            deliverables=[Deliverable(name="Report", description="Final report")],
            evaluation_criteria=[
                EvaluationCriterion(criterion="Price", weight=40.0),
            ],
            budget_range="$500K - $1M",
            risks=[Risk(risk="Short Timeline", detail="Only 30 days", severity="high")],
            raw_pages=42,
            raw_word_count=15000,
        )
        assert result.issuing_organization == "City of Metro"
        assert len(result.deadlines) == 1
        assert len(result.eligibility_criteria) == 1
        assert len(result.deliverables) == 1
        assert len(result.evaluation_criteria) == 1
        assert len(result.risks) == 1
        assert result.budget_range == "$500K - $1M"
        assert result.raw_pages == 42
        assert result.raw_word_count == 15000

    def test_invalid_document_type(self):
        with pytest.raises(ValidationError):
            RFPParseResult(
                title="Bad",
                document_type="INVALID",
                summary="Should fail",
            )

    def test_missing_required_title(self):
        with pytest.raises(ValidationError):
            RFPParseResult(document_type="RFP", summary="Missing title")  # type: ignore[call-arg]

    def test_missing_required_summary(self):
        with pytest.raises(ValidationError):
            RFPParseResult(title="X", document_type="RFP")  # type: ignore[call-arg]

    def test_serialize_round_trip(self):
        original = RFPParseResult(
            title="RFP-1",
            document_type="RFP",
            summary="Test summary",
            deadlines=[Deadline(label="Due", date="2025-07-01")],
        )
        data = original.model_dump(mode="json")
        restored = RFPParseResult.model_validate(data)
        assert restored.title == original.title
        assert restored.document_type == original.document_type
        assert restored.summary == original.summary
        assert restored.deadlines[0].label == "Due"
        assert restored.deadlines[0].date_value == "2025-07-01"

    def test_empty_lists_in_json_deserialization(self):
        """JSON payload with empty lists deserializes correctly."""
        data: dict[str, Any] = {
            "title": "Test",
            "document_type": "RFP",
            "summary": "Test",
            "deadlines": [],
            "eligibility_criteria": [],
            "deliverables": [],
            "evaluation_criteria": [],
            "risks": [],
        }
        result = RFPParseResult.model_validate(data)
        assert len(result.deadlines) == 0

    def test_partial_criteria(self):
        """A result with only some criteria populated still validates."""
        result = RFPParseResult(
            title="Partial",
            document_type="RFQ",
            summary="Only what's available",
            deadlines=[Deadline(label="Deadline", date="2025-08-01")],
        )
        assert result.document_type == DocumentType.rfq
        assert len(result.eligibility_criteria) == 0
        assert len(result.deliverables) == 0
