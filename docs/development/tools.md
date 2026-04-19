# Development Tools

## uv - Python Package Manager

[uv](https://github.com/astral-sh/uv) is a fast Python package manager and installer, written in Rust. It's used for dependency management, virtual environment creation, and running Python commands.

### Key uv Commands

```bash
# Install dependencies from pyproject.toml
uv sync

# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Run Python commands in the project environment
uv run python script.py
uv run pytest tests/
uv run repoman --help

# Update dependencies
uv lock --upgrade

# Show dependency tree
uv tree
```

### Why uv?

- **Speed**: Much faster than pip and poetry
- **Reliability**: Deterministic dependency resolution
- **Compatibility**: Works with existing Python tooling
- **Modern**: Built for modern Python development workflows

## Makefile - Development Automation

The project includes a comprehensive Makefile that automates common development tasks.

### Available Make Commands

Run `make help` for the authoritative list. Summary:

```bash
# Setup
make setup                   # Install dependencies with uv
make install                 # Alias for setup
make sync                    # Sync dependencies with uv

# Testing
make test                    # Run all tests
make test-coverage           # Run tests with coverage report
make test-unit               # Run unit tests only
make test-utils              # Run utility tests only
make test-cli                # Run CLI tests only
make test-isolated           # Run isolated tests only
make test-fast               # Run fast tests (skip slow ones)
make test-single FILE=path  # Run a single test file (e.g. FILE=tests/test_utils/test_theme.py)
make test-function TEST=path # Run a specific test (e.g. TEST=tests/test_cli/test_cli.py::test_version)

# Code Quality
make format                  # Format code (ruff)
make lint                    # Lint code (ruff)
make format-check            # Check if code is formatted correctly
make fix                     # Auto-fix linting issues
make check-types             # Type check (mypy)
make type-check              # Alias for check-types
make check-quality           # Run formatting and linting checks
make check                   # Run all quality checks (format-check, lint, check-types)

# Compliance
make compliance-check        # Run repoman against this repository's own compliance baseline

# Documentation
make docs                    # Build documentation
make docs-serve              # Serve documentation locally (e.g. http://localhost:8000)
make docs-check              # Check documentation for issues (strict build)
make check-docs              # Alias for docs-check

# Other
make clean                   # Clean cache and build files
make help                    # Print all targets
make update-instantiated-template-coverage  # Update coverage % in docs/development/testing.md
make setup-cursor            # Copy cursor config from config/cursor to .cursor
make setup-vscode            # Copy VS Code config from config/vscode to .vscode
make setup-ide               # Copy Cursor and VS Code config (setup-cursor + setup-vscode)
```

See [Make commands](../make-commands.md) for the full reference.

### Makefile Structure

```makefile
# Example of how the Makefile is organized
.PHONY: test test-coverage lint format clean docs docs-serve

test:
	uv run pytest -c=config/pytest.ini tests/

test-coverage:
	uv run pytest --cov=src/repoman --cov-report=html --cov-report=term-missing

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

docs:
	uv run mkdocs build --config-file=config/mkdocs.yml

docs-serve:
	uv run mkdocs serve --config-file=config/mkdocs.yml

clean:
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ htmlcov/ site/
```

### Adding Documentation Commands to Makefile

To add documentation commands to your Makefile, add these lines:

```makefile
#######################
#   Documentation     #
#######################
docs: ## Build documentation
	uv run mkdocs build --config-file=config/mkdocs.yml

docs-serve: ## Serve documentation locally
	uv run mkdocs serve --config-file=config/mkdocs.yml

docs-check: ## Check documentation for issues
	uv run mkdocs build --config-file=config/mkdocs.yml --strict
```
