from __future__ import annotations

from watad.models import AwardAlternative, AwardRecommendation, RFQDraft, SupplierCandidate


def rank_award_options(
    rfq: RFQDraft,
    supplier_candidates: list[SupplierCandidate],
) -> AwardRecommendation | None:
    if not supplier_candidates:
        return None

    ranked_candidates = sorted(
        supplier_candidates,
        key=lambda candidate: (-candidate.fit_score, candidate.unit_price_sar),
    )
    recommended = ranked_candidates[0]
    alternatives = [
        AwardAlternative(
            supplier_id=candidate.supplier_id,
            supplier_name=candidate.supplier_name,
            reason=_alternative_reason(candidate, recommended, rfq),
        )
        for candidate in ranked_candidates[1:]
    ]
    optimization_goal = rfq.optimization_preference or "balanced"

    return AwardRecommendation(
        recommended_supplier_id=recommended.supplier_id,
        recommended_supplier_name=recommended.supplier_name,
        optimization_goal=optimization_goal,
        reason=_recommendation_reason(recommended, optimization_goal),
        estimated_total_price_sar=_estimated_total_price(recommended, rfq),
        tradeoffs=_tradeoffs(recommended, ranked_candidates, rfq),
        alternatives=alternatives,
    )


def _recommendation_reason(candidate: SupplierCandidate, optimization_goal: str) -> str:
    return (
        f"{candidate.supplier_name} is the strongest {optimization_goal} fit based on "
        "the scored supplier shortlist."
    )


def _alternative_reason(
    candidate: SupplierCandidate,
    recommended: SupplierCandidate,
    rfq: RFQDraft,
) -> str:
    reasons: list[str] = []
    if candidate.unit_price_sar < recommended.unit_price_sar:
        reasons.append("lower unit price")
    if candidate.delivery_days < recommended.delivery_days:
        reasons.append("faster delivery")
    if rfq.payment_preference and rfq.payment_preference in candidate.payment_terms:
        reasons.append("supports requested payment terms")
    if candidate.risks:
        reasons.append(f"risks: {', '.join(candidate.risks)}")

    if not reasons:
        return "Comparable option with a lower overall fit score."

    return f"{candidate.supplier_name} offers {', '.join(reasons)}."


def _tradeoffs(
    recommended: SupplierCandidate,
    candidates: list[SupplierCandidate],
    rfq: RFQDraft,
) -> list[str]:
    tradeoffs: list[str] = []
    lowest_unit_price = min(candidate.unit_price_sar for candidate in candidates)
    fastest_delivery_days = min(candidate.delivery_days for candidate in candidates)

    if recommended.unit_price_sar > lowest_unit_price:
        tradeoffs.append("Not the lowest unit price")
    if recommended.delivery_days > fastest_delivery_days:
        tradeoffs.append("Delivery is slower than the fastest option")
    if rfq.payment_preference and rfq.payment_preference not in recommended.payment_terms:
        tradeoffs.append("Does not support requested payment terms")
    if rfq.quantity is not None and recommended.available_quantity < rfq.quantity:
        tradeoffs.append("Requires split delivery or partial fulfillment")

    for risk in recommended.risks:
        if risk not in tradeoffs:
            tradeoffs.append(risk)

    return tradeoffs


def _estimated_total_price(candidate: SupplierCandidate, rfq: RFQDraft) -> float:
    quantity = rfq.quantity or candidate.available_quantity
    return candidate.unit_price_sar * quantity
