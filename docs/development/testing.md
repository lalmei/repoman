# Repoman Test Suite

This directory contains the comprehensive test suite for the repoman project, designed to ensure code quality and reliability.

## 🎉 Current Status (Updated: August 2024)

### Test Suite Health

- **✅ All Tests Passing**: 143/143 tests (100% success rate)
- **📊 Coverage**: 93.89% overall coverage (excellent improvement from 79.17%)
- **📊 Instantiated template coverage**: 92.72% (update with `make update-instantiated-template-coverage`) <!-- instantiated-template-coverage: 92.72% -->
- **⚡ Performance**: Full suite runs in ~1.30s
- **🔧 Test Isolation**: Perfect - no dependencies between tests
- **🚀 Parallel Execution**: Successfully tested with 8 workers

### Recent Achievements

- **Eliminated all interactive prompts** during test execution
- **Resolved resource warnings** and unclosed file handles
- **Implemented comprehensive security validation** with 18 attack vectors tested

- **Optimized test configuration** for better performance and reliability

### Module Coverage Status

- **`_version.py`**: 99% coverage (up from 67%)
- **`extensions.py`**: 100% coverage (newly added)
- **`logging.py`**: 96% coverage
- **`copier.py`**: 91% coverage
- **`theme.py`**: 100% coverage
- **`main_cli.py`**: 82% coverage

### Test Categories

- **Unit Tests**: 67 tests (utility functions, theme, logging)
- **CLI Tests**: 33 tests (command execution, argument parsing)
- **Extension Tests**: 43 tests (Jinja2 extensions, git integration)
- **Version Tests**: 24 tests (version management, debug info)

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── ci_runner.py             # CI command runner (run_make_command, CommandResult)
├── conftest.py              # Pytest configuration and fixtures
├── template_testing.py      # Template instantiation helpers (instantiate_template, cleanup_project_artifacts)
├── fixtures/                # Test fixtures (e.g. default_copier_answers.yml)
├── test_template/           # Template/CI integration tests
│   ├── __init__.py
│   ├── conftest.py
│   └── test_ci.py           # CI commands on instantiated template
├── test_utils/              # Utility function tests
│   ├── __init__.py
│   ├── conftest.py          # Test-specific configuration
│   ├── test_theme.py        # Theme utility tests
│   ├── test_logging.py      # Logging utility tests
│   ├── test_ci_runner.py    # Unit tests for ci_runner
│   └── test_template_testing.py  # Unit tests for template_testing
├── test_cli/                # CLI command tests
│   ├── __init__.py
│   ├── test_cli.py          # Main CLI tests
│   └── test_create.py       # Create command tests
├── test_input/              # Input processing tests
│   └── test_extensions.py   # Jinja2 extensions tests
└── test_version.py          # Version and debug utilities tests
```

See [Test Utilities Reference](#test-utilities-reference) for `ci_runner` and `template_testing`.

## Test Utilities Reference

The test suite uses two utility modules for template instantiation and CI command execution. These are part of the test infrastructure, not the repoman library.

### ci_runner.py

Runs make commands in instantiated template projects with output streaming and capture.

| Component                                                | Purpose                                                                                                                          |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `CommandResult`                                          | Dataclass with `returncode`, `stdout`, `stderr`, `command` for assertions                                                        |
| `run_make_command(project_dir, command, env?, timeout?)` | Executes `make <command>` in `project_dir`; checks for `uv` in PATH; streams output while capturing; optional timeout in seconds |

**Used by:** `conftest.py` (setup, format, fix), `test_template/test_ci.py` (format-check, lint, check-types, test), `test_utils/test_ci_runner.py` (unit tests).

### template_testing.py

Instantiates templates and cleans up artifacts for isolated, reproducible tests.

| Component                                                                                              | Purpose                                                                                                                     |
| ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `instantiate_template(output_dir, template_path?, project_name?, copier_data?, answers_file?, force?)` | Runs Copier to instantiate the template; returns path to project directory                                                  |
| `cleanup_project_artifacts(project_dir)`                                                               | Removes .venv, dist, build, site, egg-info, caches so tests don't leave artifacts                                           |
| `_slugify` (private)                                                                                   | Internal helper to compute package names for Copier data; mirrors `repoman.extensions.slugify` so tests stay self-contained |

**Used by:** `conftest.py` (fixtures `instantiated_template`, `setup_template`), `test_template/test_ci.py` (instantiation and cleanup tests).

## Instantiated template test coverage

Repoman runs tests on an **instantiated** copy of the main template to ensure the generated project’s CI (format-check, lint, check-types, test) works. We also run tests **with coverage** on that instantiated project so you can see and track how much of the generated code is covered.

- **What runs**: The test `test_instantiated_template_test_coverage` runs `make test-coverage-report` in the instantiated project. That runs pytest with coverage (term-missing and html reports). The template provides `test-coverage-report` (no fail-under) so the run always succeeds and we can read the coverage value.
- **Visibility**: The full coverage report (term-missing) is streamed in repoman’s pytest output when you run the template CI tests.
- **Programmatic value**: We parse the total line coverage % from the report and log it (e.g. “Instantiated template line coverage: 38.81%”). The same value is recorded in **Test Suite Health** above as “Instantiated template coverage”; update it by running `make update-instantiated-template-coverage` (see below).

## Quick Start

### 1. Run All Tests

```bash
# From the project root
make test

# Or directly with pytest
uv run pytest -c=config/pytest.ini tests/
```

### 2. Run Specific Test Categories

```bash
# Unit tests only
make test-unit

# Utility tests only
make test-utils

# CLI tests only
make test-cli

# Isolated tests only
make test-isolated

# Fast tests (skip slow ones)
make test-fast
```

### 3. Run Individual Test Files

```bash
# Run a specific test file
make test-single FILE=tests/test_utils/test_theme.py

# Or directly with pytest
uv run pytest -c=config/pytest.ini tests/test_utils/test_theme.py
```

### 4. Run Tests with Coverage

```bash
# Generate coverage report (writes HTML to docs/htmlcov)
make test-coverage

# View HTML coverage report locally, or build docs and open Development → Coverage report
open docs/htmlcov/index.html
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- **Purpose**: Test individual components in isolation
- **Execution**: Fast, no external dependencies
- **Examples**: Utility functions, theme creation, logging setup

### Integration Tests (`@pytest.mark.integration`)

- **Purpose**: Test component interactions and CLI commands
- **Execution**: May require file system operations
- **Examples**: CLI command execution, template processing

### Utility Tests (`@pytest.mark.utils`)

- **Purpose**: Test utility functions and helpers
- **Execution**: Fast, isolated
- **Examples**: Theme utilities, logging configuration

### CLI Tests (`@pytest.mark.cli`)

- **Purpose**: Test command-line interface functionality
- **Execution**: May require file system operations
- **Examples**: Create command, argument parsing

### Isolated Tests (`@pytest.mark.isolated`)

- **Purpose**: Tests that must run in complete isolation
- **Execution**: Each test runs in its own temporary directory
- **Examples**: File operations, logging with files

## Test Isolation Features

### Automatic Test Isolation

The test suite includes several isolation mechanisms:

1. **Working Directory Isolation**: Each test runs in a unique temporary directory
2. **Logger State Cleanup**: Logger state is restored between tests
3. **Environment Variable Management**: Test-specific environment variables are isolated
4. **File System Cleanup**: Temporary files and directories are automatically cleaned up

### Fixtures

Key fixtures available to all tests:

- `tmp_path`: Pytest's built-in temporary directory fixture
- `cli_runner`: Typer CLI runner for testing commands
- `cli_app`: The main CLI application instance
- `test_workspace`: Isolated workspace for file operations
- `mock_template_structure`: Mock template for testing

For fixture optimization and scope management, see [Testing Fixtures](testing-fixtures.md).

## Running Tests in Different Environments

### Development Environment

```bash
# Quick test run during development
make test-fast

# Run specific test category
make test-utils

# Run with verbose output
uv run pytest -c=config/pytest.ini -vvv tests/
```

### Continuous Integration

```bash
# Run all tests with coverage
make test-coverage

# Run tests in parallel (if pytest-xdist is available)
uv run pytest -c=config/pytest.ini -n auto tests/
```

### Debug Mode

```bash
# Run tests with maximum verbosity
uv run pytest -c=config/pytest.ini -vvv --tb=long tests/

# Run specific test with debug output
uv run pytest -c=config/pytest.ini -vvv --tb=long tests/test_utils/test_logging.py::test_set_up_logger_basic
```

For troubleshooting common issues, see [Testing Troubleshooting](testing-troubleshooting.md).

For best practices, coverage requirements, and contributing guidelines, see [Testing Best Practices](testing-best-practices.md).

## See also

- [Testing Fixtures](testing-fixtures.md)
- [Testing Troubleshooting](testing-troubleshooting.md)
- [Testing Best Practices](testing-best-practices.md)
