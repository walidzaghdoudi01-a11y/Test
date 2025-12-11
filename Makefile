.PHONY: help install setup-db migrate start test clean lint format

help:
	@echo "Audit Logging System - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make setup-db     - Start PostgreSQL with Docker"
	@echo "  make migrate      - Run database migrations"
	@echo "  make start        - Start the audit service"
	@echo "  make test         - Run tests"
	@echo "  make test-cov     - Run tests with coverage"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean up generated files"
	@echo "  make docker-up    - Start all services with Docker Compose"
	@echo "  make docker-down  - Stop all services"
	@echo ""

install:
	pip install -r requirements.txt
	pip install -e audit-client/

setup-db:
	docker-compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 5

migrate:
	cd database && alembic upgrade head

start:
	cd audit-service && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=audit_service --cov=audit_client --cov-report=html --cov-report=term

lint:
	flake8 audit-service/ audit-client/ tests/ --max-line-length=100 --ignore=E501,W503
	mypy audit-service/ audit-client/ --ignore-missing-imports

format:
	black audit-service/ audit-client/ tests/ --line-length=100
	isort audit-service/ audit-client/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f audit-service
