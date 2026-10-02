"""Pydantic models for structured RFP extraction output."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class DocumentType(StrEnum):
    rfp = "RFP"
    rfq = "RFQ"
    rfi = "RFI"
    tender = "Tender"
    other = "Other"


class EligibilityCriterion(BaseModel):
    """A single eligibility or qualification requirement."""
    category: str = Field(description="e.g. 'Financial', 'Experience', 'Certification'")
    requirement: str = Field(description="Full text of the criterion")
    mandatory: bool = Field(default=True)


class Deliverable(BaseModel):
    """A deliverable or work product requested."""
    name: str = Field(description="Short name of the deliverable")
    description: str = Field(description="Full description from the document")
    due_date: str | None = Field(default=None, description="Due date if specified")


class EvaluationCriterion(BaseModel):
    """An evaluation criterion with weight."""
    criterion: str = Field(description="Name / description of the criterion")
    weight: float | None = Field(
        default=None,
        description="Weight percentage (e.g. 30 means 30%)",
    )


class Deadline(BaseModel):
    """A key date extracted from the document."""
    model_config = {"populate_by_name": True}
    label: str = Field(description="What this date is for")
    date_value: str = Field(alias="date", description="Date string as it appears")


class Risk(BaseModel):
    """A potential risk or gotcha identified in the document."""
    risk: str = Field(description="Short risk label")
    detail: str = Field(description="Why this is a risk")
    severity: str = Field(default="medium", description="low / medium / high")


class RFPParseResult(BaseModel):
    """Top-level structured extraction from a single RFP/RFQ document."""

    title: str = Field(description="Document title")
    document_type: DocumentType
    issuing_organization: str | None = None
    solicitation_number: str | None = None

    summary: str = Field(description="One-paragraph summary of the procurement")

    # Key dates
    deadlines: list[Deadline] = Field(default_factory=list)

    # Requirements
    eligibility_criteria: list[EligibilityCriterion] = Field(default_factory=list)
    deliverables: list[Deliverable] = Field(default_factory=list)

    # Evaluation
    evaluation_criteria: list[EvaluationCriterion] = Field(default_factory=list)
    budget_range: str | None = None

    # Risks & gotchas
    risks: list[Risk] = Field(default_factory=list)

    # Raw metadata
    raw_pages: int = 0
    raw_word_count: int = 0
