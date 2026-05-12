.DEFAULT_GOAL := help

.PHONY: help sync setup install-hooks run dev smoke-api infra-up infra-down infra-reset lint lint-fix format format-check typecheck test test-unit test-integration test-eval coverage check ci clean

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Install all workspace packages and dev dependencies.
	uv sync --all-packages

setup: sync install-hooks ## Install dependencies, hooks, and create .env if missing.
	@test -f .env || cp .env.example .env
	@echo "Setup complete. Fill .env with provider keys before running LLM-backed flows."

install-hooks: ## Install pre-commit and commit-msg hooks.
	uv run pre-commit install --hook-type pre-commit --hook-type commit-msg

run: ## Run the backend console-script entrypoint.
	uv run watad

dev: ## Run the future FastAPI app with reload once watad.api exists.
	uv run uvicorn watad.api:app --reload

smoke-api: ## Smoke test a running API at WATAD_API_BASE_URL or localhost:8000.
	uv run python scripts/smoke_api.py

infra-up: ## Start local Postgres+pgvector and Redis.
	docker compose -f infra/docker-compose.yml up -d

infra-down: ## Stop local infrastructure.
	docker compose -f infra/docker-compose.yml down

infra-reset: ## Stop local infrastructure and remove volumes.
	docker compose -f infra/docker-compose.yml down -v

lint: ## Run Ruff lint checks.
	uv run ruff check .

lint-fix: ## Run Ruff lint checks and apply safe fixes.
	uv run ruff check --fix .

format: ## Format Python files with Ruff.
	uv run ruff format .

format-check: ## Check Python formatting without writing changes.
	uv run ruff format --check .

typecheck: ## Run strict mypy checks.
	uv run mypy .

test: ## Run the full pytest suite.
	uv run pytest

test-unit: ## Run fast tests only.
	uv run pytest -m "not integration and not eval"

test-integration: ## Run container-backed integration tests.
	uv run pytest -m integration

test-eval: ## Run LLM-backed eval tests.
	uv run pytest -m eval

coverage: ## Run tests with coverage.
	uv run pytest --cov=watad

check: lint typecheck test ## Run local commit gates.

ci: format-check lint typecheck test ## Run CI-equivalent checks.

clean: ## Remove local tool caches.
	rm -rf .coverage .mypy_cache .pytest_cache .ruff_cache htmlcov
