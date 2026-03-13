# AGENTS.md

Guidance for AI agents working on the repoman repo. Keep changes aligned with
project conventions, architecture, and quality standards.

## Quick Start

- Install deps: `uv sync`
- Run tests: `make test`
- Run checks: `make check`
- Run CLI: `uv run python -m repoman --help`

## Architecture and Layering

Repoman is intentionally layered. Keep the direction of dependencies intact:

- `repoman.copier`, `repoman.config`, and `repoman.hotspots` are pure logic (no Typer/Rich/CLI).
- `repoman.cli` contains all UX, Typer, and Rich usage.
- Call flow is `cli` → `repoman.copier` / `repoman.config`, never the reverse.

See `docs/development/architecture.md` for module relationships and flows.

## Templates and Generators

- Main template lives in `src/repoman/main_template/`.
- The `src/repoman/extentions` directory name is intentional; do not rename it.
- When editing templates, consider impacts to tests in `tests/test_template/`.

## Code Quality

Use Ruff and MyPy configurations in `config/`:

- Lint: `make lint`
- Format: `make format`
- Type check: `make type-check`
- Full check: `make check`

Ruff rules are in `config/ruff.toml`. Prefer fixing issues over adding ignores.

## Testing

- Full suite: `make test`
- Focused runs: `make test-unit`, `make test-cli`, `make test-utils`
- Single file: `make test-single FILE=tests/path/to/test_file.py`
- Direct pytest: `uv run pytest -c=config/pytest.ini tests/`

See `docs/development/testing.md` for categories, fixtures, and troubleshooting.

## Documentation

- Development docs: `docs/development/`
- CLI reference: `docs/cli.md`
- Template reference: `docs/template.md`

Update docs when behavior or commands change.

## AI Usage Policy (External Contributions)

If preparing content for external contribution or release, follow
`AI_POLICY.md`:

- Disclose AI usage and tools.
- AI-generated PRs require an accepted issue and human verification.
- No AI-generated media.

Maintainers may have additional discretion; when in doubt, follow the policy.
