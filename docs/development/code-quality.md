# Code Quality

## Linting with Ruff

[Ruff](https://github.com/astral-sh/ruff) is a fast Python linter written in Rust.

```bash
# Check for linting issues
make lint

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Format code
make format
```

## Type Checking with MyPy

```bash
# Run type checking
make type-check

# Run type checking with specific configuration
uv run mypy src/repoman/
```

## Configuration Files

- **`config/ruff.toml`**: Ruff linting and formatting configuration
- **`config/mypy.ini`**: MyPy type checking configuration
- **`pyproject.toml`**: Project metadata and tool configurations
