# Generated project

This page summarizes what a repoman-generated project contains. For conditional structure and file layout, see [Template structure](../template-structure.md). For FastAPI and RAG internals, see [Template architecture](template-architecture.md).

## Layout (high-level)

After you run `repoman create --project_name my-project` with typical options, the generated project includes:

- **`src/<package>/`** — Main Python package (config, utils, optional CLI, optional `app/` for FastAPI, optional `rag/` for RAG).
- **`tests/`** — Test package and test modules (pytest).
- **`config/`** — Config files for Ruff, MyPy, pytest, MkDocs, coverage, etc.
- **`docs/`** — Documentation source (MkDocs).
- **`make_cmds/`** — Makefile fragments (tests, quality, docs, build, uv) included by the top-level `Makefile`.
- **`Makefile`** — Composes the make_cmds and defines versioning and project-specific targets.
- **`pyproject.toml`** — Project metadata, dependencies, optional `[project.scripts]` for the CLI.

## CI

Exactly **one** CI system is included, depending on your answer: **GitHub Actions** (`.github/`), **GitLab CI** (`.gitlab-ci.yml` with optional `.gitlab/` metadata), or **Azure DevOps** (`.azuredevops/`). Each includes provider-specific CI definitions.

## Optional features

- **CLI** — If you set a CLI name (e.g. `my-app`), the template generates a Typer-based CLI under `src/<package>/cli/` and a `[project.scripts]` entry. You can add subcommands later with `repoman generator add <command_name>` (see [Adding a CLI command](../guides/adding-a-cli-command.md)).
- **FastAPI** — If FastAPI is enabled, the template generates `src/<package>/app/` with an ASGI app, router, config, controllers, views, and optional health/ready endpoints.
- **RAG** — If RAG is enabled, the template generates the RAG package, CLI subcommands (`rag ingest`, `rag query`), and when FastAPI is enabled, API routes under `/rag`. See [Template architecture](template-architecture.md) for the architecture.

For the exact file tree and conditional logic, see [Template structure](../template-structure.md).
