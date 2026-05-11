from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

from watad.models import RFQDraft, Supplier, SupplierCandidate

_PROJECT_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_SEED_PATH = _PROJECT_ROOT / "data" / "seed" / "suppliers.csv"
_PAYMENT_TERMS_LABELS: Final[dict[str, str]] = {
    "30_days": "30-day payment terms",
    "60_days": "60-day payment terms",
    "90_days": "90-day payment terms",
    "upfront": "upfront payment",
}


@dataclass(frozen=True)
class SupplierCatalog:
    suppliers: tuple[Supplier, ...]

    @classmethod
    def from_seed_data(cls, path: Path = _DEFAULT_SEED_PATH) -> SupplierCatalog:
        with path.open(newline="") as supplier_file:
            rows = csv.DictReader(supplier_file)
            suppliers = tuple(_supplier_from_row(row) for row in rows)

        return cls(suppliers=suppliers)


def shortlist_suppliers(
    rfq: RFQDraft,
    *,
    catalog: SupplierCatalog,
    today: date | None = None,
    limit: int = 3,
) -> list[SupplierCandidate]:
    eligible_suppliers = [
        _evaluate_supplier(supplier, rfq, today=today) for supplier in catalog.suppliers
    ]
    candidates = [candidate for candidate in eligible_suppliers if candidate is not None]
    return sorted(
        candidates,
        key=lambda candidate: (-candidate.fit_score, candidate.unit_price_sar),
    )[:limit]


def _supplier_from_row(row: dict[str, str]) -> Supplier:
    return Supplier(
        supplier_id=row["supplier_id"],
        name=row["name"],
        cities_served=_split_cell(row["cities_served"]),
        material_categories=_split_cell(row["material_categories"]),
        certifications=_split_cell(row["certifications"]),
        reliability_score=float(row["reliability_score"]),
        payment_terms_supported=_split_cell(row["payment_terms_supported"]),
        average_delivery_days=int(row["average_delivery_days"]),
        max_quantity_tons=float(row["max_quantity_tons"]),
        base_unit_price_sar=float(row["base_unit_price_sar"]),
        split_delivery_supported=row["split_delivery_supported"].lower() == "true",
    )


def _split_cell(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


def _evaluate_supplier(
    supplier: Supplier,
    rfq: RFQDraft,
    *,
    today: date | None,
) -> SupplierCandidate | None:
    if rfq.material_category is None or rfq.delivery_city is None or rfq.quantity is None:
        return None
    if rfq.material_category not in _lowered(supplier.material_categories):
        return None
    if rfq.delivery_city.lower() not in _lowered(supplier.cities_served):
        return None
    if not _supports_required_certifications(supplier, rfq.certification_requirements):
        return None

    available_quantity = min(rfq.quantity, supplier.max_quantity_tons)
    full_quantity_available = supplier.max_quantity_tons >= rfq.quantity
    if not full_quantity_available and not (
        supplier.split_delivery_supported and rfq.split_delivery_acceptable is True
    ):
        return None

    strengths = _supplier_strengths(supplier, rfq, full_quantity_available)
    risks = _supplier_risks(supplier, rfq, full_quantity_available, today=today)
    fit_score = _score_supplier(
        supplier,
        rfq,
        full_quantity_available=full_quantity_available,
        today=today,
    )

    return SupplierCandidate(
        supplier_id=supplier.supplier_id,
        supplier_name=supplier.name,
        fit_score=fit_score,
        unit_price_sar=supplier.base_unit_price_sar,
        available_quantity=available_quantity,
        delivery_days=supplier.average_delivery_days,
        payment_terms=supplier.payment_terms_supported,
        reliability_score=supplier.reliability_score,
        strengths=strengths,
        risks=risks,
        total_price_sar=supplier.base_unit_price_sar * available_quantity,
    )


def _supports_required_certifications(
    supplier: Supplier,
    required_certifications: list[str],
) -> bool:
    supplier_certifications = _lowered(supplier.certifications)
    return all(
        certification.lower() in supplier_certifications
        for certification in required_certifications
    )


def _supplier_strengths(
    supplier: Supplier,
    rfq: RFQDraft,
    full_quantity_available: bool,
) -> list[str]:
    strengths: list[str] = []
    if rfq.payment_preference and rfq.payment_preference in supplier.payment_terms_supported:
        strengths.append("supports requested payment terms")
    if full_quantity_available:
        strengths.append("full quantity available")
    if supplier.average_delivery_days <= 7:
        strengths.append("fast delivery window")
    if supplier.reliability_score >= 0.9:
        strengths.append("high reliability")

    return strengths


def _supplier_risks(
    supplier: Supplier,
    rfq: RFQDraft,
    full_quantity_available: bool,
    *,
    today: date | None,
) -> list[str]:
    risks: list[str] = []
    if not full_quantity_available:
        risks.append("requires split delivery")
    if rfq.payment_preference and rfq.payment_preference not in supplier.payment_terms_supported:
        risks.append("payment terms do not match preference")
    if _delivery_days_until_deadline(rfq, today=today) < supplier.average_delivery_days:
        risks.append("delivery may miss requested deadline")

    return risks


def _score_supplier(
    supplier: Supplier,
    rfq: RFQDraft,
    *,
    full_quantity_available: bool,
    today: date | None,
) -> float:
    price_score = _price_score(supplier.base_unit_price_sar)
    delivery_score = _delivery_score(supplier, rfq, today=today)
    availability_score = 1.0 if full_quantity_available else 0.55
    payment_score = _payment_score(supplier, rfq)
    reliability_score = supplier.reliability_score
    weights = _weights_for_goal(rfq.optimization_preference)

    score = (
        weights.price * price_score
        + weights.delivery * delivery_score
        + weights.availability * availability_score
        + weights.payment * payment_score
        + weights.reliability * reliability_score
    )
    return round(score, 4)


def _price_score(unit_price_sar: float) -> float:
    market_reference = 2450
    return min(1.0, market_reference / unit_price_sar)


def _delivery_score(supplier: Supplier, rfq: RFQDraft, *, today: date | None) -> float:
    days_until_deadline = _delivery_days_until_deadline(rfq, today=today)
    if days_until_deadline <= 0:
        return 0.5
    if supplier.average_delivery_days <= days_until_deadline:
        return 1.0

    lateness = supplier.average_delivery_days - days_until_deadline
    return max(0.4, 1 - (lateness * 0.15))


def _payment_score(supplier: Supplier, rfq: RFQDraft) -> float:
    if rfq.payment_preference is None:
        return 0.7
    if rfq.payment_preference in supplier.payment_terms_supported:
        return 1.0
    if rfq.payment_preference == "deferred_payment" and any(
        term.endswith("_days") for term in supplier.payment_terms_supported
    ):
        return 0.85

    return 0.25


def _delivery_days_until_deadline(rfq: RFQDraft, *, today: date | None) -> int:
    if rfq.delivery_deadline is None or today is None:
        return 999

    deadline = date.fromisoformat(rfq.delivery_deadline)
    return (deadline - today).days


@dataclass(frozen=True)
class _SupplierScoreWeights:
    price: float
    delivery: float
    availability: float
    payment: float
    reliability: float


def _weights_for_goal(goal: str | None) -> _SupplierScoreWeights:
    if goal == "fastest_delivery":
        return _SupplierScoreWeights(
            price=0.2,
            delivery=0.4,
            availability=0.15,
            payment=0.15,
            reliability=0.1,
        )
    if goal == "payment_terms":
        return _SupplierScoreWeights(
            price=0.2,
            delivery=0.15,
            availability=0.15,
            payment=0.4,
            reliability=0.1,
        )
    if goal == "lowest_price":
        return _SupplierScoreWeights(
            price=0.45,
            delivery=0.15,
            availability=0.15,
            payment=0.15,
            reliability=0.1,
        )

    return _SupplierScoreWeights(
        price=0.3,
        delivery=0.25,
        availability=0.2,
        payment=0.15,
        reliability=0.1,
    )


def _lowered(values: Iterable[str]) -> set[str]:
    return {value.lower() for value in values}


def describe_payment_terms(payment_terms: list[str]) -> list[str]:
    return [_PAYMENT_TERMS_LABELS.get(term, term) for term in payment_terms]
