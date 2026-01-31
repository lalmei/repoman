SHELL := bash

version := 0.0.1

src.python := $(shell find ./src -type f -name "*.py" || :)
test.python := $(shell find ./tests -type f -name "*.py" || :)
src.python.pyc := $(shell find ./src -type f -name "*.pyc")
cache.dir := $(shell find . -type d -name __pycache__)
checkpoint.dir := $(shell find . -type d -name .ipynb_checkpoints)
mypy.cache.dir := $(shell find . -type d -name ".mypy_cache")
pytest.cache.dir := $(shell find . -type d -name ".pytest_cache" )


# notebooks := $(shell find ./notebooks -type f -name "*.ipynb" || :)

deployments.dir := deployment
uv.project.enviroment := .venv
dist.dir := dist

build.wheel := $(dist.dir)/repoman-$(version).tar.gz

docker.image := repoman_base:$(version)
docker.image.deploy := repoman:$(version)



.PHONY: help
help: ## Print the help screen.
	@echo "$(subdirs)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":|:[[:space:]].*?##"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


#######################
#     Testing & QA      #
#######################
clean: ## Clean up cache and build files
	@echo "Cleaning up..."
	@rm -rf $(cache.dir) $(checkpoint.dir) $(mypy.cache.dir) $(pytest.cache.dir) $(dist.dir)

test: clean ## Run all tests
	uv run pytest -c=config/pytest.ini $(test.python)

test-unit: clean ## Run unit tests only
	uv run pytest -c=config/pytest.ini -m "unit" $(test.python)

test-utils: clean ## Run utility tests only
	uv run pytest -c=config/pytest.ini -m "utils" $(test.python)

test-cli: clean ## Run CLI tests only
	uv run pytest -c=config/pytest.ini -m "cli" $(test.python)

test-isolated: clean ## Run isolated tests only
	uv run pytest -c=config/pytest.ini -m "isolated" $(test.python)

test-fast: clean ## Run fast tests (skip slow ones)
	uv run pytest -c=config/pytest.ini -m "not slow" $(test.python)

test-single: clean ## Run a single test file (usage: make test-single FILE=tests/test_utils/test_theme.py)
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-single FILE=tests/test_utils/test_theme.py"; \
		exit 1; \
	fi
	uv run pytest -c=config/pytest.ini $(FILE)

test-function: clean ## Run a specific test function (usage: make test-function TEST=tests/test_cli/test_cli.py::test_version)
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-function TEST=tests/test_cli/test_cli.py::test_version"; \
		exit 1; \
	fi
	uv run pytest -c=config/pytest.ini $(TEST)

test-coverage: clean ## Run tests with coverage report
	uv run pytest -c=config/pytest.ini --cov=src/repoman --cov-report=term-missing --cov-report=html $(test.python)

#######################
#     Formatting      #
#######################
format: ## Format code using ruff
	uv run ruff format src/repoman tests/ --config=config/ruff.toml --exclude src/repoman/main_template

lint: ## Lint code using ruff
	uv run ruff check src/repoman tests/ --config=config/ruff.toml --exclude src/repoman/main_template

format-check: ## Check if code is formatted correctly
	uv run ruff format --check src/repoman tests/ --config=config/ruff.toml --exclude src/repoman/main_template

fix: ## Auto-fix linting issues
	uv run ruff check --fix src/repoman tests/ --config=config/ruff.toml --exclude src/repoman/main_template

check-types: ## Type check code using mypy
	uv run mypy src/repoman/ --config-file=config/mypy.ini

type-check: check-types ## Alias for check-types

check: format-check lint check-types ## Run all quality checks (format-check, lint, check-types)

#######################
#   Documentation     #
#######################
docs: ## Build documentation
	uv run mkdocs build --config-file=config/mkdocs.yml

docs-serve: ## Serve documentation locally
	uv run mkdocs serve --config-file=config/mkdocs.yml

docs-serve-open: ## Serve documentation and open in default browser
	@(sleep 2 && uv run python -m webbrowser "http://127.0.0.1:8000") &
	uv run mkdocs serve --config-file=config/mkdocs.yml

docs-check: ## Check documentation for issues
	uv run mkdocs build --config-file=config/mkdocs.yml --strict

update-instantiated-template-coverage: ## Update instantiated template coverage %% in docs/development/testing.md
	uv run python scripts/update_instantiated_template_coverage.py

#######################
#      Setup          #
#######################
setup-cursor: ## Copy cursor configuration from config/cursor to .cursor
	@mkdir -p .cursor
	@cp -r config/cursor/* .cursor/
	@echo "Cursor configuration synced to .cursor/"
