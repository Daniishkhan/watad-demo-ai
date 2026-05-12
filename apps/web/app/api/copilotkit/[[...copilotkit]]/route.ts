import path from "node:path";
import { loadEnvConfig } from "@next/env";
import {
  BuiltInAgent,
  CopilotRuntime,
  createCopilotRuntimeHandler,
} from "@copilotkit/runtime/v2";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const repoRoot = process.cwd().endsWith(path.join("apps", "web"))
  ? path.resolve(process.cwd(), "../..")
  : process.cwd();

loadEnvConfig(repoRoot);

const copilotRuntime = new CopilotRuntime({
  agents: {
    default: new BuiltInAgent({
      model: process.env.COPILOTKIT_MODEL ?? "openai/gpt-4o-mini",
      apiKey: process.env.OPENAI_API_KEY,
      maxSteps: 6,
      prompt: [
        "You are the Watad AridOS RFQ Copilot embedded in an operator console.",
        "Use the available frontend tools to start or update RFQ workflows instead of inventing state.",
        "When the user provides a procurement request, call start_rfq_workflow.",
        "When a workflow exists and the user adds clarification, call send_rfq_workflow_message.",
        "Only call approve_workflow_action when the user explicitly asks to approve a pending human-gated action.",
        "Never fabricate suppliers, credit status, approval records, or documents; summarize only the tool result and visible workflow state.",
        "If the workflow needs clarification, ask the most important missing question in concise operator language.",
      ].join(" "),
    }),
  },
});

const handleCopilotRequest = createCopilotRuntimeHandler({
  runtime: copilotRuntime,
  basePath: "/api/copilotkit",
  cors: true,
});

export const GET = handleCopilotRequest;
export const POST = handleCopilotRequest;
export const OPTIONS = handleCopilotRequest;
