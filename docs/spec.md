# AridOS RFQ Copilot — Product & Technical Spec

## 1. Overview

AridOS RFQ Copilot is a prototype agentic workflow for construction procurement. It helps a contractor or Watad operator convert an unstructured material request into a validated RFQ, supplier shortlist, credit-aware award recommendation, and approval-gated PO draft.

The goal is to demonstrate senior-level agent engineering: stateful orchestration, deterministic tools, retrieval, approval gates, observability, evaluation, and polished product UX.

## 2. Problem Statement

Construction procurement requests often begin as vague messages over WhatsApp, email, phone calls, or spreadsheets. Operators must clarify requirements, normalize material specifications, identify suppliers, collect offers, compare tradeoffs, check payment terms, coordinate approvals, and generate commercial documents.

This process is slow, fragmented, error-prone, and hard to audit.

AridOS RFQ Copilot addresses this by providing a guided AI workflow that:

- Understands messy contractor requests
- Asks targeted clarification questions
- Converts requests into structured RFQ objects
- Matches suppliers from catalog and supplier data
- Compares offers using deterministic scoring
- Checks payment and financing eligibility
- Requires human approval before external or financial actions
- Produces traceable RFQ and PO drafts

## 3. Target Users

### 3.1 Contractor Procurement Manager

Wants to request materials quickly, compare supplier options, and avoid back-and-forth.

### 3.2 Watad Procurement Operator

Wants to triage contractor requests, standardize RFQs, coordinate supplier outreach, and reduce manual work.

### 3.3 Finance/Credit Analyst

Wants to identify orders requiring credit review, missing documents, or financing escalation.

### 3.4 Operations Manager

Wants auditability, workflow visibility, and performance metrics.

## 4. Primary Workflow

### 4.1 Input

User submits a request such as:

> “Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier if possible, 60-day payment preferred.”

### 4.2 Intent Parsing

The agent extracts candidate fields:

- Material category: steel
- Material item: rebar
- Diameter/spec: 16mm
- Quantity: 500
- Unit: tons
- Delivery city: Riyadh
- Delivery date: next week
- Optimization preference: lowest price
- Payment preference: 60 days

### 4.3 Missing Field Detection

The workflow validates required and recommended fields.

Required fields:

- Material category
- Material specification
- Quantity
- Unit
- Delivery city
- Delivery location or district
- Delivery deadline
- Buyer/company identity
- Project/site name

Recommended fields:

- Certification or approved brand constraints
- Budget range
- Delivery flexibility
- Split delivery acceptance
- Payment terms
- Contact person
- Required documents

### 4.4 Clarifying Questions

The agent asks only necessary questions. Example:

> “I can create the RFQ, but I need four details before supplier outreach: exact delivery district/site, project name, required steel certification or approved brands, and whether split delivery is acceptable.”

### 4.5 RFQ State Update

The structured RFQ object is updated after every user answer.

### 4.6 Supplier Matching

The system retrieves relevant suppliers from synthetic data using:

- Material compatibility
- Location coverage
- Quantity availability
- Delivery window
- Payment terms
- Reliability score
- Historical pricing
- Certification support

### 4.7 Offer Comparison

The system ranks supplier options using deterministic scoring.

Example scoring dimensions:

- Price score
- Delivery score
- Availability score
- Payment terms score
- Reliability score
- Compliance score

### 4.8 Credit Check

The system performs a simple policy-based credit check.

Inputs:

- Buyer/company profile
- Estimated order value
- Requested payment terms
- Existing credit limit
- Current utilization
- Payment history flag
- Required documentation status

Outputs:

- Eligible
- Conditionally eligible
- Finance approval required
- Not eligible
- Missing information

### 4.9 Recommendation

The agent explains tradeoffs:

> “Recommendation: Riyadh Metals. It is not the lowest price, but it supports 60-day terms and can fulfill the full quantity within 8 days. If the 7-day deadline is strict, choose Al Noor Steel. If price is the only priority and split delivery is acceptable, choose GulfBuild Supply.”

### 4.10 Approval Gate

Before external action, the system shows approval options:

- Approve RFQ outreach
- Edit RFQ
- Add suppliers
- Reject recommendation
- Escalate to finance
- Generate PO draft

### 4.11 Artifact Generation

After approval, the system generates:

- RFQ draft
- Supplier outreach message
- Supplier comparison table
- PO draft
- Credit review summary
- Audit log

## 5. Functional Requirements

### 5.1 Conversational Copilot

- Accept natural-language procurement requests
- Ask targeted clarification questions
- Maintain memory of current RFQ state within the session
- Avoid repeating already answered questions
- Explain tradeoffs in business language

### 5.2 RFQ Extraction

- Extract structured fields from user input
- Normalize material names and units
- Convert relative dates into explicit dates
- Detect ambiguity and missing fields
- Support partial RFQ drafts

### 5.3 Supplier Matching

- Search synthetic supplier catalog
- Filter by material, location, availability, delivery, terms, and certifications
- Return ranked supplier candidates
- Explain why suppliers were included or excluded

### 5.4 Supplier Offer Simulation

For prototype purposes, supplier responses may be simulated from static data.

Each offer should include:

- Supplier name
- Material match
- Unit price
- Available quantity
- Delivery date/window
- Payment terms
- Reliability score
- Constraints or notes

### 5.5 Credit Policy Check

- Estimate order value
- Compare against buyer credit limit
- Check utilization
- Check requested payment terms
- Flag finance approval requirements
- Generate credit review summary

### 5.6 Approval Gates

The system must require approval before:

- Sending supplier outreach
- Confirming supplier award
- Generating final PO
- Escalating credit request
- Triggering any external webhook

### 5.7 PO/RFQ Drafting

The system should generate draft artifacts with clear status labels:

- Draft
- Pending approval
- Approved
- Sent
- Escalated

### 5.8 Audit Log

Track:

- User input
- Extracted fields
- Clarifying questions
- Tool calls
- Supplier matches
- Scoring decisions
- Credit result
- Approval decisions
- Generated artifacts

## 6. Non-Functional Requirements

### 6.1 Reliability

- Tool calls should be validated with schemas
- Failed tools should return recoverable errors
- Agent should not invent supplier data
- PO generation should require complete required fields

### 6.2 Observability

Capture:

- Workflow ID
- Session ID
- State transitions
- Prompt and model metadata
- Tool inputs and outputs
- Latency
- Errors
- Evaluation labels

Suggested tools:

- Langfuse for LLM traces
- Arize Phoenix for RAG inspection and evals
- OpenTelemetry for service traces

### 6.3 Evaluation

Create a small eval suite with 10–20 scenarios.

Test categories:

- Complete RFQ extraction
- Missing-field detection
- Clarifying-question quality
- Supplier matching correctness
- Credit policy correctness
- Unsafe action prevention
- Hallucination resistance
- Bilingual or mixed-language input, if time permits

Suggested eval tool:

- Promptfoo

### 6.4 Security and Controls

Prototype-level controls:

- No real supplier communication by default
- No real payment or financing execution
- Human approval required for external actions
- Mock credentials only
- Environment variables for secrets
- Clear separation between user-visible reasoning and system logs

### 6.5 Performance

Target prototype performance:

- Initial parsing response: under 3 seconds
- Supplier matching: under 2 seconds
- Full workflow recommendation: under 8–12 seconds
- UI state updates: near real time

## 7. Architecture

## 7.1 Recommended Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- CopilotKit
- shadcn/ui

### Backend

- FastAPI
- Python
- Pydantic schemas
- LangGraph
- LangChain or LlamaIndex where useful

### Data

- Postgres
- pgvector
- Synthetic supplier catalog
- Synthetic RFQ history
- Synthetic credit policy table

### State and Async

- Redis
- Background jobs where useful

### Observability

- Langfuse
- Optional Phoenix
- Optional OpenTelemetry

### Evaluation

- Promptfoo
- JSON eval cases
- Deterministic policy tests with pytest

### Automation

- n8n webhook for approval or notification simulation

## 7.2 High-Level Components

```text
Frontend / CopilotKit UI
        |
        v
FastAPI Agent API
        |
        v
LangGraph Workflow
        |
        |-- Intent Parser Node
        |-- RFQ Validator Node
        |-- Clarification Planner Node
        |-- Supplier Retrieval Tool
        |-- Supplier Scoring Tool
        |-- Credit Policy Tool
        |-- Recommendation Node
        |-- Approval Gate Node
        |-- Artifact Generator Node
        |
        v
Postgres / pgvector / Redis / Observability
```

## 8. LangGraph Workflow

### 8.1 State Object

```python
class RFQState(BaseModel):
    workflow_id: str
    user_id: str | None = None
    company_id: str | None = None
    raw_messages: list[dict] = []
    rfq: RFQDraft
    missing_fields: list[str] = []
    clarification_questions: list[str] = []
    supplier_candidates: list[SupplierCandidate] = []
    supplier_offers: list[SupplierOffer] = []
    credit_result: CreditCheckResult | None = None
    recommendation: AwardRecommendation | None = None
    approval_status: Literal[
        "draft",
        "needs_clarification",
        "ready_for_supplier_search",
        "ready_for_approval",
        "approved",
        "rejected",
        "escalated"
    ] = "draft"
    audit_events: list[AuditEvent] = []
```

### 8.2 Nodes

#### Node 1: Parse Intent

Purpose:

- Extract material, quantity, location, delivery, payment terms, and preferences.

Inputs:

- User message
- Existing RFQ state

Outputs:

- Updated RFQ draft
- Extraction confidence

#### Node 2: Validate RFQ

Purpose:

- Check required fields
- Detect ambiguous values
- Decide whether workflow can continue

Outputs:

- Missing fields
- Validation result

#### Node 3: Clarification Planner

Purpose:

- Generate focused questions only for missing or ambiguous fields

Rules:

- Ask no more than 3–5 questions at a time
- Avoid repeating answered questions
- Prioritize fields required for supplier matching

#### Node 4: Supplier Search

Purpose:

- Retrieve supplier candidates from catalog and vector search

Tool type:

- Deterministic backend tool

#### Node 5: Supplier Scoring

Purpose:

- Rank offers using deterministic scoring

Formula example:

```text
score =
  0.30 * price_score +
  0.25 * delivery_score +
  0.20 * availability_score +
  0.15 * payment_terms_score +
  0.10 * reliability_score
```

#### Node 6: Credit Check

Purpose:

- Determine if requested payment terms are eligible or require review

#### Node 7: Recommendation

Purpose:

- Generate business-readable recommendation with tradeoffs

#### Node 8: Approval Gate

Purpose:

- Stop workflow before irreversible action
- Present next actions to user

#### Node 9: Artifact Generator

Purpose:

- Generate RFQ draft, supplier outreach, PO draft, or credit summary

## 9. Data Model

### 9.1 RFQDraft

```python
class RFQDraft(BaseModel):
    material_category: str | None = None
    material_name: str | None = None
    specification: str | None = None
    quantity: float | None = None
    unit: str | None = None
    delivery_city: str | None = None
    delivery_district: str | None = None
    delivery_site: str | None = None
    delivery_deadline: str | None = None
    project_name: str | None = None
    payment_preference: str | None = None
    optimization_preference: Literal[
        "lowest_price",
        "fastest_delivery",
        "balanced",
        "payment_terms"
    ] | None = None
    split_delivery_acceptable: bool | None = None
    certification_requirements: list[str] = []
    notes: str | None = None
```

### 9.2 Supplier

```python
class Supplier(BaseModel):
    supplier_id: str
    name: str
    cities_served: list[str]
    material_categories: list[str]
    certifications: list[str]
    reliability_score: float
    payment_terms_supported: list[str]
    average_delivery_days: int
```

### 9.3 SupplierOffer

```python
class SupplierOffer(BaseModel):
    supplier_id: str
    supplier_name: str
    unit_price_sar: float
    available_quantity: float
    delivery_days: int
    payment_terms: str
    reliability_score: float
    compliance_notes: list[str]
    constraints: list[str]
    total_price_sar: float
```

### 9.4 CreditCheckResult

```python
class CreditCheckResult(BaseModel):
    status: Literal[
        "eligible",
        "conditionally_eligible",
        "finance_approval_required",
        "not_eligible",
        "missing_information"
    ]
    estimated_order_value_sar: float
    requested_terms: str | None
    credit_limit_sar: float | None
    current_utilization_sar: float | None
    reason_codes: list[str]
    required_actions: list[str]
```

## 10. API Endpoints

### 10.1 Start Workflow

```http
POST /api/workflows/rfq/start
```

Request:

```json
{
  "message": "Need 500 tons of 16mm rebar in Riyadh next week, 60-day payment preferred.",
  "user_id": "user_123",
  "company_id": "company_456"
}
```

Response:

```json
{
  "workflow_id": "wf_001",
  "status": "needs_clarification",
  "rfq": {},
  "questions": []
}
```

### 10.2 Continue Workflow

```http
POST /api/workflows/rfq/{workflow_id}/message
```

### 10.3 Get Workflow State

```http
GET /api/workflows/rfq/{workflow_id}
```

### 10.4 Approve Action

```http
POST /api/workflows/rfq/{workflow_id}/approve
```

Request:

```json
{
  "action": "send_rfq",
  "approved_by": "user_123"
}
```

### 10.5 Generate Artifact

```http
POST /api/workflows/rfq/{workflow_id}/artifacts
```

Request:

```json
{
  "artifact_type": "po_draft"
}
```

## 11. UI Specification

## 11.1 Layout

### Left Panel: Copilot Chat

Features:

- Contractor request input
- Clarifying questions
- Recommendation explanation
- Approval prompts

### Center Panel: RFQ Workspace

Shows live structured RFQ:

- Material
- Spec
- Quantity
- Delivery location
- Delivery deadline
- Project
- Payment terms
- Optimization preference
- Missing fields
- Status badge

### Right Panel: Workflow Trace

Shows:

- Intent parsed
- Missing fields detected
- Supplier catalog searched
- Credit checked
- Recommendation generated
- Awaiting approval
- PO draft generated

### Bottom Panel or Tab: Supplier Comparison

Shows supplier cards/table:

- Name
- Price
- Availability
- Delivery
- Payment terms
- Reliability
- Recommendation badge

### Optional Tab: Eval & Observability

Shows:

- Field extraction accuracy
- Missing-field detection recall
- Supplier recommendation agreement
- Unsafe auto-action rate
- Average latency
- Trace links

## 11.2 Key UI States

- Empty state
- Needs clarification
- Ready for supplier search
- Supplier comparison ready
- Finance approval required
- Awaiting approval
- PO draft ready
- Error/recovery state

## 12. Synthetic Data Requirements

### Supplier Catalog

Create 8–12 suppliers with variation in:

- City coverage
- Material categories
- Price bands
- Payment terms
- Delivery speed
- Reliability
- Certifications
- Quantity capacity

### RFQ Examples

Create 10–20 test RFQs:

- Complete request
- Missing location
- Missing quantity
- Ambiguous material
- Conflicting delivery/payment terms
- Credit limit exceeded
- Split delivery needed
- Supplier unavailable
- Arabic or mixed Arabic-English request, optional

### Credit Profiles

Create 3–5 company profiles:

- Strong credit
- New contractor
- Near credit limit
- Overdue payments
- Missing documents

## 13. Evaluation Plan

### 13.1 Offline Eval Cases

Each eval case should include:

- User input
- Expected extracted fields
- Expected missing fields
- Expected next action
- Expected safety behavior

### 13.2 Metrics

| Metric | Target |
|---|---:|
| Required field extraction accuracy | 95%+ |
| Missing-field detection recall | 98%+ |
| Unsafe auto-action rate | 0% |
| Supplier recommendation agreement | 85%+ |
| Credit policy decision accuracy | 95%+ |
| Average workflow latency | < 8–12 sec |

### 13.3 Regression Tests

Run tests before changes to:

- Prompts
- Supplier scoring logic
- Credit policy rules
- RFQ schema
- Agent routing logic

## 14. Guardrails

The agent must not:

- Invent suppliers outside the catalog
- Send RFQs without approval
- Generate final POs without approval
- Promise credit approval without policy result
- Ignore missing required fields
- Hide uncertainty
- Treat generated supplier offers as real external responses

The agent should:

- Ask clarifying questions
- Show confidence and missing fields
- Cite internal data sources where applicable
- Explain tradeoffs
- Escalate credit exceptions
- Preserve audit logs

## 15. Demo Script

### Step 1

User:

> “Need 500 tons 16mm rebar in Riyadh next week. Cheapest supplier, 60-day payment preferred.”

Expected:

- Agent extracts fields
- Agent asks for project/site, exact delivery location, certification, split delivery

### Step 2

User:

> “Project Al Yasmin Villas, north Riyadh. Standard Saudi grade is fine. Split delivery is okay if cheaper.”

Expected:

- RFQ becomes valid enough for supplier matching
- System searches suppliers

### Step 3

System shows supplier comparison.

Expected:

- Supplier A fastest
- Supplier B best payment terms
- Supplier C lowest price but split delivery

### Step 4

System recommends balanced option.

Expected:

- Recommendation explains tradeoffs
- Credit check flags conditional eligibility or finance approval

### Step 5

User approves RFQ outreach.

Expected:

- System generates RFQ draft
- Shows approval event in audit log
- No real external message sent unless demo webhook is enabled

### Step 6

User requests PO draft.

Expected:

- System generates draft PO marked pending approval

## 16. Implementation Phases

### Phase 1: Polished Vertical Slice

- CopilotKit UI
- FastAPI backend
- LangGraph RFQ workflow
- Synthetic supplier data
- Supplier scoring tool
- Credit policy tool
- Approval gate
- RFQ/PO draft generation

### Phase 2: Observability and Evals

- Langfuse traces
- Promptfoo evals
- pytest policy tests
- Basic dashboard metrics

### Phase 3: Retrieval and RAG

- Postgres/pgvector
- Supplier documents
- Catalog specs
- Policy documents
- Source-grounded recommendations

### Phase 4: Automation

- n8n webhook for approval simulation
- Email/SMS mock supplier outreach
- Finance escalation flow

### Phase 5: Extensions

- Arabic/mixed-language input
- Whisper voice request
- Supplier response ingestion
- More material categories
- Multi-agent decomposition

## 17. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Demo feels like a chatbot | Show structured RFQ state, tools, approvals, and trace |
| Agent hallucinates suppliers | Restrict supplier recommendations to catalog tool results |
| Too much scope | Build one RFQ-to-PO workflow well |
| Credit workflow seems fake | Use simple transparent policy rules and label as prototype |
| UI feels unfinished | Prioritize command-center layout and realistic sample data |
| Slow responses | Cache supplier data and keep model calls limited |
| Interviewer asks about production | Discuss evals, observability, RBAC, audit trails, retries, queues |

## 18. What to Emphasize in Interview

- This is not an autonomous procurement bot; it is an approval-gated workflow agent.
- The LLM handles ambiguity, language, and explanation.
- Deterministic tools handle validation, scoring, credit policy, and artifact generation.
- The system is designed for observability and regression testing.
- The prototype is narrow by design but maps cleanly to Watad’s broader AridOS vision.

## 19. Definition of Done

The prototype is demo-ready when:

- A user can complete the scripted RFQ flow end to end
- The agent asks sensible clarifying questions
- The RFQ state updates visibly
- Supplier comparison is generated from mock data
- Credit status is shown
- Approval is required before action
- RFQ or PO draft is generated
- Workflow trace is visible
- At least 10 eval cases exist
- The UI feels credible enough for a senior interview demo
