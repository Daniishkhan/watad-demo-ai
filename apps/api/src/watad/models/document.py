from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

type GeneratedDocumentType = Literal[
    "rfq_draft",
    "supplier_outreach_draft",
    "award_recommendation_memo",
    "po_preview",
]
type GeneratedDocumentStatus = Literal["draft", "pending_approval", "approved"]


class GeneratedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    workflow_id: str
    document_type: GeneratedDocumentType
    title: str
    status: GeneratedDocumentStatus = "draft"
    requires_approval_before_send: bool = True
    content: dict[str, object] = Field(default_factory=dict)
