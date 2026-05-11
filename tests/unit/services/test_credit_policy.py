from watad.models import AwardRecommendation, RFQDraft
from watad.services.credit_policy import BuyerProfileStore, check_credit_policy


def test_check_credit_policy_requires_finance_for_demo_deferred_payment() -> None:
    result = check_credit_policy(
        rfq=RFQDraft(payment_preference="60_days"),
        recommendation=AwardRecommendation(
            recommended_supplier_id="SUP-002",
            recommended_supplier_name="Riyadh Metals",
            optimization_goal="lowest_price",
            reason="Best fit",
            estimated_total_price_sar=1_180_000,
        ),
        company_id="company_456",
        buyer_profiles=BuyerProfileStore.from_seed_data(),
    )

    assert result.status == "finance_approval_required"
    assert result.finance_approval_required is True
    assert result.estimated_order_value_sar == 1_180_000
    assert result.requested_terms == "60_days"
    assert result.credit_limit_sar == 2_000_000
    assert result.current_utilization_sar == 450_000
    assert result.reason_codes == [
        "requested_deferred_terms_require_review",
        "order_value_exceeds_auto_approval_threshold",
        "missing_credit_documents",
    ]
    assert result.required_actions == [
        "route_to_finance_reviewer",
        "collect_latest_bank_statement",
        "collect_signed_project_contract",
    ]


def test_check_credit_policy_returns_missing_information_for_unknown_company() -> None:
    result = check_credit_policy(
        rfq=RFQDraft(payment_preference="30_days"),
        recommendation=AwardRecommendation(
            recommended_supplier_id="SUP-001",
            recommended_supplier_name="Al Noor Steel",
            optimization_goal="balanced",
            reason="Best fit",
            estimated_total_price_sar=250_000,
        ),
        company_id="missing_company",
        buyer_profiles=BuyerProfileStore.from_seed_data(),
    )

    assert result.status == "missing_information"
    assert result.finance_approval_required is False
    assert result.reason_codes == ["buyer_profile_not_found"]
    assert result.required_actions == ["collect_buyer_credit_profile"]


def test_check_credit_policy_rejects_projected_utilization_over_limit() -> None:
    result = check_credit_policy(
        rfq=RFQDraft(payment_preference="30_days"),
        recommendation=AwardRecommendation(
            recommended_supplier_id="SUP-001",
            recommended_supplier_name="Al Noor Steel",
            optimization_goal="balanced",
            reason="Best fit",
            estimated_total_price_sar=250_000,
        ),
        company_id="company_near_limit",
        buyer_profiles=BuyerProfileStore.from_seed_data(),
    )

    assert result.status == "not_eligible"
    assert result.finance_approval_required is False
    assert result.reason_codes == ["projected_utilization_exceeds_credit_limit"]
    assert result.required_actions == ["request_payment_terms_revision_or_credit_limit_review"]
