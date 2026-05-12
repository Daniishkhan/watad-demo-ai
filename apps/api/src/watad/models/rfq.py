from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from watad.models.approval import ApprovalRequest
from watad.models.credit import CreditCheckResult
from watad.models.document import GeneratedDocument
from watad.models.recommendation import AwardRecommendation
from watad.models.supplier import SupplierCandidate

type OptimizationPreference = Literal[
    "lowest_price",
    "fastest_delivery",
    "balanced",
    "payment_terms",
]
type RFQWorkflowStatus = Literal[
    "draft",
    "needs_clarification",
    "ready_for_supplier_search",
    "supplier_shortlist_ready",
    "recommendation_ready",
    "finance_approval_required",
    "credit_not_eligible",
    "credit_missing_information",
    "draft_artifacts_ready",
    "approval_recorded",
    "approval_rejected",
]


class RFQDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_category: str | None = None
    material_name: str | None = None
    specification: str | None = None
    quantity: float | None = None
    unit: str | None = None
    delivery_city: str | None = None
    delivery_district: str | None = None
    delivery_site: str | None = None
    delivery_deadline: str | None = None
    project_name: str | None = None
    payment_preference: str | None = None
    optimization_preference: OptimizationPreference | None = None
    split_delivery_acceptable: bool | None = None
    certification_requirements: list[str] = Field(default_factory=list)
    notes: str | None = None

    @field_validator(
        "material_category",
        "material_name",
        "specification",
        "unit",
        "delivery_city",
        "delivery_district",
        "delivery_site",
        "delivery_deadline",
        "project_name",
        "payment_preference",
        "notes",
        mode="before",
    )
    @classmethod
    def normalize_blank_string(cls, value: Any) -> Any:
        if not isinstance(value, str):
            return value

        normalized = value.strip()
        return normalized or None

    @field_validator("quantity")
    @classmethod
    def require_positive_quantity(cls, value: float | None) -> float | None:
        if value is not None and value <= 0:
            raise ValueError("quantity must be greater than zero")
        return value

    @field_validator("certification_requirements", mode="before")
    @classmethod
    def normalize_certification_requirements(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return value

        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                return value

            requirement = item.strip()
            if requirement:
                normalized.append(requirement)

        return normalized


class RFQValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: RFQWorkflowStatus
    missing_fields: list[str] = Field(default_factory=list)
    is_ready_for_supplier_search: bool = False


class WorkflowMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RFQWorkflowState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workflow_id: str
    user_id: str
    company_id: str | None = None
    status: RFQWorkflowStatus = "draft"
    rfq: RFQDraft = Field(default_factory=RFQDraft)
    missing_fields: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    supplier_candidates: list[SupplierCandidate] = Field(default_factory=list)
    recommendation: AwardRecommendation | None = None
    credit_check: CreditCheckResult | None = None
    approval_requests: list[ApprovalRequest] = Field(default_factory=list)
    generated_documents: list[GeneratedDocument] = Field(default_factory=list)
    messages: list[WorkflowMessage] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)
