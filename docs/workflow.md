# AridOS RFQ Copilot — Engineering Workflow

This document defines *how* we work on the codebase. The product/architecture specs are in `onepager.md`, `spec.md`, `agentic.md`, and `data_strategy.md`; this file is the engineering process layer.

## 0. Repository Shape — Monorepo + Modular Monolith

The repo is a **uv workspace monorepo**:

```
apps/api/          # FastAPI + LangGraph backend (the only app today)
apps/web/          # Next.js + CopilotKit frontend — added when needed, not now
packages/          # internal shared libs — only when at least 2 members need the same code
tests/             # workspace-wide tests, organized by layer (see §2)
docs/              # specs + this workflow doc
data/              # mock-data layers per docs/data_strategy.md
infra/             # docker-compose, migrations, deploy config
pyproject.toml     # workspace root: dev/tooling deps + ruff/mypy/pytest config
uv.lock            # single lockfile for the whole workspace
```

**Two principles drive this shape:**

1. **Monorepo for atomicity.** Backend, future frontend, docs, infra, fixtures, seed data, and workflow specs stay versioned together. For an approval-gated procurement product, many changes cut across API contracts, data models, evals, and UI flows — atomic PRs matter more than independent deploy cadences.
2. **Modular monolith inside `apps/api/`, not multiple backend services.** One FastAPI app with clear modules (`api/`, `agents/`, `services/`, `models/`, `persistence/`, `workflows/`) is simpler and safer right now. Add a separate worker process *only* when background jobs, queue consumers, or long-running LangGraph executions genuinely need independent scaling. Don't pre-split.

**Monorepo's main downside is tooling complexity once Python and TypeScript both exist.** That stays manageable if we keep boundaries clean: backend owns the OpenAPI schema, frontend consumes generated clients/types later, and CI runs scoped checks per app.

**`packages/` growth criteria:** promote code into `packages/shared/` only when ≥ 2 workspace members genuinely need the same code. Speculative shared libs rot.

## 1. Branching Strategy — GitHub Flow

We use **GitHub Flow**: a single long-lived branch (`main`) plus short-lived topic branches that merge back via Pull Request.

### Why GitHub Flow

- The project is a single-deliverable prototype — no parallel release tracks, no maintenance branches, no hotfix-vs-feature distinction. Git Flow would be overkill.
- `main` is the only branch we ever deploy or demo from, so keeping it always-green is the only invariant we need to protect.
- PRs serve as the review artifact even when working solo — they force a moment of reflection between "I think it works" and "this is on `main`".

### Branch naming

```
feat/<scope>        new behavior
fix/<scope>         bug fix
test/<scope>        tests only, no production change
chore/<scope>       tooling, deps, infra, CI
docs/<scope>        docs only
refactor/<scope>    internal change, no behavior delta
```

`<scope>` should match the area of work — usually an agent, a tool, or a layer. Examples:

- `feat/intake-agent`
- `feat/supplier-scoring`
- `fix/rfq-validator-empty-spec`
- `test/credit-policy-edge-cases`
- `chore/upgrade-langgraph`
- `docs/workflow`

### Branch lifecycle

1. `git checkout main && git pull`
2. `git checkout -b feat/<scope>`
3. Work in tight TDD cycles (see §2). Commit often using Conventional Commits (§3).
4. Before opening a PR: rebase on `main`, run all quality gates, complete the PR checklist (§4).
5. Open PR. Self-review the diff in the GitHub UI before requesting review.
6. Squash-merge if the branch has noisy WIP commits; merge as-is if every commit is meaningful and atomic.
7. Delete the branch after merge.

### Rules

- **Never commit directly to `main`.** Even one-line typo fixes go through a `docs/` branch.
- **Keep branches short-lived** — under 3 days ideally, never more than a week. Long branches collect drift, conflict pain, and review fatigue.
- **One branch, one concern.** If you discover unrelated work mid-branch, stash it, open a separate branch, come back.
- **Rebase, don't merge `main` in.** Linear history is easier to bisect later.

### main branch protection (when this becomes a team repo)

When this is no longer a solo project, configure on GitHub:
- Require PR before merge
- Require status checks to pass (lint, types, tests)
- Require linear history
- Disallow force-push to `main`

## 2. TDD Discipline

We use **test-driven development first**, but we are honest about where TDD does and doesn't apply. LLM-driven behavior is non-deterministic and can't be pinned down by unit assertions; deterministic logic can and must.

### The four layers

| Layer | What it covers | Test approach | Lives in |
|---|---|---|---|
| **Pure logic** | RFQ validators, material/unit normalization, supplier scoring, credit policy rules, approval state machine, ID generation, date resolution | Unit tests, TDD red→green→refactor. No I/O, no LLM, no clock. | `tests/unit/` |
| **Tools / services** | DB queries, supplier search, audit-log writes, document persistence, Redis state | Integration tests against the real Postgres/Redis containers. | `tests/integration/` (mark `@pytest.mark.integration`) |
| **Graph routing** | LangGraph supervisor's transitions between nodes given a state object | Unit tests with hand-crafted `WorkflowState` and mocked agent outputs. | `tests/unit/graph/` |
| **LLM-driven agents** | Intake field extraction, clarifying questions, recommendation rationale, document drafting | Eval scenarios. Assert on output schema, presence of required fields, and guardrail violations — not exact strings. | `tests/evals/` |

### TDD cycle (for the first three layers)

1. **Red.** Write the failing test first. The test name describes the behavior in business terms ("scoring penalizes suppliers that can't meet the deadline"). Run it; confirm it fails for the right reason.
2. **Green.** Write the smallest implementation that makes the test pass. Resist adding speculative branches "while you're in there".
3. **Refactor.** With tests green, clean up names, extract helpers, remove duplication. Tests stay green throughout.
4. **Commit.** Each red→green→refactor loop is typically one commit (`feat: …` or `test: …`). Don't batch many cycles into one commit.

### What *not* to do

- Don't write code first and tests after. The point of TDD is letting the test shape the API.
- Don't write three failing tests in parallel. One at a time keeps the loop tight and the diagnosis fast.
- Don't unit-test LLM output. `assert response.text == "expected sentence"` will be flaky and brittle. Use evals for that.
- Don't mock the database in integration tests. We had `docker compose up` for a reason — mocked queries hide real schema/SQL bugs.
- Don't TDD throwaway scripts (one-off data inspection, ad-hoc explorations). TDD is for code that ships.

### Guardrails are tests

Every invariant in CLAUDE.md's *Guardrails to Preserve* section must have a test that fails if the invariant is violated. Examples:

- *"Supplier outreach must not happen without approval"* → a test that drives the workflow to the outreach step without an approval event and asserts the outreach tool was never invoked.
- *"The agent must never invent suppliers outside the catalog"* → an eval scenario that asks for a supplier the catalog doesn't have, and asserts the response either says "no match" or names only catalog entries.

Guardrail tests are non-negotiable; reviewers should reject any PR that loosens or removes one without a written justification.

## 3. Commit Conventions

We use **Conventional Commits**. Format:

```
<type>(<scope>): <subject>

<body — optional, explains *why*, not *what*>
```

Types:
- `feat` — new behavior visible to a user or another module
- `fix` — bug fix
- `test` — tests only (no production code change)
- `chore` — tooling, deps, infra, build
- `docs` — docs only
- `refactor` — internal restructure, no behavior delta
- `perf` — performance change
- `style` — formatting only

Scope is the affected area: an agent name, a module, a layer. Optional but recommended.

Subject:
- Imperative mood ("add", not "added" or "adds")
- Lowercase, no trailing period
- ≤ 72 chars

Body:
- Explain *why*, not *what*. The diff shows what.
- Reference the source-of-truth doc section if applicable: "implements `docs/agentic.md` §6.4".
- Reference the issue or RFC if applicable.

Good examples:
```
feat(supplier-scoring): weight reliability above price for balanced goal

The scoring formula in spec.md §8.5 now treats reliability as primary
when optimization_goal=balanced. Price is the tiebreaker.

test(credit-policy): cover utilization-at-limit edge case

fix(intake-agent): preserve answered fields when re-asking missing ones
```

Bad examples:
```
update code            # what code? why?
fix bug                # which bug?
WIP                    # don't ship WIP commits to main
asdf                   # please no
```

## 4. PR Checklist

Copy this into the PR description and tick boxes before requesting review (or merging your own PR):

```
- [ ] All tests pass: `uv run pytest`
- [ ] Lint clean: `uv run ruff check .`
- [ ] Types clean: `uv run mypy .`
- [ ] New behavior has tests at the appropriate layer (unit / integration / graph / eval)
- [ ] Touched guardrails (approval gate, supplier catalog boundary, credit policy) have updated/added tests
- [ ] No secrets in diff (no `sk-...`, no real API keys, no passwords)
- [ ] Branch is rebased on latest `main`
- [ ] PR title uses Conventional Commits format
- [ ] Linked to source-of-truth doc section if implementing a spec'd feature
```

## 5. Pre-commit and CI

Local hooks are configured with pre-commit:

```bash
make setup
# or, if dependencies are already installed:
make install-hooks
```

Hook behavior:
- **pre-commit:** repo-wide `ruff check --fix`, `ruff format`, strict `mypy`, and full `pytest`
- **commit-msg:** validates Conventional Commit subjects, e.g. `feat(api): add health check`

The commit must not be created if any lint, type, or test step fails.

Run hooks manually with:

```bash
uv run pre-commit run --all-files
```

GitHub Actions CI runs on pushes to `main` and pull requests. It installs with `uv sync --all-packages --locked`, then runs Ruff format check, Ruff lint, mypy, and fast pytest. Add a separate service-backed integration job once `tests/integration/` has real tests.

## 6. Anti-patterns to avoid

- **"I'll add tests later"** — you won't, and the tests you do add will be shaped to fit the code instead of the other way around.
- **Long-lived feature branches** — they accumulate merge conflicts and reviewer fatigue. Split into smaller deliveries.
- **Skipping the PR for "trivial" changes** — there is no trivial change to `main`. The PR is the review checkpoint.
- **Mocking what you can run for real** — Postgres is one `docker compose up` away. Use it.
- **Asserting LLM output by string match** — switch to schema/structural assertions or move it to `tests/evals/`.
- **Committing directly to `main` "just this once"** — there is no "just this once". Branch.
