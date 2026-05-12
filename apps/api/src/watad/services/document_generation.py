from __future__ import annotations

from watad.models import (
    AwardRecommendation,
    CreditCheckResult,
    GeneratedDocument,
    RFQDraft,
    SupplierCandidate,
)


def generate_draft_documents(
    *,
    workflow_id: str,
    rfq: RFQDraft,
    supplier_candidates: list[SupplierCandidate],
    recommendation: AwardRecommendation,
    credit_check: CreditCheckResult | None,
) -> list[GeneratedDocument]:
    return [
        GeneratedDocument(
            document_id=f"DOC-{workflow_id}-RFQ",
            workflow_id=workflow_id,
            document_type="rfq_draft",
            title=f"RFQ Draft - {_project_label(rfq)}",
            content=_rfq_content(rfq),
        ),
        GeneratedDocument(
            document_id=f"DOC-{workflow_id}-OUTREACH",
            workflow_id=workflow_id,
            document_type="supplier_outreach_draft",
            title=f"Supplier Outreach Draft - {_project_label(rfq)}",
            content=_outreach_content(rfq, supplier_candidates),
        ),
        GeneratedDocument(
            document_id=f"DOC-{workflow_id}-MEMO",
            workflow_id=workflow_id,
            document_type="award_recommendation_memo",
            title=f"Award Recommendation Memo - {_project_label(rfq)}",
            content=_recommendation_content(recommendation, credit_check),
        ),
        GeneratedDocument(
            document_id=f"DOC-{workflow_id}-PO",
            workflow_id=workflow_id,
            document_type="po_preview",
            title=f"Draft PO Preview - {_project_label(rfq)}",
            content=_po_preview_content(rfq, recommendation, credit_check),
        ),
    ]


def _rfq_content(rfq: RFQDraft) -> dict[str, object]:
    return {
        "status_label": "Draft - not sent",
        "project_name": rfq.project_name,
        "material": rfq.material_name,
        "specification": rfq.specification,
        "quantity": rfq.quantity,
        "unit": rfq.unit,
        "delivery_city": rfq.delivery_city,
        "delivery_site": rfq.delivery_site,
        "delivery_deadline": rfq.delivery_deadline,
        "payment_preference": rfq.payment_preference,
    }


def _outreach_content(
    rfq: RFQDraft,
    supplier_candidates: list[SupplierCandidate],
) -> dict[str, object]:
    return {
        "status_label": "Draft - approval required before send",
        "supplier_ids": [candidate.supplier_id for candidate in supplier_candidates],
        "message": (
            f"Please quote {rfq.quantity:g} {rfq.unit} of {rfq.specification} "
            f"for delivery to {rfq.delivery_site}, {rfq.delivery_city}."
        )
        if rfq.quantity is not None and rfq.unit is not None
        else "Please quote the attached RFQ requirements.",
    }


def _recommendation_content(
    recommendation: AwardRecommendation,
    credit_check: CreditCheckResult | None,
) -> dict[str, object]:
    return {
        "status_label": "Draft memo",
        "recommended_supplier_id": recommendation.recommended_supplier_id,
        "recommended_supplier_name": recommendation.recommended_supplier_name,
        "reason": recommendation.reason,
        "tradeoffs": recommendation.tradeoffs,
        "credit_status": credit_check.status if credit_check else None,
    }


def _po_preview_content(
    rfq: RFQDraft,
    recommendation: AwardRecommendation,
    credit_check: CreditCheckResult | None,
) -> dict[str, object]:
    return {
        "status_label": "Draft - not issued",
        "project_name": rfq.project_name,
        "supplier_id": recommendation.recommended_supplier_id,
        "supplier_name": recommendation.recommended_supplier_name,
        "estimated_total_price_sar": recommendation.estimated_total_price_sar,
        "payment_terms": rfq.payment_preference,
        "credit_status": credit_check.status if credit_check else None,
        "requires_approval_before_issue": True,
    }


def _project_label(rfq: RFQDraft) -> str:
    return rfq.project_name or "Unnamed Project"
