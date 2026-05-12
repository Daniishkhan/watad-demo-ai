from __future__ import annotations

from datetime import UTC, datetime

from watad.models import ApprovalAction, ApprovalRequest, CreditCheckResult


def create_approval_request(
    *,
    workflow_id: str,
    credit_check: CreditCheckResult | None,
) -> ApprovalRequest:
    if credit_check is not None and credit_check.finance_approval_required:
        return ApprovalRequest(
            approval_id=f"APR-{workflow_id}-FINANCE",
            workflow_id=workflow_id,
            action="finance_review",
            approver_role="finance_reviewer",
            message="Finance approval is required before deferred payment terms can proceed.",
        )

    return ApprovalRequest(
        approval_id=f"APR-{workflow_id}-OUTREACH",
        workflow_id=workflow_id,
        action="send_rfq_to_suppliers",
        approver_role="procurement_manager",
        message="Procurement manager approval is required before supplier outreach.",
    )


def record_approval_decision(
    approval: ApprovalRequest,
    *,
    decision: str,
    decided_by: str,
) -> ApprovalRequest:
    if approval.status != "pending":
        raise ValueError("approval request has already been decided")
    if decision not in {"approved", "rejected"}:
        raise ValueError("decision must be approved or rejected")

    return approval.model_copy(
        update={
            "status": decision,
            "decided_by": decided_by,
            "decided_at": datetime.now(UTC),
        }
    )


def find_pending_approval(
    approvals: list[ApprovalRequest],
    *,
    action: ApprovalAction,
) -> ApprovalRequest:
    for approval in approvals:
        if approval.action == action and approval.status == "pending":
            return approval

    raise KeyError(action)
