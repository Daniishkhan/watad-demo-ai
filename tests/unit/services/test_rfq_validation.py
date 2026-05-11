from watad.models import RFQDraft
from watad.services.rfq_validation import generate_clarifying_question, validate_rfq


def test_validate_rfq_marks_city_only_delivery_as_missing_site() -> None:
    result = validate_rfq(
        RFQDraft(
            material_category="steel",
            material_name="rebar",
            specification="16mm rebar",
            quantity=500,
            unit="tons",
            delivery_city="Riyadh",
            delivery_deadline="2026-05-18",
            payment_preference="60_days",
        ),
        company_id="company_123",
    )

    assert result.status == "needs_clarification"
    assert result.is_ready_for_supplier_search is False
    assert result.missing_fields == [
        "delivery_site",
        "project_name",
        "certification_requirements",
        "split_delivery_acceptable",
    ]


def test_validate_rfq_is_ready_when_required_and_demo_fields_are_present() -> None:
    result = validate_rfq(
        RFQDraft(
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
            certification_requirements=["Saudi standard"],
            split_delivery_acceptable=True,
        ),
        company_id="company_123",
    )

    assert result.status == "ready_for_supplier_search"
    assert result.is_ready_for_supplier_search is True
    assert result.missing_fields == []


def test_generate_clarifying_question_groups_missing_fields_without_guessing() -> None:
    question = generate_clarifying_question(
        [
            "delivery_site",
            "project_name",
            "certification_requirements",
            "split_delivery_acceptable",
        ]
    )

    assert "exact delivery site" in question
    assert "project name" in question
    assert "certification" in question
    assert "split delivery" in question
