# Make commands

Development tasks are driven by the **Makefile**. For an up-to-date list of targets and short descriptions, run:

```bash
make help
```

The following sections group targets by purpose.

## Testing

| Target | Description |
|--------|-------------|
| `make test` | Run all tests |
| `make test-unit` | Run unit tests only |
| `make test-utils` | Run utility tests only |
| `make test-cli` | Run CLI tests only |
| `make test-isolated` | Run isolated tests only |
| `make test-fast` | Run fast tests (skip slow ones) |
| `make test-single` | Run a single test file. Usage: `make test-single FILE=tests/path/to/test_file.py` |
| `make test-function` | Run a specific test function. Usage: `make test-function TEST=tests/test_cli/test_cli.py::test_version` |
| `make test-coverage` | Run tests with coverage report (term + HTML); HTML is written to `docs/htmlcov` and included in the built docs under **Development → Coverage report** |

## Code quality

| Target | Description |
|--------|-------------|
| `make format` | Format code using ruff |
| `make lint` | Lint code using ruff |
| `make format-check` | Check if code is formatted correctly |
| `make fix` | Auto-fix linting issues |
| `make check-types` | Type check code using mypy |
| `make type-check` | Alias for `check-types` |
| `make check` | Run all quality checks (format-check, lint, check-types) |

## Documentation

| Target | Description |
|--------|-------------|
| `make docs` | Build documentation (include the [coverage report](coverage.md) by running `make test-coverage` first) |
| `make docs-serve` | Serve documentation locally (e.g. http://localhost:8000) |
| `make docs-serve-open` | Serve documentation and open in the default browser |
| `make docs-check` | Check documentation for issues (strict build) |

## Other

| Target | Description |
|--------|-------------|
| `make help` | Print the help screen (all targets) |
| `make clean` | Clean up cache and build files |
| `make update-instantiated-template-coverage` | Update instantiated template coverage % in docs/development/testing.md |
| `make setup-cursor` | Copy cursor configuration from config/cursor to .cursor |

## Typical workflow

Before committing:

1. `make format` — format code
2. `make check` — run all quality checks
3. `make test` — run tests

If you change docs or dependencies:

- `make docs-serve` — preview at http://localhost:8000
- `make docs-check` — ensure docs build in strict mode
