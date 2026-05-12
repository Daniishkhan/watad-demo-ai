from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

type CreditCheckStatus = Literal[
    "eligible",
    "conditionally_eligible",
    "finance_approval_required",
    "not_eligible",
    "missing_information",
]


class BuyerCreditProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    company_name: str
    credit_limit_sar: float
    current_utilization_sar: float
    payment_history_status: Literal["current", "overdue"]
    documents_on_file: list[str] = Field(default_factory=list)

    @field_validator("credit_limit_sar", "current_utilization_sar")
    @classmethod
    def require_non_negative_amount(cls, value: float) -> float:
        if value < 0:
            raise ValueError("credit amounts must be non-negative")
        return value


class CreditCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: CreditCheckStatus
    estimated_order_value_sar: float
    requested_terms: str | None
    credit_limit_sar: float | None
    current_utilization_sar: float | None
    finance_approval_required: bool = False
    reason_codes: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
