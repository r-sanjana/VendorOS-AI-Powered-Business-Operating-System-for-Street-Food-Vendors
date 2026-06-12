# VendorOS Backend – Developer Makefile
# Usage: make <target>

.PHONY: help install dev test lint format migrate upgrade downgrade docker-up docker-down clean

PYTHON  := python3
PIP     := pip
UVICORN := uvicorn
APP     := app.main:app

# ── Help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "VendorOS Backend – Available Commands"
	@echo "======================================"
	@echo "  make install       Install all Python dependencies"
	@echo "  make dev           Start development server with hot-reload"
	@echo "  make test          Run the full test suite"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run ruff linter"
	@echo "  make format        Format code with black + ruff"
	@echo "  make migrate msg=  Create a new Alembic migration"
	@echo "  make upgrade       Apply all pending migrations"
	@echo "  make downgrade     Roll back the last migration"
	@echo "  make docker-up     Start all Docker services"
	@echo "  make docker-down   Stop all Docker services"
	@echo "  make clean         Remove caches and .pyc files"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────────
install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# ── Development server ────────────────────────────────────────────────────────
dev:
	$(UVICORN) $(APP) \
		--host 0.0.0.0 \
		--port 8000 \
		--reload \
		--log-level debug

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	pytest

test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html
	@echo "HTML coverage report: htmlcov/index.html"

# ── Code quality ──────────────────────────────────────────────────────────────
lint:
	ruff check app tests

format:
	black app tests
	ruff check --fix app tests

# ── Alembic migrations ────────────────────────────────────────────────────────
migrate:
	@if [ -z "$(msg)" ]; then echo "Usage: make migrate msg='your message'"; exit 1; fi
	alembic revision --autogenerate -m "$(msg)"

upgrade:
	alembic upgrade head

downgrade:
	alembic downgrade -1

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up -d --build
	@echo "Services running:"
	@echo "  API:     http://localhost:8000"
	@echo "  Docs:    http://localhost:8000/api/docs"
	@echo "  Health:  http://localhost:8000/health"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f backend

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov .ruff_cache .mypy_cache
	@echo "Clean complete."