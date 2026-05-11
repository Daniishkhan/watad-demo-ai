from __future__ import annotations

from typing import Final

from watad.models import RFQDraft, RFQValidationResult

_FIELD_QUESTION_LABELS: Final[dict[str, str]] = {
    "material_category": "the material category",
    "material_name": "the material item",
    "specification": "the material specification",
    "quantity": "the quantity",
    "unit": "the unit",
    "delivery_city": "the delivery city",
    "delivery_site": "the exact delivery site or district",
    "delivery_deadline": "the delivery deadline",
    "project_name": "the project name",
    "company_id": "the buyer or company identity",
    "certification_requirements": "any certification or approved-brand requirements",
    "split_delivery_acceptable": "whether split delivery is acceptable",
}
_READINESS_FIELDS: Final[tuple[str, ...]] = (
    "material_category",
    "material_name",
    "specification",
    "quantity",
    "unit",
    "delivery_city",
    "delivery_site",
    "delivery_deadline",
    "project_name",
    "certification_requirements",
    "split_delivery_acceptable",
)


def validate_rfq(rfq: RFQDraft, *, company_id: str | None) -> RFQValidationResult:
    missing_fields: list[str] = []

    for field_name in _READINESS_FIELDS:
        value = getattr(rfq, field_name)
        if _is_missing(value):
            missing_fields.append(field_name)

    if company_id is None:
        missing_fields.append("company_id")

    is_ready = not missing_fields
    return RFQValidationResult(
        status="ready_for_supplier_search" if is_ready else "needs_clarification",
        missing_fields=missing_fields,
        is_ready_for_supplier_search=is_ready,
    )


def generate_clarifying_question(missing_fields: list[str]) -> str:
    labels = [
        _FIELD_QUESTION_LABELS[field] for field in missing_fields if field in _FIELD_QUESTION_LABELS
    ]
    if not labels:
        return "I can continue once the missing RFQ details are provided."

    if labels == [
        "the exact delivery site or district",
        "the project name",
        "any certification or approved-brand requirements",
        "whether split delivery is acceptable",
    ]:
        return (
            "I can create this RFQ. I need four details first: the exact delivery site "
            "or district, the project name, any certification or approved-brand "
            "requirements, and whether split delivery is acceptable."
        )

    return f"I can create this RFQ. I need {len(labels)} detail(s) first: {_join_labels(labels)}."


def _is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return not value

    return False


def _join_labels(labels: list[str]) -> str:
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"

    return f"{', '.join(labels[:-1])}, and {labels[-1]}"
