from __future__ import annotations

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from watad.models import RFQDraft, RFQValidationResult, RFQWorkflowState
from watad.services.rfq_validation import validate_rfq
from watad.workflows.rfq import RFQWorkflowService

app = FastAPI(title="Watad AridOS RFQ Copilot API")
workflow_service = RFQWorkflowService()


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


@app.post("/tools/rfq/validate", response_model=RFQValidationResult)
def validate_rfq_tool(request: ValidateRFQRequest) -> RFQValidationResult:
    return validate_rfq(request.rfq, company_id=request.company_id)
