from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from watad.models import AwardRecommendation, BuyerCreditProfile, CreditCheckResult, RFQDraft

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_BUYER_PROFILES_PATH = _PROJECT_ROOT / "data" / "seed" / "buyer_profiles.csv"
_AUTO_APPROVAL_THRESHOLD_SAR: Final[float] = 500_000
_REVIEW_REQUIRED_TERMS: Final[set[str]] = {"60_days", "90_days", "deferred_payment"}
_REQUIRED_DEFERRED_DOCUMENTS: Final[set[str]] = {
    "latest_bank_statement",
    "signed_project_contract",
}
_DOCUMENT_ACTIONS: Final[dict[str, str]] = {
    "latest_bank_statement": "collect_latest_bank_statement",
    "signed_project_contract": "collect_signed_project_contract",
}
_DOCUMENT_LABELS: Final[dict[str, str]] = {
    "latest_bank_statement": "latest bank statement",
    "signed_project_contract": "signed project contract",
}


@dataclass(frozen=True)
class BuyerProfileStore:
    profiles: dict[str, BuyerCreditProfile]

    @classmethod
    def from_seed_data(cls, path: Path = _DEFAULT_BUYER_PROFILES_PATH) -> BuyerProfileStore:
        with path.open(newline="") as profiles_file:
            rows = csv.DictReader(profiles_file)
            profiles = {_profile_from_row(row).company_id: _profile_from_row(row) for row in rows}

        return cls(profiles=profiles)

    def get(self, company_id: str) -> BuyerCreditProfile | None:
        return self.profiles.get(company_id)


def check_credit_policy(
    *,
    rfq: RFQDraft,
    recommendation: AwardRecommendation,
    company_id: str | None,
    buyer_profiles: BuyerProfileStore,
) -> CreditCheckResult:
    estimated_order_value = recommendation.estimated_total_price_sar
    requested_terms = rfq.payment_preference
    if company_id is None:
        return CreditCheckResult(
            status="missing_information",
            estimated_order_value_sar=estimated_order_value,
            requested_terms=requested_terms,
            credit_limit_sar=None,
            current_utilization_sar=None,
            reason_codes=["company_id_missing"],
            required_actions=["collect_buyer_identity"],
        )

    profile = buyer_profiles.get(company_id)
    if profile is None:
        return CreditCheckResult(
            status="missing_information",
            estimated_order_value_sar=estimated_order_value,
            requested_terms=requested_terms,
            credit_limit_sar=None,
            current_utilization_sar=None,
            reason_codes=["buyer_profile_not_found"],
            required_actions=["collect_buyer_credit_profile"],
        )

    projected_utilization = profile.current_utilization_sar + estimated_order_value
    if projected_utilization > profile.credit_limit_sar:
        return CreditCheckResult(
            status="not_eligible",
            estimated_order_value_sar=estimated_order_value,
            requested_terms=requested_terms,
            credit_limit_sar=profile.credit_limit_sar,
            current_utilization_sar=profile.current_utilization_sar,
            reason_codes=["projected_utilization_exceeds_credit_limit"],
            required_actions=["request_payment_terms_revision_or_credit_limit_review"],
        )

    reason_codes: list[str] = []
    required_actions: list[str] = []
    missing_documents: list[str] = []

    if requested_terms in _REVIEW_REQUIRED_TERMS:
        reason_codes.append("requested_deferred_terms_require_review")
        required_actions.append("route_to_finance_reviewer")
    if estimated_order_value > _AUTO_APPROVAL_THRESHOLD_SAR:
        reason_codes.append("order_value_exceeds_auto_approval_threshold")
        if "route_to_finance_reviewer" not in required_actions:
            required_actions.append("route_to_finance_reviewer")
    if profile.payment_history_status == "overdue":
        reason_codes.append("payment_history_overdue")
        if "route_to_finance_reviewer" not in required_actions:
            required_actions.append("route_to_finance_reviewer")

    documents_needed = _missing_documents(profile, requested_terms)
    if documents_needed:
        reason_codes.append("missing_credit_documents")
        missing_documents = [_DOCUMENT_LABELS[document] for document in documents_needed]
        required_actions.extend(_DOCUMENT_ACTIONS[document] for document in documents_needed)

    if required_actions:
        return CreditCheckResult(
            status="finance_approval_required",
            estimated_order_value_sar=estimated_order_value,
            requested_terms=requested_terms,
            credit_limit_sar=profile.credit_limit_sar,
            current_utilization_sar=profile.current_utilization_sar,
            finance_approval_required=True,
            reason_codes=reason_codes,
            required_actions=required_actions,
            missing_documents=missing_documents,
        )

    return CreditCheckResult(
        status="eligible",
        estimated_order_value_sar=estimated_order_value,
        requested_terms=requested_terms,
        credit_limit_sar=profile.credit_limit_sar,
        current_utilization_sar=profile.current_utilization_sar,
        finance_approval_required=False,
        reason_codes=["within_credit_policy"],
        required_actions=[],
    )


def _profile_from_row(row: dict[str, str]) -> BuyerCreditProfile:
    return BuyerCreditProfile(
        company_id=row["company_id"],
        company_name=row["company_name"],
        credit_limit_sar=float(row["credit_limit_sar"]),
        current_utilization_sar=float(row["current_utilization_sar"]),
        payment_history_status=row["payment_history_status"],  # type: ignore[arg-type]
        documents_on_file=_split_cell(row["documents_on_file"]),
    )


def _split_cell(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def _missing_documents(profile: BuyerCreditProfile, requested_terms: str | None) -> list[str]:
    if requested_terms not in _REVIEW_REQUIRED_TERMS:
        return []

    documents_on_file = set(profile.documents_on_file)
    return sorted(_REQUIRED_DEFERRED_DOCUMENTS - documents_on_file)
