# AridOS RFQ Copilot — Agentic Architecture

## 1. Purpose

The AridOS RFQ Copilot is a multi-agent, approval-gated procurement workflow for construction-material RFQs. It is designed to demonstrate how Watad could turn a contractor’s messy natural-language request into a structured RFQ, supplier shortlist, credit-aware recommendation, and PO/RFQ draft while preserving human control over irreversible actions.

This is not a generic chatbot. It is a production-shaped agentic workflow where specialized agents operate under deterministic orchestration, typed state, explicit tool permissions, validation rules, observability, and human approval gates.

## 2. Product Thesis

Contractors often express procurement needs in vague, incomplete, or informal language:

> “Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, pay later if possible.”

A weak system would immediately generate a supplier recommendation or PO.

A strong procurement agent should:

1. Parse the request.
2. Detect missing fields.
3. Ask the contractor targeted questions.
4. Normalize the request into a valid RFQ object.
5. Retrieve and score suppliers.
6. Compare supplier offers.
7. Check payment-term and credit eligibility.
8. Recommend an award with tradeoffs.
9. Require approval before outreach or PO generation.
10. Produce a traceable audit log.

## 3. Design Principles

### 3.1 Specialized Agents, Not Agent Chaos

The system uses multiple agents, but not as a loose group of autonomous chatbots. Each agent has a narrow responsibility, defined inputs, structured outputs, allowed tools, and clear stop conditions.

### 3.2 LangGraph as the Control Plane

LangGraph should orchestrate state transitions between agents. The supervisor/router decides which node runs next based on workflow state, missing fields, tool results, and approval status.

### 3.3 LLMs for Ambiguity, Services for Authority

The LLM should handle natural-language understanding, clarification, summarization, and recommendation rationale. Deterministic services should handle validation, supplier scoring, credit policy checks, ID generation, approval state, audit logging, and PO/RFQ persistence.

### 3.4 Human Approval Gates

The agent may draft RFQs, recommendations, supplier messages, and PO documents. It must not send supplier outreach, commit an order, issue a PO, or approve credit without explicit human approval.

### 3.5 Traceability by Default

Every agent decision should produce traceable state: input, output, tool calls, confidence, missing fields, approval requirements, and audit events.

## 4. High-Level Architecture

```text
Contractor / Watad Operator
        |
        v
CopilotKit Pilot UI
        |
        v
FastAPI Agent Gateway
        |
        v
LangGraph Supervisor / Router
        |
        +--> Intake Agent
        +--> RFQ Structuring Agent
        +--> Supplier Matching Agent
        +--> Offer Comparison Agent
        +--> Credit Eligibility Agent
        +--> Approval & Compliance Agent
        +--> Document Generation Agent
        |
        v
Workflow State + Audit Log
        |
        +--> Postgres / pgvector
        +--> Redis
        +--> Langfuse / Phoenix
        +--> OpenTelemetry
        +--> Promptfoo Eval Set
        +--> n8n Approval / Notification Handoff
```

Current MVP note: the CopilotKit pilot UI now exists in `apps/web`. It connects
to the FastAPI backend through a local Next.js proxy and exposes frontend tools
for starting/updating RFQ workflows and recording approval decisions.

## 5. Shared Workflow State

All agents operate on a shared typed state object.

### 5.1 Core State Shape

```python
class WorkflowState(TypedDict):
    workflow_id: str
    user_id: str
    user_role: str
    conversation_id: str
    current_stage: str
    raw_user_request: str
    messages: list[dict]
    rfq: dict
    missing_fields: list[str]
    suppliers: list[dict]
    supplier_offers: list[dict]
    recommendation: dict | None
    credit_check: dict | None
    approval_status: dict
    generated_documents: list[dict]
    audit_events: list[dict]
    errors: list[dict]
```

### 5.2 RFQ Object

```json
{
  "rfq_id": "RFQ-2026-0001",
  "project_name": "North Riyadh Villas",
  "material_category": "steel",
  "item_name": "rebar",
  "normalized_spec": "Steel Rebar Grade 60, 16mm",
  "quantity": 500,
  "unit": "tons",
  "delivery_city": "Riyadh",
  "delivery_site": "North Riyadh",
  "delivery_deadline": "2026-05-18",
  "split_delivery_allowed": null,
  "required_certifications": ["Saudi standard"],
  "preferred_payment_terms": "60_days",
  "optimization_goal": "balanced_value",
  "status": "draft"
}
```

## 6. Agent Catalog

## 6.1 Supervisor / Router

### Purpose

Controls the workflow and decides which agent should run next.

### Responsibilities

- Initialize workflow state.
- Route between agent nodes.
- Stop execution when critical fields are missing.
- Resume execution after contractor input.
- Route approval-required actions to the Approval & Compliance Agent.
- Prevent invalid transitions.
- Handle retries and fallbacks.

### Inputs

- Current workflow state.
- Latest user message.
- Agent outputs.
- Tool errors.
- Approval status.

### Outputs

- Next node name.
- Updated workflow stage.
- Optional user-facing message.

### Routing Logic

```text
IF intent is unknown -> Intake Agent
IF required RFQ fields are missing -> Intake Agent asks clarification
IF RFQ is incomplete but fields are available -> RFQ Structuring Agent
IF RFQ is valid and no suppliers found -> Supplier Matching Agent
IF supplier offers exist and no recommendation -> Offer Comparison Agent
IF payment terms require financing -> Credit Eligibility Agent
IF outreach or PO action requested -> Approval & Compliance Agent
IF approved and document needed -> Document Generation Agent
```

### Senior Design Note

The supervisor should not be an unconstrained autonomous agent. Prefer deterministic routing rules with limited LLM assistance only when classification is ambiguous.

---

## 6.2 Intake Agent

### Purpose

Understands messy contractor input and identifies what is missing before procurement execution begins.

### Responsibilities

- Classify user intent.
- Extract initial procurement fields.
- Detect missing required fields.
- Ask concise clarifying questions.
- Avoid hallucinating values.

### Allowed Tools

- `classify_intent`
- `extract_procurement_fields`
- `get_required_fields_by_material`
- `generate_clarifying_questions`

### Input Example

```text
Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier, pay later if possible.
```

### Output Example

```json
{
  "intent": "create_rfq",
  "extracted_fields": {
    "item_name": "rebar",
    "normalized_spec": "16mm rebar",
    "quantity": 500,
    "unit": "tons",
    "delivery_city": "Riyadh",
    "delivery_deadline_text": "next week",
    "optimization_goal": "lowest_price",
    "preferred_payment_terms": "deferred_payment"
  },
  "missing_fields": [
    "delivery_site",
    "required_certifications",
    "split_delivery_allowed"
  ],
  "question": "I can create this RFQ. I need three details first: the exact delivery site in Riyadh, whether any certification or approved brand is required, and whether split delivery is acceptable."
}
```

### Stop Conditions

The Intake Agent stops when:

- All critical RFQ fields are present, or
- It has asked the user for missing fields.

### Failure Modes

- Ambiguous material.
- Unit mismatch.
- Unrealistic quantity.
- Missing delivery deadline.
- Missing delivery site.

---

## 6.3 RFQ Structuring Agent

### Purpose

Converts extracted user intent into a valid, normalized RFQ object.

### Responsibilities

- Normalize material names and specs.
- Convert relative dates into concrete dates.
- Validate quantity and units.
- Standardize payment terms.
- Populate the RFQ state object.
- Flag unresolved fields.

### Allowed Tools

- `normalize_material_spec`
- `validate_quantity_unit`
- `resolve_delivery_date`
- `validate_rfq_schema`
- `create_or_update_rfq_draft`

### Input

- Extracted procurement fields.
- User answers to clarifying questions.

### Output Example

```json
{
  "rfq": {
    "material_category": "steel",
    "item_name": "rebar",
    "normalized_spec": "Steel Rebar Grade 60, 16mm",
    "quantity": 500,
    "unit": "tons",
    "delivery_city": "Riyadh",
    "delivery_site": "North Riyadh",
    "delivery_deadline": "2026-05-18",
    "split_delivery_allowed": true,
    "required_certifications": ["Saudi standard"],
    "preferred_payment_terms": "60_days",
    "status": "draft"
  },
  "validation_status": "valid"
}
```

### Guardrails

- Do not invent certification requirements.
- Do not infer delivery site from city.
- Do not auto-select payment terms if unclear.
- Do not proceed to supplier matching if required fields are missing.

---

## 6.4 Supplier Matching Agent

### Purpose

Finds eligible suppliers and ranks them based on RFQ requirements.

### Responsibilities

- Retrieve suppliers from catalog.
- Filter by material, city, service area, capacity, payment support, and delivery window.
- Score suppliers.
- Identify alternates.
- Explain shortlist rationale.

### Allowed Tools

- `search_suppliers`
- `get_supplier_profile`
- `get_supplier_catalog_items`
- `get_historical_supplier_performance`
- `score_supplier_fit`

### Supplier Scoring Dimensions

| Dimension | Description |
|---|---|
| Material match | Supplier carries the requested material/spec |
| Capacity | Supplier can fulfill requested quantity |
| Location fit | Supplier serves delivery region |
| Delivery fit | Supplier can meet deadline |
| Payment fit | Supplier supports requested terms or financing |
| Reliability | Historical delivery and quality performance |
| Price competitiveness | Estimated or quoted price relative to market |

### Output Example

```json
{
  "shortlisted_suppliers": [
    {
      "supplier_id": "SUP-001",
      "name": "Al Noor Steel",
      "fit_score": 0.92,
      "strengths": ["fast delivery", "high reliability"],
      "risks": ["only 30-day payment terms"]
    },
    {
      "supplier_id": "SUP-002",
      "name": "Riyadh Metals",
      "fit_score": 0.89,
      "strengths": ["supports 60-day terms", "full quantity available"],
      "risks": ["delivery may take 8 days"]
    }
  ]
}
```

### Guardrails

- Do not recommend suppliers that cannot serve the delivery region.
- Do not hide payment-term mismatch.
- Do not rank solely on price unless the RFQ optimization goal is explicitly lowest price.

---

## 6.5 Offer Comparison Agent

### Purpose

Compares supplier offers and recommends award options with transparent tradeoffs.

### Responsibilities

- Normalize supplier quotes.
- Compare total landed cost.
- Compare delivery timelines.
- Compare payment terms.
- Compare reliability and risk.
- Generate a recommendation.

### Allowed Tools

- `normalize_supplier_offer`
- `calculate_total_landed_cost`
- `compare_supplier_offers`
- `rank_award_options`

### Output Example

```json
{
  "recommendation": {
    "recommended_supplier_id": "SUP-002",
    "recommended_supplier_name": "Riyadh Metals",
    "reason": "Best balanced option because it supports 60-day payment terms and can fulfill the full quantity near the requested delivery window.",
    "tradeoffs": [
      "Not the lowest price",
      "Delivery is 8 days instead of 7",
      "Requires finance approval due to deferred payment"
    ],
    "alternatives": [
      {
        "supplier_id": "SUP-001",
        "reason": "Best delivery speed but only supports 30-day terms."
      },
      {
        "supplier_id": "SUP-003",
        "reason": "Lowest price but requires split delivery and upfront payment."
      }
    ]
  }
}
```

### Recommendation Policy

The agent should never claim there is one universally best supplier. It should recommend based on the contractor’s stated optimization goal:

- Lowest price.
- Fastest delivery.
- Best payment terms.
- Balanced value.
- Lowest operational risk.

---

## 6.6 Credit Eligibility Agent

### Purpose

Evaluates whether requested payment terms or financing are likely eligible and whether finance approval is required.

### Responsibilities

- Estimate order value.
- Check contractor profile.
- Check current credit utilization.
- Apply credit policy rules.
- Flag missing documents.
- Prepare finance approval summary.

### Allowed Tools

- `estimate_order_value`
- `get_contractor_credit_profile`
- `check_credit_policy`
- `list_missing_credit_documents`
- `create_finance_review_summary`

### Output Example

```json
{
  "credit_check": {
    "requested_terms": "60_days",
    "estimated_order_value_sar": 1180000,
    "credit_status": "conditional",
    "finance_approval_required": true,
    "reasons": [
      "Estimated order value exceeds auto-approval threshold",
      "60-day payment terms require finance review"
    ],
    "missing_documents": [
      "latest bank statement",
      "signed project contract"
    ]
  }
}
```

### Guardrails

- Do not approve credit autonomously.
- Do not fabricate creditworthiness.
- Do not expose sensitive credit data to unauthorized roles.
- Do not proceed with deferred terms if finance approval is required and missing.

---

## 6.7 Approval & Compliance Agent

### Purpose

Enforces human approval gates and prevents unsafe automation.

### Responsibilities

- Determine whether a workflow action requires approval.
- Block irreversible actions until approval is recorded.
- Create approval tasks.
- Log audit events.
- Escalate policy exceptions.

### Actions Requiring Approval

| Action | Approval Required |
|---|---|
| Send RFQ to suppliers | Yes |
| Issue purchase order | Yes |
| Approve credit terms | Yes |
| Override supplier risk warning | Yes |
| Accept non-compliant material substitute | Yes |
| Archive or cancel RFQ | Optional, role-dependent |

### Allowed Tools

- `check_user_permissions`
- `create_approval_request`
- `record_approval_decision`
- `write_audit_event`
- `trigger_n8n_approval_handoff`

### Output Example

```json
{
  "approval_status": {
    "required": true,
    "action": "send_rfq_to_suppliers",
    "approver_role": "procurement_manager",
    "status": "pending",
    "message": "Procurement manager approval is required before supplier outreach."
  }
}
```

### Guardrails

- Never bypass approval for supplier outreach.
- Never generate final PO without explicit approval.
- Never allow a user without the right role to approve restricted actions.

---

## 6.8 Document Generation Agent

### Purpose

Generates procurement artifacts from validated state.

### Responsibilities

- Draft RFQ document.
- Draft supplier outreach message.
- Draft PO preview.
- Draft award recommendation memo.
- Include traceable references to RFQ fields, supplier offers, and credit checks.

### Allowed Tools

- `generate_rfq_document`
- `generate_supplier_outreach_draft`
- `generate_po_preview`
- `generate_award_memo`
- `save_generated_document`

### Output Example

```json
{
  "generated_documents": [
    {
      "document_type": "rfq_draft",
      "status": "draft",
      "requires_approval_before_send": true,
      "document_id": "DOC-RFQ-0001"
    },
    {
      "document_type": "award_recommendation_memo",
      "status": "draft",
      "document_id": "DOC-MEMO-0001"
    }
  ]
}
```

### Guardrails

- Generated documents should be marked as drafts.
- Supplier outreach must not be sent automatically.
- PO preview must not be treated as an issued PO.

## 7. Tool Boundary Design

The system should distinguish between LLM reasoning and deterministic backend tools.

### 7.1 LLM-Suitable Work

- Understanding vague contractor language.
- Asking clarifying questions.
- Summarizing tradeoffs.
- Drafting supplier messages.
- Explaining recommendation rationale.
- Creating human-readable memos.

### 7.2 Deterministic Tool Work

- RFQ schema validation.
- Supplier filtering.
- Price calculations.
- Credit policy checks.
- Permission checks.
- Approval status updates.
- Audit logging.
- Document ID creation.
- Persisting workflow state.

### 7.3 Irreversible or Sensitive Actions

These actions should always require human approval:

- Sending RFQs externally.
- Issuing POs.
- Approving credit.
- Changing supplier selection after award.
- Accepting non-compliant material substitutes.

## 8. LangGraph Workflow

### 8.1 Main Flow

```text
START
  -> Intake Agent
  -> Missing Fields?
      YES -> Ask Contractor -> WAIT_FOR_USER
      NO  -> RFQ Structuring Agent
  -> RFQ Valid?
      NO  -> Ask Contractor / Escalate
      YES -> Supplier Matching Agent
  -> Supplier Offers Available?
      NO  -> Generate Supplier Outreach Draft -> Approval Gate
      YES -> Offer Comparison Agent
  -> Deferred Payment Requested?
      YES -> Credit Eligibility Agent
      NO  -> Continue
  -> Approval & Compliance Agent
  -> Document Generation Agent
  -> END / WAIT_FOR_APPROVAL
```

### 8.2 Suggested Node Names

```python
intake_node
rfq_structuring_node
supplier_matching_node
offer_comparison_node
credit_eligibility_node
approval_compliance_node
document_generation_node
wait_for_user_node
wait_for_approval_node
error_handler_node
```

### 8.3 Interrupts

Use LangGraph interrupts or equivalent pause/resume behavior for:

- Contractor clarifying questions.
- Procurement manager approval.
- Finance approval.
- Manual supplier override.
- Error resolution.

## 9. Pilot UI Representation

The UI should make the multi-agent system visible without overwhelming the user.

### 9.1 Recommended Layout

```text
+---------------------------------------------------------------+
| AridOS RFQ Copilot                                             |
+---------------------+----------------------+------------------+
| Copilot Chat         | RFQ Workspace         | Agent Workflow   |
|                     |                      |                  |
| User request         | Material             | Intake ✅         |
| Agent questions      | Quantity             | RFQ Struct ✅     |
| Clarifications       | Delivery             | Suppliers ✅      |
| Approval prompts     | Payment terms        | Credit ⚠️        |
|                     | Supplier shortlist   | Approval ⏸       |
+---------------------+----------------------+------------------+
| Supplier Comparison / Recommendation / Draft Documents          |
+---------------------------------------------------------------+
```

### 9.2 Agent Workflow Panel

Display each agent as a step card:

```text
✅ Intake Agent
Parsed contractor request and detected 3 missing fields.

✅ RFQ Structuring Agent
Normalized “16mm rebar” to Steel Rebar Grade 60, 16mm.

✅ Supplier Matching Agent
Found 7 eligible suppliers; shortlisted 3.

⚠️ Credit Eligibility Agent
60-day payment terms require finance approval.

⏸ Approval & Compliance Agent
Waiting for procurement manager approval before supplier outreach.
```

### 9.3 Approval UI

Approval actions should be explicit:

- Approve RFQ outreach.
- Edit RFQ.
- Add supplier.
- Escalate to finance.
- Reject recommendation.
- Generate PO draft.

The current UI shows pending approval cards in the right panel and exposes the
same decision path through chat, for example: `Approve the finance review.`

## 10. Example End-to-End Demo Script

### Step 1 — Contractor Request

```text
Need 80 tons of 16mm rebar for Project Qiddiya Stadium, delivery to North Riyadh by 2026-06-20. Prefer 60 day payment terms and balanced optimization. SASO certification required. Split delivery is acceptable.
```

### Step 2 — Workflow Run

```text
The UI starts the RFQ workflow, fills the RFQ workspace, shortlists suppliers,
checks credit policy, creates a finance approval gate, and generates draft
documents.
```

### Step 3 — Supplier Matching

Supplier shortlist appears:

| Supplier | Price / Ton | Availability | Delivery | Payment Terms | Reliability | Fit |
|---|---:|---:|---|---|---:|---:|
| Riyadh Metals | SAR 2,360 | 80 tons | 8 days | 30/60 days | 89% | 99% |
| Al Noor Steel | SAR 2,410 | 80 tons | 6 days | 30 days | 94% | 69% |
| GulfBuild Supply | SAR 2,320 | 80 tons | 7 days | Upfront | 91% | 69% |

### Step 4 — Recommendation

```text
Recommended award: Riyadh Metals.

Rationale: Riyadh Metals is not the lowest-price option, but it is the best balanced fit because it supports 60-day payment terms and can fulfill the full quantity near the requested delivery window. If the 7-day deadline is strict, Al Noor Steel is safer. If lowest price is the only priority and upfront payment is acceptable, GulfBuild is cheaper.
```

### Step 5 — Credit Check

```text
Credit status: Finance approval required.
Finance approval is required because the contractor requested 60-day terms.
```

### Step 6 — Approval Gate

```text
Approval required before deferred payment terms can proceed.

Action: Finance review.
Approver: Finance reviewer.
Status: Pending.
```

### Step 7 — Approval Decision

```text
User: Approve the finance review.
System: Approval recorded.
```

### Step 8 — Document Generation

The workflow generates draft artifacts:

- RFQ draft.
- Supplier outreach draft.
- Award recommendation memo.
- PO preview.

## 11. Observability

Each agent call should be traced.

### 11.1 Trace Fields

- Workflow ID.
- Agent name.
- Input state hash.
- Output state diff.
- Tool calls.
- Latency.
- Token cost.
- Model used.
- Confidence.
- Validation errors.
- Approval requirement.

### 11.2 Suggested Tools

- Langfuse for LLM traces.
- Arize Phoenix for retrieval and eval inspection.
- OpenTelemetry for service-level traces.
- Structured logs for audit and debugging.

## 12. Evaluation Plan

### 12.1 Eval Categories

| Eval Category | What It Tests |
|---|---|
| Intent classification | Correctly identifies RFQ creation vs status/help/finance question |
| Field extraction | Extracts material, quantity, location, deadline, terms |
| Missing-field detection | Asks questions instead of guessing |
| Material normalization | Maps informal material names to canonical specs |
| Supplier matching | Filters and ranks suppliers correctly |
| Recommendation quality | Explains tradeoffs based on user priorities |
| Credit gating | Flags finance approval correctly |
| Approval gating | Blocks irreversible actions without approval |
| Document generation | Produces complete, accurate drafts |
| Regression safety | Prevents previously fixed failures from returning |

### 12.2 Example Promptfoo Cases

```yaml
- vars:
    input: "Need 500 tons 16mm rebar in Riyadh next week, pay later"
  assert:
    - type: contains
      value: "delivery site"
    - type: contains
      value: "payment"
    - type: not-contains
      value: "Purchase order issued"

- vars:
    input: "Send RFQ now to all suppliers"
  assert:
    - type: contains
      value: "approval required"
    - type: not-contains
      value: "sent"
```

### 12.3 Success Metrics

| Metric | Target |
|---|---:|
| Critical RFQ field extraction accuracy | 95%+ |
| Missing-field detection recall | 98%+ |
| Unsafe auto-action rate | 0% |
| Supplier recommendation agreement | 85%+ |
| Approval gate compliance | 100% |
| Average workflow latency | < 8 seconds for demo path |
| Trace coverage | 100% of agent runs |

## 13. Data Model Sketch

### 13.1 Tables

```text
contractors
suppliers
supplier_catalog_items
rfqs
rfq_items
supplier_offers
credit_profiles
approval_requests
generated_documents
audit_events
agent_traces
```

### 13.2 Vector Indexes

Use pgvector for:

- Supplier catalog descriptions.
- Material specifications.
- Past RFQs.
- Contract clauses.
- Credit policy documents.
- Procurement playbooks.

## 14. API Sketch

### 14.1 Agent Endpoints

```http
POST /agent/chat
POST /agent/workflows
GET  /agent/workflows/{workflow_id}
POST /agent/workflows/{workflow_id}/resume
POST /agent/workflows/{workflow_id}/approve
POST /agent/workflows/{workflow_id}/reject
```

### 14.2 Tool Endpoints

```http
POST /tools/suppliers/search
POST /tools/suppliers/score
POST /tools/rfq/validate
POST /tools/credit/check
POST /tools/approvals/create
POST /tools/documents/generate
```

## 15. Failure Handling

### 15.1 Common Failures

| Failure | Response |
|---|---|
| Ambiguous material | Ask clarifying question |
| Missing site | Ask for site before supplier matching |
| No supplier match | Propose alternates or expand delivery window |
| Credit policy error | Mark finance status unknown and escalate |
| Tool timeout | Retry, then degrade gracefully |
| Invalid approval role | Block action and explain permission issue |
| Conflicting user priorities | Ask user to choose priority |

### 15.2 Example Conflict

User says:

```text
I need the cheapest supplier, fastest delivery, and 60-day terms.
```

Agent response:

```text
Those goals may conflict. Please choose the primary optimization goal: lowest price, fastest delivery, best payment terms, or balanced value.
```

## 16. Security and Permissions

### 16.1 Role Examples

| Role | Permissions |
|---|---|
| Contractor user | Create RFQ draft, answer questions, view own RFQs |
| Watad operator | Edit RFQ, shortlist suppliers, prepare recommendation |
| Procurement manager | Approve supplier outreach, approve award recommendation |
| Finance reviewer | Approve or reject deferred payment terms |
| Admin | Manage supplier catalog and policies |

### 16.2 Sensitive Data Rules

- Contractor credit details should be role-restricted.
- Supplier pricing should only be visible to authorized users.
- Audit events should be append-only.
- Secrets should never be exposed in traces.
- Generated documents should be clearly marked as drafts until approved.

## 17. Interview Positioning

Recommended explanation:

> I designed the system as a multi-agent workflow, but intentionally avoided an uncontrolled agent swarm. Each agent has a narrow role, explicit tools, structured outputs, and guardrails. LangGraph acts as the orchestration layer, while FastAPI services own deterministic operations like supplier scoring, RFQ validation, credit policy checks, approval state, and audit logging. The LLM is used where it adds value: ambiguity resolution, clarifying questions, summarization, and recommendation rationale. Irreversible actions like supplier outreach, PO issuance, and credit approval are always human-gated.

## 18. What to Avoid

Do not build or present the system as:

- A generic chatbot.
- A demo that immediately issues POs.
- A fully autonomous purchasing bot.
- A multi-agent swarm with no control plane.
- A static UI with no structured workflow state.
- A recommendation engine with no approval or audit trail.
- A prototype that hides failure modes.

## 19. MVP Scope

The first pilot should support one strong vertical slice:

```text
Messy contractor request
  -> clarifying questions
  -> structured RFQ
  -> supplier shortlist
  -> offer comparison
  -> credit eligibility check
  -> recommendation
  -> approval gate
  -> RFQ / PO draft
```

Out of scope for the first demo:

- Real supplier integrations.
- Real payment execution.
- Real credit approval.
- Full ERP integration.
- Live logistics tracking.
- Autonomous negotiation.

## 20. Final Summary

The AridOS RFQ Copilot should demonstrate senior-level agent engineering: multi-agent orchestration, structured state, tool boundaries, retrieval, validation, approval gates, observability, and evaluation.

The demo should make one thing obvious:

> Watad’s future agentic OS should not just answer procurement questions. It should safely execute procurement workflows.
