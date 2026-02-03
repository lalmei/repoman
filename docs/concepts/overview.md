# What is repoman

Repoman is a **Python project generator** and repository management tool. It uses a single **Copier** template to generate new Python projects with a consistent layout, CI, optional CLI, optional FastAPI app, and optional RAG (retrieval-augmented generation) or dataset modules.

## When to use repoman

Use repoman when you want to:

- **Start a new Python project** with a standard structure (src layout, tests, config, docs, Makefile).
- **Get a standardized layout** — one of GitHub Actions, GitLab CI, or Azure DevOps; config for Ruff, MyPy, pytest, MkDocs; optional Typer CLI and FastAPI app.
- **Generate a project** that already includes CI, code quality, documentation, and optional features (CLI, FastAPI, RAG) so you can focus on your code.

## When not to use repoman

Repoman is aimed at **new** projects generated from its template. It is less suitable when:

- You have an **existing project** that was not created with repoman and you do not want to adopt the full template layout (you would need to either migrate or use repoman only for new projects).

## How it works

1. You run `repoman create <project_name>` (or `repoman update` for an existing repoman-generated project).
2. Copier runs the template with your answers and writes the generated project to disk.
3. Answers are stored in `.copier-answers.yml` in the generated project and are reused by `repoman update`. See [Copier and answers](copier-and-answers.md) for details.

For a hands-on start, see [Creating a project](../guides/creating-a-project.md). For what the template contains and how it is configured, see [The template](../template.md).
