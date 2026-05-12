from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type ApprovalAction = Literal[
    "finance_review",
    "send_rfq_to_suppliers",
    "issue_purchase_order",
]
type ApprovalStatus = Literal["pending", "approved", "rejected"]


class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str
    workflow_id: str
    action: ApprovalAction
    approver_role: str
    status: ApprovalStatus = "pending"
    message: str
    decided_by: str | None = None
    decided_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
