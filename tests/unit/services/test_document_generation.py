from watad.models import (
    AwardRecommendation,
    CreditCheckResult,
    RFQDraft,
    SupplierCandidate,
)
from watad.services.document_generation import generate_draft_documents


def test_generate_draft_documents_marks_outputs_as_drafts_and_approval_gated() -> None:
    documents = generate_draft_documents(
        workflow_id="wf_123",
        rfq=RFQDraft(
            material_category="steel",
            material_name="rebar",
            specification="16mm rebar",
            quantity=500,
            unit="tons",
            delivery_city="Riyadh",
            delivery_site="North Riyadh",
            delivery_deadline="2026-05-18",
            project_name="Al Yasmin Villas",
            payment_preference="60_days",
        ),
        supplier_candidates=[
            SupplierCandidate(
                supplier_id="SUP-002",
                supplier_name="Riyadh Metals",
                fit_score=0.96,
                unit_price_sar=2360,
                available_quantity=500,
                delivery_days=8,
                payment_terms=["30_days", "60_days"],
                reliability_score=0.89,
                strengths=["supports requested payment terms"],
                risks=["delivery may miss requested deadline"],
                total_price_sar=1_180_000,
            )
        ],
        recommendation=AwardRecommendation(
            recommended_supplier_id="SUP-002",
            recommended_supplier_name="Riyadh Metals",
            optimization_goal="lowest_price",
            reason="Best fit",
            estimated_total_price_sar=1_180_000,
        ),
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

    assert [document.document_type for document in documents] == [
        "rfq_draft",
        "supplier_outreach_draft",
        "award_recommendation_memo",
        "po_preview",
    ]
    assert all(document.status == "draft" for document in documents)
    assert all(document.requires_approval_before_send for document in documents)
    assert documents[-1].title == "Draft PO Preview - Al Yasmin Villas"
    assert documents[-1].content["status_label"] == "Draft - not issued"
