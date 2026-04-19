# Generated project

This page summarizes what a repoman-generated project contains. For conditional structure and file layout, see [Template structure](../template-structure.md). For generated behavior, see [Template architecture](template-architecture.md).

## Layout

Generated projects typically include:

- `src/<package>/` for the main Python package
- `tests/` for pytest-based tests
- `config/` for Ruff, MyPy, pytest, MkDocs, and related config
- `docs/` for project documentation
- `make_cmds/` for Makefile fragments
- `pyproject.toml` for package metadata and dependencies

## Optional features

- **CLI:** If a CLI name is provided, the template generates a Typer-based CLI.
- **FastAPI:** If FastAPI is enabled, the template generates `src/<package>/app/`.
- **Datasets:** If dataset support is enabled, the template generates dataset config and the selected loaders under `src/<package>/datasets/`.
