.PHONY: dev dev-frontend dev-backend build test lint format typecheck clean db-migrate db-upgrade docker-up docker-down setup

# ─── Development ──────────────────────────────────────────────
dev:
	bun run dev

dev-frontend:
	bun run --filter frontend dev

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ─── Build ────────────────────────────────────────────────────
build:
	bun run build

# ─── Testing ──────────────────────────────────────────────────
test:
	cd backend && pytest

test-frontend:
	bun run --filter frontend test

test-e2e:
	bun run --filter frontend test:e2e

# ─── Linting & Formatting ─────────────────────────────────────
lint:
	bun run lint
	cd backend && ruff check .

lint-fix:
	bun run lint -- --fix
	cd backend && ruff check . --fix

format:
	bun run format
	cd backend && ruff format .

format-check:
	bun run format -- --check
	cd backend && ruff format --check .

# ─── Type Checking ────────────────────────────────────────────
typecheck:
	bun run --filter frontend typecheck

# ─── Database ─────────────────────────────────────────────────
db-migrate:
	cd backend && alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

# ─── Docker ───────────────────────────────────────────────────
docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-build:
	docker compose build

# ─── Setup ────────────────────────────────────────────────────
setup:
	bun install
	cd backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
	pre-commit install

# ─── Clean ────────────────────────────────────────────────────
clean:
	bun install --force
	cd frontend && rm -rf .next
	cd backend && rm -rf __pycache__ .ruff_cache
