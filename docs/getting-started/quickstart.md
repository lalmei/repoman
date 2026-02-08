# Quick start

This page walks through creating your first project with repoman in a few steps.

## 1. Install repoman

Install repoman as described in [Installation](installation.md) (e.g. `uv sync` in the repoman repo, or `pip install -e .`).

## 2. Create a project

From the directory where you want the new project folder to appear:

```bash
uv run repoman create --project_name my-project
```

(Or run `repoman create --project_name my-project` if repoman is installed globally.)

Repoman will prompt you for project name, description, author, CI system, Python package name, and optional features (FastAPI, RAG, etc.). You can accept the defaults by pressing Enter, or change them. See [Template prompts](../template-prompts.md) for the full list of prompts.

## 3. Enter the project and install dependencies

```bash
cd my-project
uv sync
```

## 4. Run tests

```bash
make test
```

This confirms the generated project is set up correctly.

## 5. Next steps

- Open the project in your IDE and explore the layout (see [Generated project](../concepts/generated-project.md) and [Template structure](../template-structure.md)).
- Add code, run `make check`, and adjust the template options if you regenerate.
- To change an existing project after template updates, use [Updating a project](../guides/updating-a-project.md).

For more detail on creation options (non-interactive use, custom output path), see [Creating a project](../guides/creating-a-project.md) and the [CLI reference](../cli.md).
