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
make setup
make infra-up
make run
make test
```

Before opening a PR, run:

```bash
make ci
```

Useful commands:

```bash
make check             # local commit gates: lint + typecheck + all tests
make coverage          # test coverage report
make install-hooks     # install pre-commit and commit-msg hooks
```

Read `AGENTS.md` for contributor guidance and `docs/workflow.md` for branching, testing, and PR process.
