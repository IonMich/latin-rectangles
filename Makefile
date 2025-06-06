.PHONY: help install test lint format check clean
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the project in development mode
	uv sync --dev

test: ## Run tests
	uv run pytest --no-cov

test-cov: ## Run tests with coverage report
	uv run pytest --cov-report=html --cov-report=term

lint: ## Run linting
	uv run ruff check

lint-fix: ## Run linting with auto-fix
	uv run ruff check --fix

format: ## Format code
	uv run ruff format

format-check: ## Check formatting without making changes
	uv run ruff format --check

type-check: ## Run type checking
	uv run mypy src/

check: ## Run all checks (linting, formatting, type checking, tests)
	@echo "Running all checks..."
	uv run ruff check
	uv run ruff format --check
	uv run mypy src/
	uv run pytest

clean: ## Clean up build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the main application
	uv run latin-rectangles

build: ## Build the package
	uv build

publish-test: ## Publish to test PyPI
	uv publish --repository testpypi

publish: ## Publish to PyPI
	uv publish
