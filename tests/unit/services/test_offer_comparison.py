from watad.models import RFQDraft, SupplierCandidate
from watad.services.offer_comparison import rank_award_options


def test_rank_award_options_recommends_best_fit_and_explains_tradeoffs() -> None:
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
    candidates = [
        _candidate(
            supplier_id="SUP-002",
            supplier_name="Riyadh Metals",
            fit_score=0.94,
            unit_price_sar=2360,
            delivery_days=8,
            payment_terms=["30_days", "60_days"],
            risks=["delivery may miss requested deadline"],
        ),
        _candidate(
            supplier_id="SUP-001",
            supplier_name="Al Noor Steel",
            fit_score=0.91,
            unit_price_sar=2410,
            delivery_days=6,
            payment_terms=["30_days"],
            risks=["payment terms do not match preference"],
        ),
        _candidate(
            supplier_id="SUP-003",
            supplier_name="GulfBuild Supply",
            fit_score=0.82,
            unit_price_sar=2320,
            available_quantity=300,
            delivery_days=7,
            payment_terms=["upfront"],
            risks=["requires split delivery", "payment terms do not match preference"],
        ),
    ]

    recommendation = rank_award_options(rfq, candidates)

    assert recommendation is not None
    assert recommendation.recommended_supplier_id == "SUP-002"
    assert recommendation.recommended_supplier_name == "Riyadh Metals"
    assert recommendation.optimization_goal == "lowest_price"
    assert recommendation.estimated_total_price_sar == 1_180_000
    assert "Not the lowest unit price" in recommendation.tradeoffs
    assert "Delivery is slower than the fastest option" in recommendation.tradeoffs
    assert [alternative.supplier_id for alternative in recommendation.alternatives] == [
        "SUP-001",
        "SUP-003",
    ]


def test_rank_award_options_returns_none_without_candidates() -> None:
    recommendation = rank_award_options(RFQDraft(quantity=500), [])

    assert recommendation is None


def _candidate(
    *,
    supplier_id: str,
    supplier_name: str,
    fit_score: float,
    unit_price_sar: float,
    delivery_days: int,
    payment_terms: list[str],
    risks: list[str],
    available_quantity: float = 500,
) -> SupplierCandidate:
    return SupplierCandidate(
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        fit_score=fit_score,
        unit_price_sar=unit_price_sar,
        available_quantity=available_quantity,
        delivery_days=delivery_days,
        payment_terms=payment_terms,
        reliability_score=0.9,
        strengths=[],
        risks=risks,
        total_price_sar=unit_price_sar * available_quantity,
    )
