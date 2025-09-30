# Makefile for MSSE-Capstone-Project testing and development

.PHONY: help install install-dev test test-unit test-integration test-slow test-coverage clean lint format check

help:  ## Show this help message
	@echo 'Usage: make <target>'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \\033[36m%-20s\\033[0m %s\\n", $$1, $$2}'

install:  ## Install project dependencies
	uv sync --extra test

install-dev:  ## Install development dependencies
	uv sync --extra dev

test:  ## Run all tests
	uv run pytest tests/

test-unit:  ## Run unit tests only
	uv run pytest tests/ -m unit

test-integration:  ## Run integration tests only
	uv run pytest tests/ -m integration

test-mcp:  ## Run MCP-specific tests only
	uv run pytest tests/ -m mcp

test-slow:  ## Run slow tests only
	uv run pytest tests/ -m slow

test-coverage:  ## Run tests with coverage report
	uv run pytest tests/ --cov=msse_capstone --cov-report=term-missing --cov-report=html:htmlcov

test-coverage-fail:  ## Run tests with coverage and fail if below threshold
	uv run pytest tests/ --cov=msse_capstone --cov-report=term-missing --cov-fail-under=80

clean:  ## Clean up test artifacts and cache
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint:  ## Run linting with flake8
	uv run flake8 msse_capstone/ tests/

format:  ## Format code with black and isort
	uv run black msse_capstone/ tests/
	uv run isort msse_capstone/ tests/

check:  ## Run all checks (lint, format check, tests)
	uv run black --check msse_capstone/ tests/
	uv run isort --check-only msse_capstone/ tests/
	uv run flake8 msse_capstone/ tests/
	uv run pytest tests/ --cov=msse_capstone --cov-fail-under=80

# Development workflow targets
dev-setup:  ## Set up development environment
	uv sync --extra dev
	@echo "Development environment ready!"

dev-test:  ## Quick development test run
	uv run pytest tests/ -x -v

dev-watch:  ## Run tests in watch mode (requires pytest-watch)
	uv run ptw tests/ -- --tb=short