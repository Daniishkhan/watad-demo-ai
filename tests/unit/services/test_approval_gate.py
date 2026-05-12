from watad.models import CreditCheckResult
from watad.services.approval_gate import create_approval_request, record_approval_decision


def test_create_approval_request_routes_finance_review_when_credit_requires_it() -> None:
    approval = create_approval_request(
        workflow_id="wf_123",
        credit_check=CreditCheckResult(
            status="finance_approval_required",
            estimated_order_value_sar=1_180_000,
            requested_terms="60_days",
            credit_limit_sar=2_000_000,
            current_utilization_sar=450_000,
            finance_approval_required=True,
            reason_codes=["requested_deferred_terms_require_review"],
            required_actions=["route_to_finance_reviewer"],
        ),
    )

    assert approval.action == "finance_review"
    assert approval.approver_role == "finance_reviewer"
    assert approval.status == "pending"
    assert "Finance approval is required" in approval.message


def test_create_approval_request_routes_supplier_outreach_when_credit_is_clear() -> None:
    approval = create_approval_request(
        workflow_id="wf_123",
        credit_check=CreditCheckResult(
            status="eligible",
            estimated_order_value_sar=250_000,
            requested_terms="30_days",
            credit_limit_sar=2_000_000,
            current_utilization_sar=450_000,
            finance_approval_required=False,
            reason_codes=["within_credit_policy"],
            required_actions=[],
        ),
    )

    assert approval.action == "send_rfq_to_suppliers"
    assert approval.approver_role == "procurement_manager"
    assert approval.status == "pending"


def test_record_approval_decision_updates_pending_request() -> None:
    approval = create_approval_request(
        workflow_id="wf_123",
        credit_check=CreditCheckResult(
            status="eligible",
            estimated_order_value_sar=250_000,
            requested_terms="30_days",
            credit_limit_sar=2_000_000,
            current_utilization_sar=450_000,
            finance_approval_required=False,
            reason_codes=["within_credit_policy"],
            required_actions=[],
        ),
    )

    decided = record_approval_decision(
        approval,
        decision="approved",
        decided_by="user_123",
    )

    assert decided.status == "approved"
    assert decided.decided_by == "user_123"
    assert decided.decided_at is not None
