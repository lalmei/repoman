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
   uv run repoman --help
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
Generated with `make docs-trees` from `eza --tree`.

<!-- TREE_START:repoman -->

```
repoman
├── ' .github'
│   ├── ISSUE_TEMPLATE
│   │   ├── 1-bug.md
│   │   ├── 2-feature.md
│   │   ├── 3-docs.md
│   │   ├── 4-change.md
│   │   └── config.yml
│   └── workflows
│       ├── ci.yml
│       └── release.yml
├── AI_POLICY.md
├── config
│   ├── coverage.ini
│   ├── cursor
│   │   ├── hooks.json
│   │   └── rules
│   │       └── checks.md
│   ├── mkdocs.yml
│   ├── mypy.ini
│   ├── pytest.ini
│   └── ruff.toml
├── CONTRIBUTING.md
├── coverage.xml
├── docs
│   ├── cli.md
│   ├── concepts
│   │   ├── copier-and-answers.md
│   │   ├── generated-project.md
│   │   └── overview.md
│   ├── css
│   │   ├── material.css
│   │   └── mkdocstrings.css
│   ├── development
│   │   ├── additional-resources.md
│   │   ├── ci.md
│   │   ├── code-quality.md
│   │   ├── configuration.md
│   │   ├── contributing.md
│   │   ├── debugging.md
│   │   ├── documentation.md
│   │   ├── instantiated-template-coverage-plan.md
│   │   ├── package-management.md
│   │   ├── performance-tips.md
│   │   ├── README.md
│   │   ├── testing-best-practices.md
│   │   ├── testing-fixtures.md
│   │   ├── testing-troubleshooting.md
│   │   ├── testing.md
│   │   └── tools.md
│   ├── getting-started
│   │   ├── installation.md
│   │   └── quickstart.md
│   ├── guides
│   │   ├── adding-a-cli-command.md
│   │   ├── configuration.md
│   │   ├── creating-a-project.md
│   │   └── updating-a-project.md
│   ├── index.md
│   ├── js
│   │   └── feedback.js
│   ├── make-commands.md
│   ├── reference
│   │   └── troubleshooting.md
│   ├── roadmap.md
│   ├── template-prompts.md
│   ├── template-structure.md
│   └── template.md
├── Makefile
├── pyproject.toml
├── README.md
├── scripts
│   ├── gen_credits.py
│   ├── gen_ref_nav.py
│   ├── gen_tree_docs.py
│   └── update_instantiated_template_coverage.py
├── src
│   └── repoman
│       ├── __init__.py
│       ├── __main__.py
│       ├── _version.py
│       ├── cli
│       │   ├── __init__.py
│       │   ├── commands
│       │   ├── main_cli.py
│       │   ├── messages
│       │   └── register_commands.py
│       ├── config.py
│       ├── copier.yml
│       ├── extensions.py
│       ├── extentions
│       │   ├── command_template
│       │   └── routers_template
│       ├── main_template
│       │   ├── AI_POLICY.md.jinja
│       │   ├── CHANGELOG.md.jinja
│       │   ├── CODE_OF_CONDUCT.md.jinja
│       │   ├── config
│       │   ├── CONTRIBUTING.md.jinja
│       │   ├── docs
│       │   ├── LICENSE.jinja
│       │   ├── make_cmds
│       │   ├── Makefile.jinja
│       │   ├── pyproject.toml.jinja
│       │   ├── README.md.jinja
│       │   ├── scripts
│       │   ├── src
│       │   ├── tests
│       │   ├── "{% if ci == 'azure' %}.azuredevops{% endif %}"
│       │   ├── "{% if ci == 'github' %}.github{% endif %}"
│       │   ├── "{% if ci == 'gitlab' %}.gitlab{% endif %}"
│       │   ├── '{% if python_notebooks %}notebooks{% endif %}'
│       │   └── {{_copier_conf.answers_file}}.jinja
│       └── utils
│           ├── __init__.py
│           ├── logging.py
│           └── theme
├── tests
│   ├── __init__.py
│   ├── ci_runner.py
│   ├── conftest.py
│   ├── fixtures
│   │   └── default_copier_answers.yml
│   ├── template_testing.py
│   ├── test_cli
│   │   ├── __init__.py
│   │   ├── test_cli.py
│   │   ├── test_command_registration.py
│   │   ├── test_create.py
│   │   ├── test_generator.py
│   │   └── test_update.py
│   ├── test_input
│   │   ├── __init__.py
│   │   └── test_extensions.py
│   ├── test_template
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_ci.py
│   ├── test_utils
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_ci_runner.py
│   │   ├── test_logging.py
│   │   ├── test_template_testing.py
│   │   └── test_theme.py
│   └── test_version.py
└── uv.lock
```

<!-- TREE_END -->

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
