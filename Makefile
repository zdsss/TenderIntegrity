.PHONY: run test lint install seed-whitelist

install:
	uv sync

run:
	uv run uvicorn src.api.main:app --reload --port 8000

test:
	uv run pytest tests/ -v

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

test-e2e:
	uv run pytest tests/e2e/ -v -s

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/

seed-whitelist:
	uv run python scripts/seed_whitelist.py

compare:
	uv run python scripts/run_comparison.py $(ARGS)
