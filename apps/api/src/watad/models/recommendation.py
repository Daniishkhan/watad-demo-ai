from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AwardAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    supplier_id: str
    supplier_name: str
    reason: str


class AwardRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_supplier_id: str
    recommended_supplier_name: str
    optimization_goal: str
    reason: str
    estimated_total_price_sar: float
    tradeoffs: list[str] = Field(default_factory=list)
    alternatives: list[AwardAlternative] = Field(default_factory=list)
