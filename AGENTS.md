# Repository Guidelines

## Project Structure & Module Organization

This is a Python 3.12 + TypeScript prototype for the **AridOS RFQ Copilot**, organized as a **uv workspace monorepo** with a **modular monolith** backend and a Next.js CopilotKit UI. Treat `docs/` as source of truth.

```
apps/api/src/watad/   # FastAPI + LangGraph backend
                      # modular monolith: models/, services/, workflows/, api.py
apps/web/             # Next.js + CopilotKit RFQ operator console
packages/             # shared libs only when ≥ 2 members need the same code
tests/{unit,integration,evals}/
docs/                 # specs + workflow process
data/{seed,messy,docs,generated}/
infra/                # docker-compose, migrations, deploy config
pyproject.toml        # workspace root: dev deps + ruff/mypy/pytest
apps/api/pyproject.toml  # workspace member: runtime deps + build config
```

Don't split the backend into multiple services until a runtime constraint demands it. Don't create `packages/shared/` speculatively.

## Build, Test, and Development Commands

- `uv sync --all-packages`: install all workspace members + dev deps from `uv.lock`.
- `make setup`: install dependencies, install Git hooks, and create `.env` if missing.
- `cp .env.example .env`: create local config, then fill provider keys.
- `docker compose -f infra/docker-compose.yml up -d` / `… down`: start or stop local infra (Postgres+pgvector, Redis). Compose project name is pinned to `watad`.
- `uv run watad`: run the backend console-script entrypoint.
- `uv run uvicorn watad.api:app --reload`: run the FastAPI app.
- `cd apps/web && npm install`: install frontend dependencies.
- `cd apps/web && npm run dev`: run the CopilotKit UI on `127.0.0.1:3000`.
- `cd apps/web && npm run typecheck && npm run lint && npm run build`: run frontend gates.
- `uv run pytest`: run the test suite.
- `uv run pytest tests/unit/test_x.py::test_y -v`: run one focused test.
- `uv run pytest -m "not integration and not eval"`: fast unit-only run.
- `uv run pytest -m integration` / `-m eval`: scoped runs for container-backed or LLM-backed tests.
- `uv run pytest --cov=watad`: report coverage.
- `uv run ruff check .`, `uv run ruff format .`, `uv run mypy .`: lint, format, and type-check (mypy is strict).
- `make check` / `make ci`: run local commit gates or CI-equivalent gates.

## Coding Style & Naming Conventions

Python 3.12, 4-space indentation, Ruff defaults from the workspace `pyproject.toml` with a 100-character line length. Prefer typed functions and Pydantic models for workflow state and APIs. Use `snake_case` for modules, functions, variables, and tests; `PascalCase` for classes. Keep deterministic rules in services/tools, not LLM prompts. New backend code lives under `apps/api/src/watad/<module>/` — pick the right module (`services`, `models`, `workflows`) before writing. New frontend code lives under `apps/web/app`, `apps/web/components`, `apps/web/lib`, or `apps/web/types`.

## Testing Guidelines

Pytest uses `pytest-asyncio` automatically. Name files `test_*.py`. Use TDD for pure logic: RFQ validators, normalization, scoring, credit rules, approval state, and ID generation. Mark container-backed tests with `@pytest.mark.integration` and LLM evals with `@pytest.mark.eval`. For LLM agents, write evals that assert schema, required fields, and guardrail violations, not exact text. Use `respx` for HTTP mocks. See `docs/workflow.md` §2 for the four-layer test taxonomy.

## Commit & Pull Request Guidelines

Use GitHub Flow: short-lived branches like `feat/intake-agent`, `fix/supplier-scoring`, `test/rfq-validation`, `chore/infra`, or `docs/workflow`. Do not commit directly to `main`. Use Conventional Commits, e.g. `feat(supplier-matching): add catalog filter`. PRs need a description, linked issue or spec section, and test results. Before merge, run `uv run pytest`, `uv run ruff check .`, and `uv run mypy .`; call out schema, migration, env var, approval, and compliance changes. See `docs/workflow.md` §3-§4 for the full convention and PR checklist.

Install hooks with `make install-hooks`. The pre-commit hook runs repo-wide Ruff fixes, Ruff formatting, strict mypy, and the full pytest suite before every commit. If tests fail, the commit must fail. The commit-msg hook validates Conventional Commit subjects.

## Security & Configuration Tips

Never commit `.env` files or provider keys. Do not fabricate suppliers, creditworthiness, or Watad-private records. RFQs, POs, outreach, non-compliant substitutes, credit approvals, and supplier-risk overrides must remain human-gated — see CLAUDE.md *Guardrails to Preserve* and `docs/agentic.md` §6.7. Public `data/docs/` files are for RAG demos only, not supplier records.
