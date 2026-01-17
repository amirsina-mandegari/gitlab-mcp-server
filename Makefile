.PHONY: help install dev build test lint format check clean

help:
	@echo "Commands:"
	@echo "  make install   Install in editable mode with dev deps"
	@echo "  make dev       Build and install wheel locally"
	@echo "  make build     Build wheel"
	@echo "  make test      Run tests"
	@echo "  make lint      Run linters"
	@echo "  make format    Format code"
	@echo "  make check     Lint + test"
	@echo "  make clean     Remove build artifacts"

install:
	uv pip install -e ".[dev]"

dev:
	uv build
	uv pip install dist/*.whl --force-reinstall

build:
	uv build

test:
	uv run pytest tests/ -v

lint:
	uv run flake8 gitlab_mr_mcp/ tests/
	uv run bandit -r gitlab_mr_mcp/ -c bandit.yaml

format:
	uv run black gitlab_mr_mcp/ tests/
	uv run isort gitlab_mr_mcp/ tests/

check: lint test

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
