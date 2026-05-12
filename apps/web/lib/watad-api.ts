import type { ApprovalAction, RFQWorkflowState } from "@/types/rfq";

const API_PREFIX = "/api/watad";
const DEMO_USER_ID = "watad-operator";
const DEMO_COMPANY_ID = "company_strong";

export async function startRfqWorkflow(message: string): Promise<RFQWorkflowState> {
  return watadRequest<RFQWorkflowState>("/api/workflows/rfq/start", {
    method: "POST",
    body: JSON.stringify({
      message,
      user_id: DEMO_USER_ID,
      company_id: DEMO_COMPANY_ID,
    }),
  });
}

export async function sendRfqWorkflowMessage(
  workflowId: string,
  message: string,
): Promise<RFQWorkflowState> {
  return watadRequest<RFQWorkflowState>(`/api/workflows/rfq/${workflowId}/message`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function getRfqWorkflow(workflowId: string): Promise<RFQWorkflowState> {
  return watadRequest<RFQWorkflowState>(`/api/workflows/rfq/${workflowId}`);
}

export async function approveRfqWorkflowAction(
  workflowId: string,
  action: ApprovalAction,
): Promise<RFQWorkflowState> {
  return watadRequest<RFQWorkflowState>(`/api/workflows/rfq/${workflowId}/approve`, {
    method: "POST",
    body: JSON.stringify({
      action,
      decided_by: DEMO_USER_ID,
    }),
  });
}

export async function rejectRfqWorkflowAction(
  workflowId: string,
  action: ApprovalAction,
): Promise<RFQWorkflowState> {
  return watadRequest<RFQWorkflowState>(`/api/workflows/rfq/${workflowId}/reject`, {
    method: "POST",
    body: JSON.stringify({
      action,
      decided_by: DEMO_USER_ID,
    }),
  });
}

async function watadRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await readError(response);
    throw new Error(detail || `Watad API request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

async function readError(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    return response.text();
  }

  const payload = (await response.json()) as { detail?: unknown };
  return typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
}
