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

## 🛠️ Development Tools

### uv - Python Package Manager

[uv](https://github.com/astral-sh/uv) is a fast Python package manager and installer, written in Rust. It's used for dependency management, virtual environment creation, and running Python commands.

#### Key uv Commands

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

#### Why uv?

- **Speed**: Much faster than pip and poetry
- **Reliability**: Deterministic dependency resolution
- **Compatibility**: Works with existing Python tooling
- **Modern**: Built for modern Python development workflows

### Makefile - Development Automation

The project includes a comprehensive Makefile that automates common development tasks.

#### Available Make Commands

Run `make help` for the authoritative list. Summary:

```bash
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
make check                   # Run all quality checks (format-check, lint, check-types)

# Documentation
make docs                    # Build documentation
make docs-serve              # Serve documentation locally (e.g. http://localhost:8000)
make docs-check              # Check documentation for issues (strict build)

# Other
make clean                   # Clean cache and build files
make help                    # Print all targets
make update-instantiated-template-coverage  # Update coverage % in docs/development/testing.md
make setup-cursor            # Copy cursor config from config/cursor to .cursor
```

See [Make commands](../make-commands.md) for the full reference.

#### Makefile Structure

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

#### Adding Documentation Commands to Makefile

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
  - :fontawesome-brands-python: `test_version.py`
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

### Test Categories

- **Unit Tests**: Fast, isolated tests for individual functions
- **CLI Tests**: Tests for command-line interface functionality
- **Integration Tests**: Tests for component interactions
- **Security Tests**: Tests for input validation and security vulnerabilities

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run specific test file
uv run pytest tests/test_version.py

# Run tests in parallel
uv run pytest -n auto tests/

# Run tests with verbose output
uv run pytest -vvv tests/

# Run tests and stop on first failure
uv run pytest -x tests/
```

### Test Configuration

Tests are configured in `config/pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    cli: CLI tests
    utils: Utility tests
    slow: Slow tests
```

## 📝 Code Quality

### Linting with Ruff

[Ruff](https://github.com/astral-sh/ruff) is a fast Python linter written in Rust.

```bash
# Check for linting issues
make lint

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Format code
make format
```

### Type Checking with MyPy

```bash
# Run type checking
make type-check

# Run type checking with specific configuration
uv run mypy src/repoman/
```

### Configuration Files

- **`config/ruff.toml`**: Ruff linting and formatting configuration
- **`config/mypy.ini`**: MyPy type checking configuration
- **`pyproject.toml`**: Project metadata and tool configurations

## 📚 Documentation

The project uses **MkDocs** with the **Material theme** for documentation. This provides a modern, responsive documentation site with excellent features like search, navigation, and code highlighting.

### Documentation Structure

:fontawesome-solid-folder: **docs/**

- :fontawesome-solid-file-lines: `index.md` — Homepage
- :fontawesome-solid-file-lines: `cli.md` — CLI reference (subcommands and options)
- :fontawesome-solid-file-lines: `make-commands.md` — Make targets reference
- :fontawesome-solid-file-lines: `template.md` — The template (instantiated layout)
- :fontawesome-solid-file-lines: `roadmap.md` — Potential roadmap
- :fontawesome-solid-folder: **development/** — Development documentation
  - :fontawesome-solid-file-lines: `README.md` — This development guide
  - :fontawesome-solid-file-lines: `testing.md` — Comprehensive testing guide
  - :fontawesome-solid-file-lines: `instantiated-template-coverage-plan.md`
- :fontawesome-brands-css3-alt: **css/** — Custom CSS (material.css, mkdocstrings.css)
- :fontawesome-brands-js: **js/** — Custom JavaScript (e.g. feedback.js)
- :fontawesome-solid-folder: **.overrides/** — Material theme overrides (partials, etc.)

MkDocs is configured in `config/mkdocs.yml` (in the repo root). The `docs_dir` points to this `docs/` folder.

### MkDocs Configuration

The documentation is configured in `config/mkdocs.yml` with the following features:

- **Material theme** with dark/light mode support
- **Search functionality** with highlighting
- **Navigation tabs** and sections
- **Code annotation** and copying
- **Admonitions** and callouts
- **Emoji support** with Twemoji
- **Task lists** with custom checkboxes
- **API documentation** with mkdocstrings
- **Coverage reports** integration
- **Git revision dates** (when deployed)

### Building Documentation

```bash
# Install documentation dependencies
uv sync --group docs

# Build documentation
make docs

# Serve documentation locally (with live reload)
make docs-serve

# Check documentation for issues
make docs-check
```

### Documentation Features

#### Material Theme Features

- **Dark/Light Mode**: Automatic theme switching based on system preference
- **Search**: Full-text search with highlighting and suggestions
- **Navigation**: Sticky navigation with tabs and sections
- **Code Blocks**: Syntax highlighting with copy functionality
- **Admonitions**: Beautiful callout boxes for notes, warnings, etc.

#### Writing Documentation

Use Material theme features in your markdown:

````markdown
# Admonitions

!!! note "Note"
This is a note with a title.

!!! warning "Warning"
This is a warning.

!!! tip "Tip"
This is a tip.

# Code blocks with annotations

```python
def hello_world():
    print("Hello, World!")  # (1)
```
````

1. This is an annotation

# Task lists

- [x] Completed task
- [ ] Pending task

# Emoji support

:smile: :rocket: :warning:

# Tabs

=== "Tab 1"
Content for tab 1

=== "Tab 2"
Content for tab 2

````

#### API Documentation

The project uses `mkdocstrings` for automatic API documentation:

- **Python API**: Automatically generated from docstrings
- **Cross-references**: Links between documentation sections
- **Type annotations**: Displayed in function signatures
- **Source code**: Links to GitHub repository

### Documentation Workflow

1. **Write documentation** in markdown files
2. **Add docstrings** to Python code for API docs
3. **Test locally**: `make docs-serve`
4. **Build for deployment**: `make docs`
5. **Check for issues**: `make docs-check`

### Documentation Best Practices

#### Writing Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep documentation up to date with code changes

#### Structure

- Organize content logically
- Use consistent headings
- Include table of contents for long pages
- Cross-reference related sections

#### Code Examples

- Use syntax highlighting
- Include complete, runnable examples
- Add annotations for complex code
- Test all code examples

### Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment process:

1. Builds the documentation site
2. Minifies HTML for production
3. Deploys to `https://lalmei.github.io/repoman`

### Customization

#### CSS Customization

Add custom styles in `docs/css/material.css`:

```css
/* Custom styles for the documentation */
.custom-class {
    color: var(--md-primary-fg-color);
}
````

#### JavaScript Customization

Add custom functionality in `docs/js/feedback.js`:

```javascript
// Custom JavaScript for the documentation
document.addEventListener("DOMContentLoaded", function () {
  // Your custom code here
});
```

#### Theme Overrides

Customize the Material theme in `docs/.overrides/`:

- Override template files
- Add custom components
- Modify theme behavior

## 🔄 Continuous Integration

The project uses GitHub Actions for continuous integration. The CI pipeline:

1. **Runs tests** on multiple Python versions
2. **Checks code quality** (linting, type checking)
3. **Generates coverage reports**
4. **Builds documentation**

### Local CI Simulation

```bash
# Run the equivalent of CI locally
make check
make test-coverage
make build
```

## 🐛 Debugging

### Common Issues

1. **Import Errors**:

   ```bash
   # Ensure you're in the project root
   cd /path/to/repoman

   # Activate virtual environment
   source .venv/bin/activate

   # Use uv run for Python commands
   uv run python -c "import repoman"
   ```

2. **Test Failures**:

   ```bash
   # Run specific failing test with verbose output
   uv run pytest tests/test_cli/test_create.py::test_create_command_basic -vvv

   # Run with full traceback
   uv run pytest tests/test_cli/test_create.py::test_create_command_basic --tb=long
   ```

3. **Dependency Issues**:

   ```bash
   # Reinstall dependencies
   uv sync --reinstall

   # Update lock file
   uv lock --upgrade
   ```

### Debug Tools

```bash
# Run with debug output
uv run pytest -vvv --tb=long tests/

# Run specific test with debugger
uv run python -m pdb -m pytest tests/test_cli/test_create.py::test_create_command_basic

# Check environment
uv run python -c "import sys; print(sys.path)"
```

## 🚀 Performance Tips

### Fast Development Workflow

```bash
# Run only fast tests during development
make test-fast

# Run specific test categories
make test-unit

# Use parallel test execution
uv run pytest -n auto tests/
```

### Efficient Testing

- Use appropriate fixture scopes (module/session for expensive setup)
- Mock external dependencies
- Keep unit tests fast (under 1 second each)
- Use `tmp_path` fixture for file operations

## 📦 Package Management

### Adding Dependencies

```bash
# Add runtime dependency
uv add requests

# Add development dependency
uv add --dev pytest-cov

# Add dependency with specific version
uv add "requests>=2.25.0"

# Add dependency with extras
uv add "requests[security]"
```

### Managing Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific dependency
uv add --upgrade requests

# Remove dependency
uv remove requests

# Show dependency tree
uv tree
```

## 🔧 Configuration

### Environment Variables

```bash
# Set log level for development
export REPOMAN_LOG_LEVEL=DEBUG

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff"
}
```

## 🤝 Contributing

### Before Submitting

1. **Run all tests**: `make test`
2. **Check code quality**: `make check`
3. **Update documentation** if needed
4. **Add tests** for new functionality
5. **Follow the coding standards** outlined in this guide

### Pull Request Checklist

- [ ] All tests pass
- [ ] Code is formatted and linted
- [ ] Type checking passes
- [ ] Documentation is updated
- [ ] New tests are added for new functionality
- [ ] Security considerations are addressed

## 📖 Additional Resources

- **[CLI Reference](../cli.md)**: Subcommands and options for `repoman`
- **[Make commands](../make-commands.md)**: Full list of make targets
- **[Testing Guide](testing.md)**: Comprehensive testing documentation
- **Project README** (repo root): Project overview and usage
- **[uv Documentation](https://docs.astral.sh/uv/)**: uv package manager guide
- **[Pytest Documentation](https://docs.pytest.org/)**: Testing framework guide
- **[Ruff Documentation](https://docs.astral.sh/ruff/)**: Linting and formatting guide
- **[MkDocs Documentation](https://www.mkdocs.org/)**: Static site generator guide
- **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)**: Theme documentation
- **[mkdocstrings Documentation](https://mkdocstrings.github.io/)**: API documentation generator

## 🆘 Getting Help

If you encounter issues:

1. **Check the troubleshooting section** in the testing guide
2. **Search existing issues** in the project repository
3. **Create a new issue** with detailed information about the problem
4. **Ask in the project discussions** or community channels

---

Happy coding! 🎉
