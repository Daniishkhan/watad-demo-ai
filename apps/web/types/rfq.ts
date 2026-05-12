export type OptimizationPreference =
  | "lowest_price"
  | "fastest_delivery"
  | "balanced"
  | "payment_terms";

export type RFQWorkflowStatus =
  | "draft"
  | "needs_clarification"
  | "ready_for_supplier_search"
  | "supplier_shortlist_ready"
  | "recommendation_ready"
  | "finance_approval_required"
  | "credit_not_eligible"
  | "credit_missing_information"
  | "draft_artifacts_ready"
  | "approval_recorded"
  | "approval_rejected";

export type ApprovalAction =
  | "finance_review"
  | "send_rfq_to_suppliers"
  | "issue_purchase_order";

export type ApprovalStatus = "pending" | "approved" | "rejected";

export interface RFQDraft {
  material_category: string | null;
  material_name: string | null;
  specification: string | null;
  quantity: number | null;
  unit: string | null;
  delivery_city: string | null;
  delivery_district: string | null;
  delivery_site: string | null;
  delivery_deadline: string | null;
  project_name: string | null;
  payment_preference: string | null;
  optimization_preference: OptimizationPreference | null;
  split_delivery_acceptable: boolean | null;
  certification_requirements: string[];
  notes: string | null;
}

export interface SupplierCandidate {
  supplier_id: string;
  supplier_name: string;
  fit_score: number;
  unit_price_sar: number;
  available_quantity: number;
  delivery_days: number;
  payment_terms: string[];
  reliability_score: number;
  strengths: string[];
  risks: string[];
  total_price_sar: number;
}

export interface AwardAlternative {
  supplier_id: string;
  supplier_name: string;
  reason: string;
}

export interface AwardRecommendation {
  recommended_supplier_id: string;
  recommended_supplier_name: string;
  optimization_goal: string;
  reason: string;
  estimated_total_price_sar: number;
  tradeoffs: string[];
  alternatives: AwardAlternative[];
}

export interface CreditCheckResult {
  status:
    | "eligible"
    | "conditionally_eligible"
    | "finance_approval_required"
    | "not_eligible"
    | "missing_information";
  estimated_order_value_sar: number;
  requested_terms: string | null;
  credit_limit_sar: number | null;
  current_utilization_sar: number | null;
  finance_approval_required: boolean;
  reason_codes: string[];
  required_actions: string[];
  missing_documents: string[];
}

export interface ApprovalRequest {
  approval_id: string;
  workflow_id: string;
  action: ApprovalAction;
  approver_role: string;
  status: ApprovalStatus;
  message: string;
  decided_by: string | null;
  decided_at: string | null;
  created_at: string;
}

export interface GeneratedDocument {
  document_id: string;
  workflow_id: string;
  document_type:
    | "rfq_draft"
    | "supplier_outreach_draft"
    | "award_recommendation_memo"
    | "po_preview";
  title: string;
  status: "draft" | "pending_approval" | "approved";
  requires_approval_before_send: boolean;
  content: Record<string, unknown>;
}

export interface WorkflowMessage {
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface AuditEvent {
  event_type: string;
  details: Record<string, unknown>;
  created_at: string;
}

export interface RFQWorkflowState {
  workflow_id: string;
  user_id: string;
  company_id: string | null;
  status: RFQWorkflowStatus;
  rfq: RFQDraft;
  missing_fields: string[];
  questions: string[];
  supplier_candidates: SupplierCandidate[];
  recommendation: AwardRecommendation | null;
  credit_check: CreditCheckResult | null;
  approval_requests: ApprovalRequest[];
  generated_documents: GeneratedDocument[];
  messages: WorkflowMessage[];
  audit_events: AuditEvent[];
}
