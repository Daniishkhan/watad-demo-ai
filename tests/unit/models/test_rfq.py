import pytest
from pydantic import ValidationError

from watad.models import RFQDraft


def test_rfq_draft_allows_partial_state() -> None:
    draft = RFQDraft(material_name="rebar")

    assert draft.material_name == "rebar"
    assert draft.quantity is None
    assert draft.certification_requirements == []


def test_rfq_draft_normalizes_blank_strings_and_certifications() -> None:
    draft = RFQDraft(
        material_name="  rebar  ",
        delivery_site="   ",
        certification_requirements=["  Saudi standard  ", ""],
    )

    assert draft.material_name == "rebar"
    assert draft.delivery_site is None
    assert draft.certification_requirements == ["Saudi standard"]


@pytest.mark.parametrize("quantity", [0, -1])
def test_rfq_draft_rejects_non_positive_quantity(quantity: float) -> None:
    with pytest.raises(ValidationError, match="quantity must be greater than zero"):
        RFQDraft(quantity=quantity)


def test_rfq_draft_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        RFQDraft.model_validate({"material_name": "rebar", "supplier_name": "not part of rfq"})


def test_rfq_draft_rejects_unknown_optimization_preference() -> None:
    with pytest.raises(ValidationError):
        RFQDraft.model_validate({"optimization_preference": "cheapest"})
