from datetime import date

from watad.services.intake import parse_procurement_message


def test_parse_procurement_message_extracts_demo_request_fields() -> None:
    rfq = parse_procurement_message(
        "Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, "
        "60-day payment preferred.",
        today=date(2026, 5, 11),
    )

    assert rfq.material_category == "steel"
    assert rfq.material_name == "rebar"
    assert rfq.specification == "16mm rebar"
    assert rfq.quantity == 500
    assert rfq.unit == "tons"
    assert rfq.delivery_city == "Riyadh"
    assert rfq.delivery_site is None
    assert rfq.delivery_deadline == "2026-05-18"
    assert rfq.optimization_preference == "lowest_price"
    assert rfq.payment_preference == "60_days"


def test_parse_procurement_message_extracts_clarification_answers() -> None:
    rfq = parse_procurement_message(
        "Project Al Yasmin Villas, north Riyadh. Saudi standard is fine. "
        "Split delivery is okay if cheaper.",
        today=date(2026, 5, 11),
    )

    assert rfq.project_name == "Al Yasmin Villas"
    assert rfq.delivery_site == "North Riyadh"
    assert rfq.delivery_district == "North Riyadh"
    assert rfq.certification_requirements == ["Saudi standard"]
    assert rfq.split_delivery_acceptable is True


def test_parse_procurement_message_preserves_unclear_payment_as_deferred_preference() -> None:
    rfq = parse_procurement_message(
        "Need 500 tons rebar in Riyadh next week, pay later if possible.",
        today=date(2026, 5, 11),
    )

    assert rfq.payment_preference == "deferred_payment"
