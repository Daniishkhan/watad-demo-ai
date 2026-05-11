from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any, Final, TypedDict, cast
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from watad.models import (
    AuditEvent,
    AwardRecommendation,
    RFQDraft,
    RFQWorkflowState,
    RFQWorkflowStatus,
    SupplierCandidate,
    WorkflowMessage,
)
from watad.services.intake import parse_procurement_message
from watad.services.offer_comparison import rank_award_options
from watad.services.rfq_validation import generate_clarifying_question, validate_rfq
from watad.services.supplier_matching import SupplierCatalog, shortlist_suppliers

RFQ_GRAPH_NODE_NAMES: Final[tuple[str, ...]] = (
    "intake_node",
    "rfq_validation_node",
    "supplier_matching_node",
    "offer_comparison_node",
)


class RFQGraphState(TypedDict):
    workflow_id: str
    user_id: str
    company_id: str | None
    status: RFQWorkflowStatus
    rfq: RFQDraft
    missing_fields: list[str]
    questions: list[str]
    supplier_candidates: list[SupplierCandidate]
    recommendation: AwardRecommendation | None
    messages: list[WorkflowMessage]
    audit_events: list[AuditEvent]
    latest_user_message: str
    is_new_workflow: bool


class RFQWorkflowService:
    def __init__(
        self,
        *,
        today: Callable[[], date] | None = None,
        supplier_catalog: SupplierCatalog | None = None,
    ) -> None:
        self._today = today or date.today
        self._supplier_catalog = supplier_catalog or SupplierCatalog.from_seed_data()
        self._graph: Any = _build_graph(self)
        self._workflows: dict[str, RFQWorkflowState] = {}

    @property
    def graph_node_names(self) -> tuple[str, ...]:
        return RFQ_GRAPH_NODE_NAMES

    def start(self, *, message: str, user_id: str, company_id: str | None) -> RFQWorkflowState:
        workflow_id = f"wf_{uuid4().hex[:12]}"
        state = self._run_graph(
            _initial_graph_state(
                workflow_id=workflow_id,
                user_id=user_id,
                company_id=company_id,
                latest_user_message=message,
                is_new_workflow=True,
            )
        )
        self._workflows[workflow_id] = state
        return state

    def add_message(self, *, workflow_id: str, message: str) -> RFQWorkflowState:
        state = self.get(workflow_id)
        updated_state = self._run_graph(
            _graph_state_from_workflow_state(
                state,
                latest_user_message=message,
                is_new_workflow=False,
            )
        )
        self._workflows[workflow_id] = updated_state
        return updated_state

    def get(self, workflow_id: str) -> RFQWorkflowState:
        return self._workflows[workflow_id]

    def _run_graph(self, initial_state: RFQGraphState) -> RFQWorkflowState:
        result = cast(RFQGraphState, self._graph.invoke(initial_state))
        return _workflow_state_from_graph_state(result)

    def _intake_node(self, state: RFQGraphState) -> dict[str, object]:
        parsed_update = parse_procurement_message(state["latest_user_message"], today=self._today())
        rfq = parsed_update if state["is_new_workflow"] else _merge_rfq(state["rfq"], parsed_update)
        audit_events = [*state["audit_events"]]
        if state["is_new_workflow"]:
            audit_events.append(
                AuditEvent(event_type="workflow_started", details={"user_id": state["user_id"]})
            )
        else:
            audit_events.append(AuditEvent(event_type="user_message_received"))
        audit_events.append(
            AuditEvent(
                event_type="intake_parsed",
                details={"extracted_fields": _extracted_field_names(parsed_update)},
            )
        )

        return {
            "rfq": rfq,
            "messages": [
                *state["messages"],
                WorkflowMessage(role="user", content=state["latest_user_message"]),
            ],
            "supplier_candidates": [],
            "recommendation": None,
            "audit_events": audit_events,
        }

    def _rfq_validation_node(self, state: RFQGraphState) -> dict[str, object]:
        validation = validate_rfq(state["rfq"], company_id=state["company_id"])
        return {
            "status": validation.status,
            "missing_fields": validation.missing_fields,
            "questions": _questions_for(validation.missing_fields),
            "audit_events": [
                *state["audit_events"],
                AuditEvent(
                    event_type="rfq_validated",
                    details={
                        "status": validation.status,
                        "missing_fields": validation.missing_fields,
                    },
                ),
            ],
        }

    def _supplier_matching_node(self, state: RFQGraphState) -> dict[str, object]:
        supplier_candidates = (
            shortlist_suppliers(
                state["rfq"],
                catalog=self._supplier_catalog,
                today=self._today(),
            )
            if state["status"] == "ready_for_supplier_search"
            else []
        )
        status: RFQWorkflowStatus = (
            "supplier_shortlist_ready" if supplier_candidates else state["status"]
        )
        return {
            "status": status,
            "supplier_candidates": supplier_candidates,
            "audit_events": [
                *state["audit_events"],
                *_supplier_matching_events(supplier_candidates),
            ],
        }

    def _offer_comparison_node(self, state: RFQGraphState) -> dict[str, object]:
        recommendation = rank_award_options(state["rfq"], state["supplier_candidates"])
        status: RFQWorkflowStatus = "recommendation_ready" if recommendation else state["status"]
        return {
            "status": status,
            "recommendation": recommendation,
            "audit_events": [
                *state["audit_events"],
                *_offer_comparison_events(recommendation),
            ],
        }


def _build_graph(service: RFQWorkflowService) -> Any:
    graph = StateGraph(RFQGraphState)
    graph.add_node("intake_node", service._intake_node)
    graph.add_node("rfq_validation_node", service._rfq_validation_node)
    graph.add_node("supplier_matching_node", service._supplier_matching_node)
    graph.add_node("offer_comparison_node", service._offer_comparison_node)
    graph.add_edge(START, "intake_node")
    graph.add_edge("intake_node", "rfq_validation_node")
    graph.add_conditional_edges("rfq_validation_node", _route_after_validation)
    graph.add_conditional_edges("supplier_matching_node", _route_after_supplier_matching)
    graph.add_edge("offer_comparison_node", END)
    return graph.compile()


def _route_after_validation(state: RFQGraphState) -> str:
    if state["missing_fields"]:
        return END

    return "supplier_matching_node"


def _route_after_supplier_matching(state: RFQGraphState) -> str:
    if state["supplier_candidates"]:
        return "offer_comparison_node"

    return END


def _initial_graph_state(
    *,
    workflow_id: str,
    user_id: str,
    company_id: str | None,
    latest_user_message: str,
    is_new_workflow: bool,
) -> RFQGraphState:
    return {
        "workflow_id": workflow_id,
        "user_id": user_id,
        "company_id": company_id,
        "status": "draft",
        "rfq": RFQDraft(),
        "missing_fields": [],
        "questions": [],
        "supplier_candidates": [],
        "recommendation": None,
        "messages": [],
        "audit_events": [],
        "latest_user_message": latest_user_message,
        "is_new_workflow": is_new_workflow,
    }


def _graph_state_from_workflow_state(
    state: RFQWorkflowState,
    *,
    latest_user_message: str,
    is_new_workflow: bool,
) -> RFQGraphState:
    return {
        "workflow_id": state.workflow_id,
        "user_id": state.user_id,
        "company_id": state.company_id,
        "status": state.status,
        "rfq": state.rfq,
        "missing_fields": state.missing_fields,
        "questions": state.questions,
        "supplier_candidates": state.supplier_candidates,
        "recommendation": state.recommendation,
        "messages": state.messages,
        "audit_events": state.audit_events,
        "latest_user_message": latest_user_message,
        "is_new_workflow": is_new_workflow,
    }


def _workflow_state_from_graph_state(state: RFQGraphState) -> RFQWorkflowState:
    return RFQWorkflowState(
        workflow_id=state["workflow_id"],
        user_id=state["user_id"],
        company_id=state["company_id"],
        status=state["status"],
        rfq=state["rfq"],
        missing_fields=state["missing_fields"],
        questions=state["questions"],
        supplier_candidates=state["supplier_candidates"],
        recommendation=state["recommendation"],
        messages=state["messages"],
        audit_events=state["audit_events"],
    )


def _questions_for(missing_fields: list[str]) -> list[str]:
    if not missing_fields:
        return []

    return [generate_clarifying_question(missing_fields)]


def _merge_rfq(current: RFQDraft, update: RFQDraft) -> RFQDraft:
    merged = current.model_dump()
    update_values = update.model_dump(exclude_unset=True, exclude_none=True)
    for field_name, value in update_values.items():
        if isinstance(value, list) and not value:
            continue
        merged[field_name] = value

    return RFQDraft.model_validate(merged)


def _extracted_field_names(rfq: RFQDraft) -> list[str]:
    extracted: list[str] = []
    for field_name, value in rfq.model_dump(exclude_unset=True, exclude_none=True).items():
        if isinstance(value, list) and not value:
            continue
        extracted.append(field_name)

    return extracted


def _supplier_matching_events(supplier_candidates: list[SupplierCandidate]) -> list[AuditEvent]:
    if not supplier_candidates:
        return []

    return [
        AuditEvent(
            event_type="supplier_matching_completed",
            details={
                "supplier_ids": [candidate.supplier_id for candidate in supplier_candidates],
            },
        )
    ]


def _offer_comparison_events(recommendation: AwardRecommendation | None) -> list[AuditEvent]:
    if recommendation is None:
        return []

    return [
        AuditEvent(
            event_type="offer_comparison_completed",
            details={
                "recommended_supplier_id": recommendation.recommended_supplier_id,
                "alternative_supplier_ids": [
                    alternative.supplier_id for alternative in recommendation.alternatives
                ],
            },
        )
    ]
