.PHONY: install dev lint format type-check test clean all

# Install package
install:
	uv pip install -e .

# Install with dev dependencies
dev:
	uv sync --dev
	uv run pre-commit install

# Run all checks
all: format lint type-check test-all

# Format code
format:
	uv run ruff format .

# Lint and fix code
lint:
	uv run ruff check . --fix

# Lint without fixing (for CI)
lint-check:
	uv run ruff check .

# Type checking
type-check:
	uv run mypy src/

# Run tests (single Python version)
test:
	uv run pytest -v

# Run all tests (all Python versions + mypy + lint)
test-all: lint-check type-check
	uv run tox

# Run tests on specific Python version
test-py314:
	uv run tox -e py314

test-py313:
	uv run tox -e py313

test-py312:
	uv run tox -e py312

# Clean build artifacts
clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Pre-commit hooks
pre-commit:
	uv run pre-commit run --all-files
