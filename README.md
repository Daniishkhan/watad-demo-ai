# AridOS RFQ Copilot

Prototype agentic procurement workflow for Watad, organized as a uv workspace monorepo.
The current MVP has a FastAPI + LangGraph backend in `apps/api/` and a Next.js
CopilotKit operator console in `apps/web/`.

## Repository Layout

```text
apps/api/      FastAPI + LangGraph backend package
apps/web/      Next.js + CopilotKit RFQ operator console
docs/          product, architecture, data, and workflow specs
infra/         local Docker Compose services
tests/         unit, integration, and eval test layers
packages/      future shared packages only when needed
```

## Quick Start

```bash
make setup
make infra-up
make run
make test
```

Run the backend and UI locally:

```bash
uv run uvicorn watad.api:app --host 127.0.0.1 --port 8000
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The CopilotKit runtime reads the root `.env`, so
`OPENAI_API_KEY` must be present there for real chat runs. The frontend proxies
backend calls to `http://127.0.0.1:8000` by default; override with
`WATAD_API_BASE_URL` if needed.

Demo path:

1. Click **Start sample RFQ** in the chat suggestions.
2. Confirm the RFQ workspace shows 3 suppliers, Riyadh Metals as the recommendation,
   finance approval required, and generated draft documents.
3. Type `Approve the finance review.` in the Copilot chat.
4. Confirm the workflow status changes to `Approval recorded`.

Before opening a PR, run:

```bash
make ci
cd apps/web && npm run typecheck && npm run lint && npm run build
```

Useful commands:

```bash
make check             # local commit gates: lint + typecheck + all tests
make coverage          # test coverage report
make install-hooks     # install pre-commit and commit-msg hooks
```

Read `AGENTS.md` for contributor guidance and `docs/workflow.md` for branching, testing, and PR process.
