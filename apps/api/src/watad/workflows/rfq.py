from __future__ import annotations

from collections.abc import Callable
from datetime import date
from uuid import uuid4

from watad.models import AuditEvent, RFQDraft, RFQWorkflowState, WorkflowMessage
from watad.services.intake import parse_procurement_message
from watad.services.rfq_validation import generate_clarifying_question, validate_rfq


class RFQWorkflowService:
    def __init__(self, *, today: Callable[[], date] | None = None) -> None:
        self._today = today or date.today
        self._workflows: dict[str, RFQWorkflowState] = {}

    def start(self, *, message: str, user_id: str, company_id: str | None) -> RFQWorkflowState:
        workflow_id = f"wf_{uuid4().hex[:12]}"
        parsed_rfq = parse_procurement_message(message, today=self._today())
        validation = validate_rfq(parsed_rfq, company_id=company_id)
        state = RFQWorkflowState(
            workflow_id=workflow_id,
            user_id=user_id,
            company_id=company_id,
            status=validation.status,
            rfq=parsed_rfq,
            missing_fields=validation.missing_fields,
            questions=_questions_for(validation.missing_fields),
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
            ],
        )
        self._workflows[workflow_id] = state
        return state

    def add_message(self, *, workflow_id: str, message: str) -> RFQWorkflowState:
        state = self.get(workflow_id)
        parsed_update = parse_procurement_message(message, today=self._today())
        updated_rfq = _merge_rfq(state.rfq, parsed_update)
        validation = validate_rfq(updated_rfq, company_id=state.company_id)
        updated_state = state.model_copy(
            update={
                "status": validation.status,
                "rfq": updated_rfq,
                "missing_fields": validation.missing_fields,
                "questions": _questions_for(validation.missing_fields),
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
