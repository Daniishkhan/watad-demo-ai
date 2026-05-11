# AridOS RFQ Copilot

Prototype agentic procurement workflow for Watad, organized as a uv workspace monorepo.
The backend is the first focus and lives in `apps/api/` as a modular monolith.

## Repository Layout

```text
apps/api/      FastAPI + LangGraph backend package
docs/          product, architecture, data, and workflow specs
infra/         local Docker Compose services
tests/         unit, integration, and eval test layers
packages/      future shared packages only when needed
```

## Quick Start

```bash
uv sync --all-packages
cp .env.example .env
docker compose -f infra/docker-compose.yml up -d
uv run watad
uv run pytest
```

Before opening a PR, run:

```bash
uv run ruff check .
uv run mypy .
uv run pytest
```

Read `AGENTS.md` for contributor guidance and `docs/workflow.md` for branching, testing, and PR process.
