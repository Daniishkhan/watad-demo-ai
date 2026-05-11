from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import uuid4

from watad.models import AuditEvent, RFQDraft, RFQWorkflowState, SupplierCandidate, WorkflowMessage
from watad.services.intake import parse_procurement_message
from watad.services.rfq_validation import generate_clarifying_question, validate_rfq
from watad.services.supplier_matching import SupplierCatalog, shortlist_suppliers


class RFQWorkflowService:
    def __init__(
        self,
        *,
        today: Callable[[], date] | None = None,
        supplier_catalog: SupplierCatalog | None = None,
    ) -> None:
        self._today = today or date.today
        self._supplier_catalog = supplier_catalog or SupplierCatalog.from_seed_data()
        self._workflows: dict[str, RFQWorkflowState] = {}

    def start(self, *, message: str, user_id: str, company_id: str | None) -> RFQWorkflowState:
        workflow_id = f"wf_{uuid4().hex[:12]}"
        parsed_rfq = parse_procurement_message(message, today=self._today())
        validation = validate_rfq(parsed_rfq, company_id=company_id)
        supplier_candidates = (
            shortlist_suppliers(
                parsed_rfq,
                catalog=self._supplier_catalog,
                today=self._today(),
            )
            if validation.is_ready_for_supplier_search
            else []
        )
        status = (
            "supplier_shortlist_ready"
            if supplier_candidates and validation.is_ready_for_supplier_search
            else validation.status
        )
        state = RFQWorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            company_id=company_id,
            status=status,
            rfq=parsed_rfq,
            missing_fields=validation.missing_fields,
            questions=_questions_for(validation.missing_fields),
            supplier_candidates=supplier_candidates,
            messages=[WorkflowMessage(role="user", content=message)],
            audit_events=[
                AuditEvent(event_type="workflow_started", details={"user_id": user_id}),
                AuditEvent(
                    event_type="intake_parsed",
                    details={"extracted_fields": _extracted_field_names(parsed_rfq)},
                ),
                AuditEvent(
                    event_type="rfq_validated",
                    details={
                        "status": validation.status,
                        "missing_fields": validation.missing_fields,
                    },
                ),
                *_supplier_matching_events(supplier_candidates),
            ],
        )
        self._workflows[workflow_id] = state
        return state

    def add_message(self, *, workflow_id: str, message: str) -> RFQWorkflowState:
        state = self.get(workflow_id)
        parsed_update = parse_procurement_message(message, today=self._today())
        updated_rfq = _merge_rfq(state.rfq, parsed_update)
        validation = validate_rfq(updated_rfq, company_id=state.company_id)
        supplier_candidates = (
            shortlist_suppliers(
                updated_rfq,
                catalog=self._supplier_catalog,
                today=self._today(),
            )
            if validation.is_ready_for_supplier_search
            else []
        )
        status = (
            "supplier_shortlist_ready"
            if supplier_candidates and validation.is_ready_for_supplier_search
            else validation.status
        )
        updated_state = state.model_copy(
            update={
                "status": status,
                "rfq": updated_rfq,
                "missing_fields": validation.missing_fields,
                "questions": _questions_for(validation.missing_fields),
                "supplier_candidates": supplier_candidates,
                "messages": [
                    *state.messages,
                    WorkflowMessage(role="user", content=message),
                ],
                "audit_events": [
                    *state.audit_events,
                    AuditEvent(event_type="user_message_received"),
                    AuditEvent(
                        event_type="intake_parsed",
                        details={"extracted_fields": _extracted_field_names(parsed_update)},
                    ),
                    AuditEvent(
                        event_type="rfq_validated",
                        details={
                            "status": validation.status,
                            "missing_fields": validation.missing_fields,
                        },
                    ),
                    *_supplier_matching_events(supplier_candidates),
                ],
            }
        )
        self._workflows[workflow_id] = updated_state
        return updated_state

    def get(self, workflow_id: str) -> RFQWorkflowState:
        return self._workflows[workflow_id]


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
