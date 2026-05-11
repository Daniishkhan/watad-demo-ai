from datetime import date

from watad.models import RFQDraft
from watad.services.supplier_matching import SupplierCatalog, shortlist_suppliers


def test_shortlist_suppliers_filters_to_catalog_matches_and_explains_risks() -> None:
    rfq = RFQDraft(
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
        optimization_preference="lowest_price",
        certification_requirements=["Saudi standard"],
        split_delivery_acceptable=True,
    )

    candidates = shortlist_suppliers(
        rfq,
        catalog=SupplierCatalog.from_seed_data(),
        today=date(2026, 5, 11),
    )

    assert [candidate.supplier_id for candidate in candidates] == ["SUP-002", "SUP-001", "SUP-003"]
    assert {candidate.supplier_name for candidate in candidates} == {
        "Riyadh Metals",
        "Al Noor Steel",
        "GulfBuild Supply",
    }
    assert all(candidate.fit_score > 0 for candidate in candidates)
    assert candidates[0].strengths == [
        "supports requested payment terms",
        "full quantity available",
    ]
    assert "requires split delivery" in candidates[2].risks
    assert "payment terms do not match preference" in candidates[2].risks


def test_shortlist_suppliers_does_not_include_partial_capacity_without_split_delivery() -> None:
    rfq = RFQDraft(
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
        split_delivery_acceptable=False,
    )

    candidates = shortlist_suppliers(
        rfq,
        catalog=SupplierCatalog.from_seed_data(),
        today=date(2026, 5, 11),
    )

    assert [candidate.supplier_id for candidate in candidates] == ["SUP-002", "SUP-001"]


def test_shortlist_suppliers_returns_no_candidates_when_catalog_has_no_match() -> None:
    rfq = RFQDraft(
        material_category="cement",
        material_name="white cement",
        specification="white cement",
        quantity=100,
        unit="tons",
        delivery_city="Tabuk",
        delivery_site="Tabuk Site",
        delivery_deadline="2026-05-18",
        project_name="Remote Site",
        certification_requirements=["Saudi standard"],
        split_delivery_acceptable=True,
    )

    candidates = shortlist_suppliers(
        rfq,
        catalog=SupplierCatalog.from_seed_data(),
        today=date(2026, 5, 11),
    )

    assert candidates == []
