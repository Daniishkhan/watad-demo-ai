from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from watad.models import (
    ApprovalAction,
    AwardRecommendation,
    CreditCheckResult,
    GeneratedDocument,
    RFQDraft,
    RFQValidationResult,
    RFQWorkflowState,
    SupplierCandidate,
)
from watad.services.credit_policy import BuyerProfileStore, check_credit_policy
from watad.services.offer_comparison import rank_award_options
from watad.services.rfq_validation import validate_rfq
from watad.services.supplier_matching import SupplierCatalog, shortlist_suppliers
from watad.workflows.rfq import RFQWorkflowService

app = FastAPI(title="Watad AridOS RFQ Copilot API")
workflow_service = RFQWorkflowService()
supplier_catalog = SupplierCatalog.from_seed_data()
buyer_profiles = BuyerProfileStore.from_seed_data()


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str


class StartRFQWorkflowRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    company_id: str | None = None


class WorkflowMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)


class ValidateRFQRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rfq: RFQDraft
    company_id: str | None = None


class SupplierSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rfq: RFQDraft
    limit: int = Field(default=3, ge=1, le=10)


class OfferComparisonRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rfq: RFQDraft
    supplier_candidates: list[SupplierCandidate] = Field(min_length=1)


class CreditCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rfq: RFQDraft
    recommendation: AwardRecommendation
    company_id: str | None = None


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: ApprovalAction
    decided_by: str = Field(min_length=1)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="watad-api")


@app.post(
    "/api/workflows/rfq/start",
    response_model=RFQWorkflowState,
    status_code=status.HTTP_201_CREATED,
)
def start_rfq_workflow(request: StartRFQWorkflowRequest) -> RFQWorkflowState:
    return workflow_service.start(
        message=request.message,
        user_id=request.user_id,
        company_id=request.company_id,
    )


@app.post("/api/workflows/rfq/{workflow_id}/message", response_model=RFQWorkflowState)
def add_rfq_workflow_message(workflow_id: str, request: WorkflowMessageRequest) -> RFQWorkflowState:
    try:
        return workflow_service.add_message(workflow_id=workflow_id, message=request.message)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="workflow not found") from error


@app.get("/api/workflows/rfq/{workflow_id}", response_model=RFQWorkflowState)
def get_rfq_workflow(workflow_id: str) -> RFQWorkflowState:
    try:
        return workflow_service.get(workflow_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="workflow not found") from error


@app.post("/api/workflows/rfq/{workflow_id}/approve", response_model=RFQWorkflowState)
def approve_rfq_workflow_action(
    workflow_id: str,
    request: ApprovalDecisionRequest,
) -> RFQWorkflowState:
    try:
        return workflow_service.approve(
            workflow_id=workflow_id,
            action=request.action,
            decided_by=request.decided_by,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail="pending approval not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.post("/api/workflows/rfq/{workflow_id}/reject", response_model=RFQWorkflowState)
def reject_rfq_workflow_action(
    workflow_id: str,
    request: ApprovalDecisionRequest,
) -> RFQWorkflowState:
    try:
        return workflow_service.reject(
            workflow_id=workflow_id,
            action=request.action,
            decided_by=request.decided_by,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail="pending approval not found") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@app.get("/api/workflows/rfq/{workflow_id}/artifacts", response_model=list[GeneratedDocument])
def get_rfq_workflow_artifacts(workflow_id: str) -> list[GeneratedDocument]:
    try:
        return workflow_service.get(workflow_id).generated_documents
    except KeyError as error:
        raise HTTPException(status_code=404, detail="workflow not found") from error


@app.post("/tools/rfq/validate", response_model=RFQValidationResult)
def validate_rfq_tool(request: ValidateRFQRequest) -> RFQValidationResult:
    return validate_rfq(request.rfq, company_id=request.company_id)


@app.post("/tools/suppliers/search", response_model=list[SupplierCandidate])
def search_suppliers_tool(request: SupplierSearchRequest) -> list[SupplierCandidate]:
    return shortlist_suppliers(request.rfq, catalog=supplier_catalog, limit=request.limit)


@app.post("/tools/offers/compare", response_model=AwardRecommendation)
def compare_offers_tool(request: OfferComparisonRequest) -> AwardRecommendation:
    recommendation = rank_award_options(request.rfq, request.supplier_candidates)
    if recommendation is None:
        raise HTTPException(status_code=400, detail="supplier candidates are required")

    return recommendation


@app.post("/tools/credit/check", response_model=CreditCheckResult)
def check_credit_tool(request: CreditCheckRequest) -> CreditCheckResult:
    return check_credit_policy(
        rfq=request.rfq,
        recommendation=request.recommendation,
        company_id=request.company_id,
        buyer_profiles=buyer_profiles,
    )
