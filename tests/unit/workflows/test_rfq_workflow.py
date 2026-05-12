from datetime import date

from watad.workflows.rfq import RFQWorkflowService


def test_workflow_service_exposes_langgraph_node_order() -> None:
    service = RFQWorkflowService(today=lambda: date(2026, 5, 11))

    assert service.graph_node_names == (
        "intake_node",
        "rfq_validation_node",
        "supplier_matching_node",
        "offer_comparison_node",
        "credit_eligibility_node",
    )


def test_start_workflow_returns_structured_rfq_and_clarification() -> None:
    service = RFQWorkflowService(today=lambda: date(2026, 5, 11))

    state = service.start(
        message="Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, "
        "60-day payment preferred.",
        user_id="user_123",
        company_id="company_456",
    )

    assert state.workflow_id.startswith("wf_")
    assert state.status == "needs_clarification"
    assert state.rfq.material_name == "rebar"
    assert state.rfq.quantity == 500
    assert state.rfq.delivery_deadline == "2026-05-18"
    assert state.missing_fields == [
        "delivery_site",
        "project_name",
        "certification_requirements",
        "split_delivery_acceptable",
    ]
    assert state.questions == [
        "I can create this RFQ. I need four details first: the exact delivery site "
        "or district, the project name, any certification or approved-brand "
        "requirements, and whether split delivery is acceptable."
    ]
    assert [event.event_type for event in state.audit_events] == [
        "workflow_started",
        "intake_parsed",
        "rfq_validated",
    ]


def test_continue_workflow_merges_answers_and_reaches_recommendation_state() -> None:
    service = RFQWorkflowService(today=lambda: date(2026, 5, 11))
    state = service.start(
        message="Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, "
        "60-day payment preferred.",
        user_id="user_123",
        company_id="company_456",
    )

    resumed = service.add_message(
        workflow_id=state.workflow_id,
        message=(
            "Project Al Yasmin Villas, north Riyadh. Saudi standard is fine. "
            "Split delivery is okay if cheaper."
        ),
    )

    assert resumed.status == "finance_approval_required"
    assert resumed.rfq.project_name == "Al Yasmin Villas"
    assert resumed.rfq.delivery_site == "North Riyadh"
    assert resumed.rfq.certification_requirements == ["Saudi standard"]
    assert resumed.rfq.split_delivery_acceptable is True
    assert resumed.missing_fields == []
    assert resumed.questions == []
    assert [candidate.supplier_id for candidate in resumed.supplier_candidates] == [
        "SUP-002",
        "SUP-001",
        "SUP-003",
    ]
    assert resumed.recommendation is not None
    assert resumed.recommendation.recommended_supplier_id == "SUP-002"
    assert resumed.credit_check is not None
    assert resumed.credit_check.status == "finance_approval_required"
    assert resumed.credit_check.estimated_order_value_sar == 1_180_000
    assert [event.event_type for event in resumed.audit_events][-6:] == [
        "user_message_received",
        "intake_parsed",
        "rfq_validated",
        "supplier_matching_completed",
        "offer_comparison_completed",
        "credit_eligibility_completed",
    ]


def test_get_workflow_raises_key_error_for_unknown_id() -> None:
    service = RFQWorkflowService(today=lambda: date(2026, 5, 11))

    try:
        service.get("wf_missing")
    except KeyError as error:
        assert str(error) == "'wf_missing'"
    else:
        raise AssertionError("Expected KeyError")
