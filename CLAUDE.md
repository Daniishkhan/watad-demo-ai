# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

Greenfield monorepo for **AridOS RFQ Copilot** — a prototype agentic procurement workflow for Watad (Saudi construction supply / financing). The system is fully specified in `docs/` but **the application code is not yet written**. Only the scaffold exists today: monorepo layout, deps, local infra, lint/test config, and a `main.py` stub. When asked to build a feature, expect to scaffold modules from scratch and write tests first (see *Workflow* below).

## Repository Layout (monorepo)

```
watad/
  apps/
    api/                  # FastAPI + LangGraph backend (modular monolith)
      pyproject.toml      # workspace member: runtime deps + build config
      src/watad/          # Python package (will grow into api/, agents/,
                          # services/, models/, persistence/, workflows/)
    web/                  # Next.js + CopilotKit frontend (NOT YET — add when needed)
  packages/               # internal shared libs (only when real shared code emerges)
  tests/
    unit/                 # pure logic, no I/O, TDD
    integration/          # hits Postgres/Redis containers; @pytest.mark.integration
    evals/                # LLM eval scenarios; @pytest.mark.eval
  docs/                   # specs + workflow process
  data/                   # seed/, messy/, docs/, generated/ — see docs/data_strategy.md
  infra/                  # docker-compose, migrations, deploy config
  pyproject.toml          # workspace root: dev/tooling deps + ruff/mypy/pytest config
  uv.lock                 # single lockfile for the whole workspace
```

**Why a monorepo:** atomic API↔UI changes in one PR, shared `docs/` and `data/`, single CI pipeline. **Why a modular monolith inside `apps/api/`:** one FastAPI app with clear modules is simpler than splitting agents/services/workers into separate processes. Add a worker process only when background jobs or long-running LangGraph executions need independent scaling.

**Boundary discipline:** only promote code into `packages/shared/` when at least two workspace members genuinely need it. Don't speculate.

## Commands

Python 3.12 managed by uv (workspace mode). Local infra via `docker compose`. All deps already declared and resolved into `uv.lock`.

```bash
# Setup
uv sync --all-packages                              # install all workspace members + dev deps
cp .env.example .env                                # then fill in ANTHROPIC_API_KEY etc.
docker compose -f infra/docker-compose.yml up -d    # start Postgres (pgvector) + Redis
docker compose -f infra/docker-compose.yml down     # stop them
docker compose -f infra/docker-compose.yml down -v  # full reset incl. volumes

# Run / develop
uv run watad                                        # console-script entrypoint (apps/api)
uv run uvicorn watad.api:app --reload               # once watad/api.py exists

# Quality gates (run before pushing)
uv run ruff check .                                 # lint
uv run ruff format .                                # format
uv run mypy .                                       # types (strict mode)
uv run pytest                                       # tests
uv run pytest tests/unit/test_x.py::test_y -v       # single test
uv run pytest -m "not integration and not eval"     # fast unit-only run
uv run pytest -m integration                        # integration only (needs containers)
uv run pytest --cov=watad                           # with coverage
```

Local services (defaults from `infra/docker-compose.yml`, project name pinned to `watad`):
- Postgres + pgvector v0.8.2 — `postgresql+asyncpg://watad:watad@localhost:5432/watad`
- Redis — `redis://localhost:6379/0`

## Workflow

### Branching strategy — GitHub Flow

`main` is always shippable and always green. All work happens on short-lived branches that merge back via PR.

- `feat/<scope>` — new behavior (e.g. `feat/intake-agent`, `feat/supplier-scoring`)
- `fix/<scope>` — bug fix
- `test/<scope>` — tests only, no production change
- `chore/<scope>` — tooling, deps, infra
- `docs/<scope>` — docs only
- `refactor/<scope>` — internal change, no behavior delta

Rules:
- Never commit directly to `main`. Open a PR even when working solo — the PR is the review artifact.
- Keep branches < ~3 days old. Long-lived branches collect drift.
- Rebase on `main` before merging to keep history linear; squash-merge if a branch has noisy WIP commits.
- Conventional Commits: `feat: …`, `fix: …`, `test: …`, `chore: …`, `docs: …`, `refactor: …`. Use scopes when helpful: `feat(supplier-matching): …`.

### TDD discipline — write tests first, but only where tests make sense

Not all code in this system is TDD-suitable. Be explicit about which layer you're working in:

| Layer | What it is | Test approach |
|---|---|---|
| **Pure logic** | RFQ validators, material/unit normalization, supplier scoring formula, credit policy rules, approval state machine, ID generation | **TDD unit tests** — write red test → minimal green → refactor. Lives in `tests/unit/`. No I/O, no LLM. |
| **Tools / services** | DB queries, supplier search, audit-log writes, document persistence | **Integration tests** against the real Postgres/Redis containers. Lives in `tests/integration/`. Mark with `@pytest.mark.integration`. |
| **Graph routing** | LangGraph supervisor's transitions between nodes | **Unit tests** with hand-crafted `WorkflowState` objects and mocked agent outputs. No LLM call needed. |
| **LLM-driven agents** | Intake field extraction, clarifying-question generation, recommendation rationale | **Eval scenarios**, not unit tests. Lives in `tests/evals/`. LLM behavior is non-deterministic — assert on schema, presence of required fields, and guardrail violations rather than exact strings. Mark with `@pytest.mark.eval`. |

Operational rules:
1. **Red first.** Don't write a function before there is a failing test that pins down its contract. The test names the behavior.
2. **Smallest green.** Make the test pass with the simplest possible implementation. No speculative branches.
3. **Refactor under green.** Once the test passes, clean up. Tests stay green throughout.
4. **One failing test at a time.** If you discover another missing case, write it down — don't write three failing tests in parallel.
5. **Guardrails get tests.** Every invariant in the *Guardrails to Preserve* section below must have a test that fails if the invariant is violated.

### PR checklist

Before opening a PR (or merging your own):
- [ ] All tests pass: `uv run pytest`
- [ ] Lint clean: `uv run ruff check .`
- [ ] Types clean: `uv run mypy .`
- [ ] New behavior has tests at the appropriate layer (see table above)
- [ ] No secrets in diff (search for `sk-`, `key=`, `password=`)
- [ ] If touching a guardrail (approval gate, supplier catalog boundary, credit policy), the test that protects it is updated/added

## Architecture (planned)

The product is a **multi-agent, approval-gated workflow** running as a single FastAPI process (modular monolith). Read `docs/agentic.md` and `docs/spec.md` before any implementation work — they define the contract every component must conform to. Key load-bearing decisions:

- **Modular monolith inside `apps/api/src/watad/`.** One process, clear modules: `api/` (FastAPI routers), `agents/` (LangGraph agent nodes), `services/` (deterministic tools), `models/` (Pydantic schemas), `persistence/` (SQLAlchemy + repos), `workflows/` (LangGraph graph definitions). Don't split into separate services until a runtime constraint demands it.
- **LangGraph as the control plane.** A supervisor/router node dispatches between specialized agents (Intake, RFQ Structuring, Supplier Matching, Offer Comparison, Credit Eligibility, Approval & Compliance, Document Generation). Routing is deterministic where possible; LLMs are used only for ambiguous classification. See `docs/agentic.md` §6 for the full agent catalog and §8 for the graph.
- **Shared typed `WorkflowState`** flows through every node (`docs/agentic.md` §5, `docs/spec.md` §8.1). All agent I/O is structured — no free-form passing of data between nodes.
- **LLMs handle ambiguity; deterministic services own authority.** RFQ schema validation, supplier scoring, credit policy, permissions, audit logging, ID generation, and persistence are tool calls — never LLM judgment. Tool boundaries are spelled out in `docs/agentic.md` §7.
- **Hard approval gates.** Sending RFQs, issuing POs, approving credit, accepting non-compliant substitutes, and overriding supplier risk are *always* human-gated. The Approval & Compliance Agent (`docs/agentic.md` §6.7) enforces this; do not introduce code paths that bypass it.
- **Stack target:** FastAPI + Pydantic + LangGraph backend (`apps/api/`); Next.js + CopilotKit + shadcn/ui frontend (future `apps/web/`); Postgres + pgvector for catalog/RAG; Redis for state/async; Langfuse (+ optional Phoenix / OTel) for traces; Promptfoo + pytest for evals. See `docs/spec.md` §7.1.

## Data Strategy

Per `docs/data_strategy.md`, mock data is layered intentionally and code should respect the layering:

- **Layer A — `data/seed/`** clean CSVs for deterministic demos (suppliers, materials, buyer profiles, credit policies, taxonomy, historical orders).
- **Layer B — `data/messy/`** intentionally dirty CSVs (mixed Arabic/English, unit variants, ambiguous payment terms) to exercise normalization.
- **Layer C — `data/docs/`** public construction PDFs for RAG demos, tracked in `data/docs/public_source_manifest.csv`. These are **not** Watad supplier records — never present them as such in generated output.
- **Layer D — `data/generated/synthetic_offers.json`** rule-generated supplier offers (not LLM-fabricated).

## Guardrails to Preserve

These are product invariants, not style preferences. Each one must be protected by a test that fails if it's violated. From `docs/agentic.md` §6 and `docs/spec.md` §14:

- The agent must never invent suppliers outside the catalog or fabricate creditworthiness.
- Generated documents (RFQ, PO, outreach) must be marked as drafts until approval is recorded.
- Supplier outreach and PO issuance must not happen automatically, even in demos — gate behind the approval node and/or a feature flag.
- The Supervisor should be deterministic routing first, LLM only for genuinely ambiguous classification (`docs/agentic.md` §6.1 "Senior Design Note").

## Source-of-Truth Documents

When specs and code disagree, the docs are the design intent — but they predate any implementation, so flag conflicts to the user rather than silently reinterpreting.

- `docs/onepager.md` — pitch / scope / non-goals
- `docs/spec.md` — product + technical spec, data models, API endpoints, eval plan
- `docs/agentic.md` — agent catalog, tool boundaries, LangGraph flow, guardrails
- `docs/data_strategy.md` — mock data layering and ingestion plan
- `docs/workflow.md` — branching, TDD layering, commit conventions, PR checklist (engineering process)
