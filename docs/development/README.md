# Development Guide

Welcome to the repoman development environment! This guide will help you set up your development environment and understand the tools and workflows used in this project.

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**: The project requires Python 3.12 or higher
- **uv**: Modern Python package manager and project management tool
- **Git**: Version control system

### Initial Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd repoman
   ```

2. **Install uv** (if not already installed):

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

3. **Set up the development environment**:

   ```bash
   # Install dependencies and create virtual environment
   uv sync

   # Activate the virtual environment
   source .venv/bin/activate  # macOS/Linux
   # or
   .venv\Scripts\activate     # Windows
   ```

4. **Verify the setup**:

   ```bash
   # Run tests to ensure everything is working
   make test

   # Check that repoman is available
   uv run python -m repoman --help
   ```

## Development topics

- **[Tools](tools.md)** — uv, Makefile, and development automation
- **[Code Quality](code-quality.md)** — Linting (Ruff), type checking (MyPy)
- **[Documentation](documentation.md)** — MkDocs, Material theme, building docs
- **[CI](ci.md)** — Continuous integration and local simulation
- **[Debugging](debugging.md)** — Common issues and debug tools
- **[Performance Tips](performance-tips.md)** — Fast development workflow
- **[Package Management](package-management.md)** — Adding and managing dependencies
- **[Configuration](configuration.md)** — Environment variables, IDE setup

## 📁 Project Structure

File trees use Font Awesome icons for file types (see [The template](../template.md)).

:fontawesome-solid-folder: **repoman/**

- :fontawesome-solid-folder: **src/repoman/** — Source code
  - :fontawesome-brands-python: `__init__.py`
  - :fontawesome-solid-folder: **cli/** — Command-line interface
  - :fontawesome-solid-folder: **utils/** — Utility functions
  - :fontawesome-brands-python: `_version.py`
- :fontawesome-solid-folder: **tests/** — Test suite
  - :fontawesome-brands-python: `conftest.py` — Pytest configuration
  - :fontawesome-solid-folder: **test_cli/** — CLI tests
  - :fontawesome-solid-folder: **test_utils/** — Utility tests
  - :fontawesome-solid-folder: **test_input/** — Input processing tests
  - :fontawesome-solid-file-code: `test_version.py`
- :fontawesome-solid-folder: **docs/** — Documentation
  - :fontawesome-solid-folder: **development/** — Development documentation
- :fontawesome-solid-folder: **config/** — Configuration files
  - :fontawesome-solid-file-code: `pytest.ini`
  - :fontawesome-solid-file-code: `ruff.toml`
  - :fontawesome-solid-file-code: `mypy.ini`
- :fontawesome-solid-file-code: `pyproject.toml` — Project configuration
- :fontawesome-solid-file-code: `uv.lock` — Dependency lock file
- :fontawesome-solid-file-code: `Makefile` — Development automation
- :fontawesome-solid-file-lines: `README.md` — Project overview

## 🔧 Development Workflow

### 1. Setting Up a New Feature

```bash
# Create a new branch
git checkout -b feature/new-feature

# Ensure you're in the virtual environment
source .venv/bin/activate

# Install any new dependencies
uv add new-package-name
```

### 2. Development Cycle

```bash
# 1. Make your changes
# Edit files in src/repoman/

# 2. Run tests to ensure nothing is broken
make test

# 3. Run linting and formatting
make format
make lint

# 4. Run type checking
make type-check

# 5. Run all checks
make check
```

### 3. Testing Your Changes

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-cli
make test-utils

# Run tests with coverage
make test-coverage

# Run individual test files
uv run pytest tests/test_cli/test_create.py

# Run specific test methods
uv run pytest tests/test_cli/test_create.py::test_create_command_basic
```

### 4. Code Quality

```bash
# Format your code
make format

# Check for linting issues
make lint

# Run type checking
make type-check

# Run all quality checks
make check
```

## 🧪 Testing

See the [Testing Guide](testing.md) for comprehensive documentation on test categories, running tests, fixtures, troubleshooting, and best practices.

## 🤝 Contributing

See [Contributing](contributing.md) for setup, workflow, commit conventions, and where to get help. Before submitting:

1. Run all tests: `make test`
2. Check code quality: `make check`
3. Update documentation if needed

## 📖 Additional Resources

See [Additional Resources](additional-resources.md) for links to CLI reference, Make commands, testing guide, and external documentation.
