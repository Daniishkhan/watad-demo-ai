# AridOS RFQ Copilot — One-Pager

## Summary

**AridOS RFQ Copilot** is a production-shaped prototype for Watad: a credit-aware procurement agent that helps contractors turn messy material requests into validated RFQs, supplier comparisons, approval-gated outreach, and PO drafts.

The prototype demonstrates how an agentic workflow can support Watad’s construction procurement, financing, and supply-chain operations without behaving like an unsafe “autonomous chatbot.” The system asks clarifying questions, maintains structured RFQ state, calls deterministic backend tools, retrieves supplier/catalog data, checks credit eligibility, and requires human approval before supplier outreach or PO generation.

## Why This Demo

Watad’s AridOS direction is not just a chatbot. It is an agentic operating system for construction procurement. The most valuable pilot should therefore show a realistic workflow slice:

> Contractor request → Clarifying questions → RFQ state → Supplier matching → Credit-aware recommendation → Human approval → PO draft

This directly aligns with the Agentic AI Engineer role: agent architecture, tool integrations, retrieval, evaluation, observability, backend APIs, and human-in-the-loop automation.

## Target User

Primary user:

- Contractor procurement manager
- Watad internal procurement operator
- Commercial/operations team member handling RFQs

Secondary users:

- Supplier relationship manager
- Finance/credit operations analyst
- Construction project manager

## Core Use Case

A contractor enters a vague procurement request:

> “Need 500 tons of 16mm rebar in Riyadh next week. Cheapest supplier if possible, 60-day payment preferred.”

The copilot responds with focused operational questions:

- What project or site is this for?
- What is the exact delivery district or site location?
- Are there required certifications, approved brands, or grade constraints?
- Is split delivery acceptable?
- Should the system optimize for lowest price, fastest delivery, or balanced value?
- Is 60-day payment required, preferred, or optional?

After collecting enough information, the system creates a structured RFQ, searches matching suppliers, compares offers, checks credit eligibility, recommends an award option, and routes supplier outreach or PO generation through approval.

## Product Principles

1. **Ask before acting**
   The agent should not proceed when essential procurement details are missing.

2. **LLM for ambiguity, tools for execution**
   The LLM parses intent, reasons over tradeoffs, and drafts communication. Deterministic backend services validate data, score suppliers, calculate totals, check credit policy, and generate artifacts.

3. **Human approval for irreversible actions**
   Sending RFQs, awarding suppliers, activating financing, and generating final POs require approval.

4. **Stateful, observable workflow**
   The system should expose workflow steps, state changes, traces, and audit logs.

5. **Production-shaped, not production-sized**
   The prototype should be narrow but credible: one workflow executed well rather than many incomplete features.

## Demo Flow

### 1. Natural-language request

The user enters a messy contractor request.

### 2. Clarification phase

The agent detects missing fields and asks only the necessary questions.

### 3. Structured RFQ state

The UI updates a live RFQ object with material, quantity, delivery, payment, project, and approval fields.

### 4. Supplier matching

The backend retrieves matching suppliers from synthetic supplier/catalog data.

### 5. Offer comparison

The system compares suppliers by price, availability, delivery, payment terms, reliability, and constraints.

### 6. Credit-aware recommendation

The system checks simple credit policy rules and flags whether financing or deferred payment requires human review.

### 7. Approval gate

The user approves, edits, rejects, or escalates the recommendation.

### 8. PO/RFQ artifact

The system generates a draft RFQ or PO, clearly marked as pending approval.

## Suggested UI

Use **CopilotKit** for the conversational layer and build a polished pilot command center.

Recommended layout:

- **Left panel:** Copilot chat
- **Center panel:** Live RFQ workspace
- **Right panel:** Workflow status, tool calls, and audit trace
- **Bottom or tabbed section:** Supplier comparison and recommendation
- **Optional tab:** Evaluation and observability dashboard

## Success Criteria

The prototype is successful if it demonstrates:

- Clarifying-question behavior for incomplete RFQs
- Structured RFQ extraction and validation
- Supplier retrieval and comparison
- Credit/payment-term awareness
- Human approval gates
- Traceable workflow state
- Clean backend API boundaries
- Evaluation-ready scenarios
- A polished enough UI to feel like a credible Watad pilot

## Non-Goals

The prototype does not need to include:

- Real supplier integrations
- Real payment execution
- Real credit bureau checks
- Real ERP integration
- Full Arabic support
- Production authentication
- Full procurement lifecycle coverage

These can be described as future phases.

## Interview Positioning

Recommended framing:

> “I intentionally built a focused workflow slice instead of a generic chatbot. The copilot asks for missing procurement details, updates structured RFQ state, calls deterministic tools for supplier matching and credit checks, and requires human approval before supplier outreach or PO creation. The LLM handles ambiguity and reasoning, while the backend owns validation, state, traceability, and execution.”

## Prototype Name

**AridOS RFQ Copilot**

Subtitle:

**Credit-aware procurement agent for contractor RFQs, supplier matching, and approval-gated PO generation.**
