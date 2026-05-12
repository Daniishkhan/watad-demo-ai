"use client";

import {
  AlertTriangle,
  ArrowRight,
  BadgeCheck,
  Boxes,
  Building2,
  Check,
  Clock3,
  FileText,
  Gauge,
  Landmark,
  Loader2,
  MapPin,
  PackageCheck,
  RefreshCcw,
  Send,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Truck,
  WalletCards,
} from "lucide-react";
import {
  CopilotChat,
  CopilotKit,
  useAgentContext,
  useConfigureSuggestions,
  useFrontendTool,
} from "@copilotkit/react-core/v2";
import { FormEvent, useCallback, useMemo, useRef, useState } from "react";
import { z } from "zod";
import {
  approveRfqWorkflowAction,
  getRfqWorkflow,
  rejectRfqWorkflowAction,
  sendRfqWorkflowMessage,
  startRfqWorkflow,
} from "@/lib/watad-api";
import type {
  ApprovalAction,
  ApprovalRequest,
  AuditEvent,
  GeneratedDocument,
  RFQWorkflowState,
  RFQWorkflowStatus,
  SupplierCandidate,
} from "@/types/rfq";

const DEMO_PROMPT =
  "Need 80 tons of 16mm rebar for Project Qiddiya Stadium, delivery to North Riyadh by 2026-06-20. Prefer 60 day payment terms and balanced optimization. SASO certification required. Split delivery is acceptable.";

const WORKFLOW_STEPS = [
  { label: "Intake", event: "intake_parsed" },
  { label: "Validate", event: "rfq_validated" },
  { label: "Shortlist", event: "supplier_matching_completed" },
  { label: "Compare", event: "offer_comparison_completed" },
  { label: "Credit", event: "credit_eligibility_completed" },
  { label: "Approval", event: "approval_request_created" },
  { label: "Docs", event: "draft_documents_generated" },
] as const;

const STATUS_LABELS: Record<RFQWorkflowStatus, string> = {
  draft: "Draft",
  needs_clarification: "Needs clarification",
  ready_for_supplier_search: "Ready for supplier search",
  supplier_shortlist_ready: "Supplier shortlist ready",
  recommendation_ready: "Recommendation ready",
  finance_approval_required: "Finance approval required",
  credit_not_eligible: "Credit not eligible",
  credit_missing_information: "Credit missing information",
  draft_artifacts_ready: "Draft artifacts ready",
  approval_recorded: "Approval recorded",
  approval_rejected: "Approval rejected",
};

const ACTION_LABELS: Record<ApprovalAction, string> = {
  finance_review: "Finance review",
  send_rfq_to_suppliers: "Send RFQ",
  issue_purchase_order: "Issue PO",
};

export function RfqConsole() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" useSingleEndpoint={false}>
      <RfqConsoleInner />
    </CopilotKit>
  );
}

function RfqConsoleInner() {
  const [workflow, setWorkflow] = useState<RFQWorkflowState | null>(null);
  const workflowRef = useRef<RFQWorkflowState | null>(null);
  const [operatorInput, setOperatorInput] = useState(DEMO_PROMPT);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notice, setNotice] = useState("Ready for RFQ intake");
  const [error, setError] = useState<string | null>(null);

  const pendingApproval = workflow?.approval_requests.find(
    (approval) => approval.status === "pending",
  );

  const commitWorkflow = useCallback((nextWorkflow: RFQWorkflowState) => {
    workflowRef.current = nextWorkflow;
    setWorkflow(nextWorkflow);
  }, []);

  const runStartWorkflow = useCallback(async (message: string) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const nextWorkflow = await startRfqWorkflow(message);
      commitWorkflow(nextWorkflow);
      setNotice(`Workflow ${nextWorkflow.workflow_id} started`);
      return nextWorkflow;
    } catch (err) {
      const message = getErrorMessage(err);
      setError(message);
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, [commitWorkflow]);

  const runWorkflowMessage = useCallback(
    async (message: string) => {
      const activeWorkflow = workflowRef.current;
      if (!activeWorkflow) {
        return runStartWorkflow(message);
      }

      setIsSubmitting(true);
      setError(null);
      try {
        const nextWorkflow = await sendRfqWorkflowMessage(activeWorkflow.workflow_id, message);
        commitWorkflow(nextWorkflow);
        setNotice(`Workflow ${nextWorkflow.workflow_id} updated`);
        return nextWorkflow;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [commitWorkflow, runStartWorkflow],
  );

  const refreshWorkflow = useCallback(async () => {
    const activeWorkflow = workflowRef.current;
    if (!activeWorkflow) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const nextWorkflow = await getRfqWorkflow(activeWorkflow.workflow_id);
      commitWorkflow(nextWorkflow);
      setNotice(`Workflow ${nextWorkflow.workflow_id} refreshed`);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }, [commitWorkflow]);

  const decideApproval = useCallback(
    async (action: ApprovalAction, decision: "approve" | "reject") => {
      const activeWorkflow = workflowRef.current;
      if (!activeWorkflow) {
        throw new Error("No workflow is active");
      }

      setIsSubmitting(true);
      setError(null);
      try {
        const nextWorkflow =
          decision === "approve"
            ? await approveRfqWorkflowAction(activeWorkflow.workflow_id, action)
            : await rejectRfqWorkflowAction(activeWorkflow.workflow_id, action);
        commitWorkflow(nextWorkflow);
        setNotice(`${ACTION_LABELS[action]} ${decision === "approve" ? "approved" : "rejected"}`);
        return nextWorkflow;
      } catch (err) {
        const message = getErrorMessage(err);
        setError(message);
        throw err;
      } finally {
        setIsSubmitting(false);
      }
    },
    [commitWorkflow],
  );

  const submitOperatorInput = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const message = operatorInput.trim();
    if (!message) {
      return;
    }

    await runWorkflowMessage(message);
    setOperatorInput("");
  };

  const agentContext = useMemo(
    () => ({
      active_workflow: workflow
        ? {
            workflow_id: workflow.workflow_id,
            status: workflow.status,
            rfq: workflow.rfq,
            missing_fields: workflow.missing_fields,
            questions: workflow.questions,
            supplier_count: workflow.supplier_candidates.length,
            recommendation: workflow.recommendation,
            credit_check: workflow.credit_check,
            pending_approvals: workflow.approval_requests.filter(
              (approval) => approval.status === "pending",
            ),
            document_count: workflow.generated_documents.length,
          }
        : null,
    }),
    [workflow],
  );

  useAgentContext({
    description: "Current Watad RFQ workflow state rendered in the operator console.",
    value: JSON.stringify(agentContext),
  });

  useConfigureSuggestions({
    available: "always",
    suggestions: [
      {
        title: "Start sample RFQ",
        message: DEMO_PROMPT,
      },
      {
        title: "Ask for blockers",
        message: "What is blocking this RFQ from being sent to suppliers?",
      },
      {
        title: "Approval summary",
        message: "Summarize the pending approval and what will happen next.",
      },
    ],
  });

  useFrontendTool(
    {
      name: "start_rfq_workflow",
      description:
        "Start a Watad RFQ workflow from the user's procurement request. Use this when no workflow is active or the user asks to begin a new RFQ.",
      parameters: z.object({
        message: z.string().min(1).describe("The full procurement request from the user."),
      }),
      handler: async ({ message }) =>
        summarizeToolResult(
          workflowRef.current ? await runWorkflowMessage(message) : await runStartWorkflow(message),
        ),
    },
    [runStartWorkflow, runWorkflowMessage],
  );

  useFrontendTool(
    {
      name: "send_rfq_workflow_message",
      description:
        "Send a clarification or follow-up message into the active Watad RFQ workflow. If no workflow is active, this starts one.",
      parameters: z.object({
        message: z.string().min(1).describe("The user's clarification or follow-up message."),
      }),
      handler: async ({ message }) => summarizeToolResult(await runWorkflowMessage(message)),
    },
    [runWorkflowMessage],
  );

  useFrontendTool(
    {
      name: "approve_workflow_action",
      description:
        "Approve or reject a pending human-gated RFQ workflow action. Use only after the user explicitly asks for an approval decision.",
      parameters: z.object({
        action: z
          .enum(["finance_review", "send_rfq_to_suppliers", "issue_purchase_order"])
          .describe("The pending workflow action to decide."),
        decision: z.enum(["approve", "reject"]).describe("The user's decision."),
      }),
      handler: async ({ action, decision }) =>
        summarizeToolResult(await decideApproval(action, decision)),
    },
    [decideApproval],
  );

  const completedEvents = new Set(workflow?.audit_events.map((event) => event.event_type) ?? []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark">
            <Sparkles size={20} />
          </div>
          <div>
            <p className="eyebrow">Watad AridOS</p>
            <h1>RFQ Copilot</h1>
          </div>
        </div>
        <div className="topbar-status">
          <span className="status-dot" />
          <span>{workflow ? STATUS_LABELS[workflow.status] : "No active workflow"}</span>
          <button
            className="icon-button"
            type="button"
            aria-label="Refresh workflow"
            title="Refresh workflow"
            onClick={refreshWorkflow}
            disabled={!workflow || isSubmitting}
          >
            <RefreshCcw size={16} />
          </button>
        </div>
      </header>

      <section className="workspace-grid">
        <aside className="chat-column">
          <div className="surface chat-surface">
            <div className="surface-heading">
              <div>
                <p className="eyebrow">Copilot</p>
                <h2>Procurement chat</h2>
              </div>
              {isSubmitting ? <Loader2 className="spin" size={18} /> : <BadgeCheck size={18} />}
            </div>

            <div className="quick-actions">
              <button type="button" onClick={() => setOperatorInput(DEMO_PROMPT)}>
                <PackageCheck size={15} />
                Sample RFQ
              </button>
              <button
                type="button"
                onClick={() => setOperatorInput("The delivery site is North Riyadh.")}
              >
                <MapPin size={15} />
                Site detail
              </button>
            </div>

            <form className="operator-form" onSubmit={submitOperatorInput}>
              <textarea
                value={operatorInput}
                onChange={(event) => setOperatorInput(event.target.value)}
                aria-label="RFQ message"
                placeholder="Enter an RFQ request or clarification"
                rows={5}
              />
              <button type="submit" disabled={isSubmitting || !operatorInput.trim()}>
                {isSubmitting ? <Loader2 className="spin" size={16} /> : <Send size={16} />}
                {workflow ? "Send Update" : "Run RFQ"}
              </button>
            </form>

            <div className="chat-frame">
              <CopilotChat
                agentId="default"
                className="copilot-chat"
                labels={{
                  modalHeaderTitle: "RFQ Copilot",
                  welcomeMessageText: "Send a procurement request and I will run the RFQ workflow.",
                  chatInputPlaceholder: "Ask about this RFQ or approve a pending action",
                }}
                onError={(event) => {
                  if ("error" in event) {
                    setError(event.error.message);
                  }
                }}
              />
            </div>
          </div>
        </aside>

        <section className="main-column">
          <div className="status-strip">
            {WORKFLOW_STEPS.map((step, index) => {
              const complete = completedEvents.has(step.event);
              return (
                <div
                  className={complete ? "step step-complete" : "step"}
                  key={step.event}
                  aria-label={`${step.label} ${complete ? "complete" : "pending"}`}
                >
                  <span>{complete ? <Check size={13} /> : index + 1}</span>
                  <p>{step.label}</p>
                </div>
              );
            })}
          </div>

          <div className="surface rfq-surface">
            <div className="surface-heading">
              <div>
                <p className="eyebrow">Workspace</p>
                <h2>{workflow?.workflow_id ?? "New RFQ"}</h2>
              </div>
              <StatusPill status={workflow?.status} />
            </div>

            {error ? (
              <div className="alert-row">
                <AlertTriangle size={16} />
                <span>{error}</span>
              </div>
            ) : (
              <div className="notice-row">
                <Gauge size={16} />
                <span>{notice}</span>
              </div>
            )}

            <RfqSnapshot workflow={workflow} />
          </div>

          <div className="surface supplier-surface">
            <div className="surface-heading">
              <div>
                <p className="eyebrow">Supplier shortlist</p>
                <h2>{workflow?.supplier_candidates.length ?? 0} candidates</h2>
              </div>
              <Truck size={18} />
            </div>
            <SupplierList suppliers={workflow?.supplier_candidates ?? []} />
          </div>

          <div className="split-row">
            <RecommendationPanel workflow={workflow} />
            <CreditPanel workflow={workflow} />
          </div>
        </section>

        <aside className="right-column">
          <ApprovalsPanel
            approvals={workflow?.approval_requests ?? []}
            isSubmitting={isSubmitting}
            onDecision={decideApproval}
          />
          <DocumentsPanel documents={workflow?.generated_documents ?? []} />
          <AuditPanel events={workflow?.audit_events ?? []} />
          {pendingApproval ? (
            <div className="approval-callout">
              <ShieldCheck size={18} />
              <span>{ACTION_LABELS[pendingApproval.action]} is waiting on a human gate.</span>
            </div>
          ) : null}
        </aside>
      </section>
    </main>
  );
}

function RfqSnapshot({ workflow }: { workflow: RFQWorkflowState | null }) {
  const rfq = workflow?.rfq;
  const fields = [
    {
      label: "Material",
      value: [rfq?.material_name, rfq?.specification].filter(Boolean).join(" / "),
      icon: Boxes,
    },
    {
      label: "Quantity",
      value: rfq?.quantity ? `${formatNumber(rfq.quantity)} ${rfq.unit ?? ""}`.trim() : null,
      icon: PackageCheck,
    },
    {
      label: "Delivery",
      value: [rfq?.delivery_city, rfq?.delivery_site].filter(Boolean).join(" / "),
      icon: MapPin,
    },
    {
      label: "Deadline",
      value: rfq?.delivery_deadline,
      icon: Clock3,
    },
    {
      label: "Terms",
      value: rfq?.payment_preference,
      icon: WalletCards,
    },
    {
      label: "Project",
      value: rfq?.project_name,
      icon: Building2,
    },
  ];

  return (
    <div className="rfq-grid">
      {fields.map((field) => {
        const Icon = field.icon;
        return (
          <div className="metric-cell" key={field.label}>
            <Icon size={16} />
            <p>{field.label}</p>
            <strong>{field.value || "Pending"}</strong>
          </div>
        );
      })}
      <div className="questions-cell">
        <p>Clarifications</p>
        {workflow?.questions.length ? (
          <ul>
            {workflow.questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        ) : (
          <span>No open questions</span>
        )}
      </div>
    </div>
  );
}

function SupplierList({ suppliers }: { suppliers: SupplierCandidate[] }) {
  if (suppliers.length === 0) {
    return <EmptyState icon={Truck} title="No suppliers yet" />;
  }

  return (
    <div className="supplier-list">
      {suppliers.map((supplier, index) => (
        <div className="supplier-row" key={supplier.supplier_id}>
          <div className="rank-badge">{index + 1}</div>
          <div>
            <strong>{supplier.supplier_name}</strong>
            <p>
              {formatCurrency(supplier.total_price_sar)} · {supplier.delivery_days} days ·{" "}
              {formatPercent(supplier.fit_score)} fit
            </p>
          </div>
          <div className="supplier-meta">
            <span>{formatPercent(supplier.reliability_score)} reliability</span>
            <span>{supplier.payment_terms.join(", ")}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function RecommendationPanel({ workflow }: { workflow: RFQWorkflowState | null }) {
  const recommendation = workflow?.recommendation;

  return (
    <div className="surface compact-surface">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">Award</p>
          <h2>Recommendation</h2>
        </div>
        <Landmark size={18} />
      </div>
      {recommendation ? (
        <div className="recommendation-body">
          <strong>{recommendation.recommended_supplier_name}</strong>
          <p>{recommendation.reason}</p>
          <span>{formatCurrency(recommendation.estimated_total_price_sar)}</span>
        </div>
      ) : (
        <EmptyState icon={Landmark} title="Awaiting comparison" />
      )}
    </div>
  );
}

function CreditPanel({ workflow }: { workflow: RFQWorkflowState | null }) {
  const credit = workflow?.credit_check;

  return (
    <div className="surface compact-surface">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">Credit</p>
          <h2>Eligibility</h2>
        </div>
        <WalletCards size={18} />
      </div>
      {credit ? (
        <div className="credit-body">
          <strong>{credit.status.replaceAll("_", " ")}</strong>
          <p>{formatCurrency(credit.estimated_order_value_sar)} estimated order value</p>
          <div className="tag-row">
            {credit.reason_codes.map((code) => (
              <span key={code}>{code.replaceAll("_", " ")}</span>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState icon={WalletCards} title="Pending recommendation" />
      )}
    </div>
  );
}

function ApprovalsPanel({
  approvals,
  isSubmitting,
  onDecision,
}: {
  approvals: ApprovalRequest[];
  isSubmitting: boolean;
  onDecision: (action: ApprovalAction, decision: "approve" | "reject") => Promise<RFQWorkflowState>;
}) {
  return (
    <div className="surface side-surface">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">Human gates</p>
          <h2>Approvals</h2>
        </div>
        <ShieldCheck size={18} />
      </div>
      {approvals.length === 0 ? (
        <EmptyState icon={ShieldCheck} title="No pending gates" />
      ) : (
        <div className="approval-list">
          {approvals.map((approval) => (
            <div className="approval-row" key={approval.approval_id}>
              <div>
                <strong>{ACTION_LABELS[approval.action]}</strong>
                <p>{approval.message}</p>
                <span>{approval.status}</span>
              </div>
              {approval.status === "pending" ? (
                <div className="decision-buttons">
                  <button
                    type="button"
                    aria-label={`Approve ${ACTION_LABELS[approval.action]}`}
                    title={`Approve ${ACTION_LABELS[approval.action]}`}
                    disabled={isSubmitting}
                    onClick={() => onDecision(approval.action, "approve")}
                  >
                    <ThumbsUp size={15} />
                  </button>
                  <button
                    type="button"
                    aria-label={`Reject ${ACTION_LABELS[approval.action]}`}
                    title={`Reject ${ACTION_LABELS[approval.action]}`}
                    disabled={isSubmitting}
                    onClick={() => onDecision(approval.action, "reject")}
                  >
                    <ThumbsDown size={15} />
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DocumentsPanel({ documents }: { documents: GeneratedDocument[] }) {
  return (
    <div className="surface side-surface">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">Artifacts</p>
          <h2>Documents</h2>
        </div>
        <FileText size={18} />
      </div>
      {documents.length === 0 ? (
        <EmptyState icon={FileText} title="No drafts yet" />
      ) : (
        <div className="document-list">
          {documents.map((document) => (
            <div className="document-row" key={document.document_id}>
              <FileText size={15} />
              <div>
                <strong>{document.title}</strong>
                <p>{document.document_type.replaceAll("_", " ")}</p>
              </div>
              <ArrowRight size={14} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function AuditPanel({ events }: { events: AuditEvent[] }) {
  return (
    <div className="surface side-surface audit-surface">
      <div className="surface-heading">
        <div>
          <p className="eyebrow">Trace</p>
          <h2>Workflow</h2>
        </div>
        <Gauge size={18} />
      </div>
      {events.length === 0 ? (
        <EmptyState icon={Gauge} title="No events yet" />
      ) : (
        <ol className="audit-list">
          {events.slice(-8).map((event) => (
            <li key={`${event.event_type}-${event.created_at}`}>
              <span />
              <div>
                <strong>{event.event_type.replaceAll("_", " ")}</strong>
                <p>{formatTime(event.created_at)}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function StatusPill({ status }: { status: RFQWorkflowStatus | undefined }) {
  return <span className="status-pill">{status ? STATUS_LABELS[status] : "Idle"}</span>;
}

function EmptyState({
  icon: Icon,
  title,
}: {
  icon: typeof Truck;
  title: string;
}) {
  return (
    <div className="empty-state">
      <Icon size={18} />
      <span>{title}</span>
    </div>
  );
}

function summarizeToolResult(workflow: RFQWorkflowState) {
  return {
    workflow_id: workflow.workflow_id,
    status: workflow.status,
    missing_fields: workflow.missing_fields,
    questions: workflow.questions,
    supplier_count: workflow.supplier_candidates.length,
    recommended_supplier: workflow.recommendation?.recommended_supplier_name ?? null,
    credit_status: workflow.credit_check?.status ?? null,
    pending_approvals: workflow.approval_requests.filter((approval) => approval.status === "pending"),
    generated_documents: workflow.generated_documents.map((document) => document.title),
  };
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "SAR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatTime(value: string): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}
