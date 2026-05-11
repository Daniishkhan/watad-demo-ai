from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Supplier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: str
    name: str
    cities_served: list[str]
    material_categories: list[str]
    certifications: list[str]
    reliability_score: float
    payment_terms_supported: list[str]
    average_delivery_days: int
    max_quantity_tons: float
    base_unit_price_sar: float
    split_delivery_supported: bool = False

    @field_validator("reliability_score")
    @classmethod
    def validate_reliability_score(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("reliability_score must be between 0 and 1")
        return value


class SupplierCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: str
    supplier_name: str
    fit_score: float
    unit_price_sar: float
    available_quantity: float
    delivery_days: int
    payment_terms: list[str]
    reliability_score: float
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    total_price_sar: float
