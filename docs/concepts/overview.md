# What is repoman

Repoman is a **Python project generator** and repository management tool. It uses a single **Copier** template to generate new Python projects with a consistent layout, CI, optional CLI, optional FastAPI support, and optional dataset modules.

## When to use repoman

Use repoman when you want to:

- start a new Python project with a standard structure
- get a consistent CI, docs, linting, and typing setup
- generate a project that already includes optional CLI, FastAPI, or dataset scaffolding

## How it works

1. You run `repoman create <project_name>` or `repoman update`.
2. Copier renders the template using your answers.
3. Those answers are stored in `.copier-answers.yml` in the generated project.
