# Copier and answers

Repoman uses **Copier** to generate projects. Copier is a template engine: it asks you questions (prompts), stores your answers, and renders the template files with those answers.

## Prompts and answers

When you run `repoman create` or `repoman update`, the prompts you see (project name, author, CI system, optional FastAPI/RAG, etc.) come from the template’s configuration. Your responses are the **answers**. The full list of prompts and defaults is in [Template prompts](../template-prompts.md).

## Where answers are stored

Answers are saved in **`.copier-answers.yml`** in the **generated project** directory (the project you created or are updating). That file records the choices you made so that:

- **`repoman update`** can re-run the template without asking again (it reuses the same answers unless you override them).
- You can edit `.copier-answers.yml` for non-interactive runs (e.g. in CI) and pass it with `--answers`.

Repoman does not store a separate config file for itself; configuration is the template’s answers.

## How repoman update uses answers

When you run `repoman update <project_dir>`:

1. Repoman (and Copier) read `.copier-answers.yml` from that project directory.
2. The template is re-applied with those answers, so only changed template files or answers cause updates.
3. You can override the answers file with `--answers` or the template with `--template`; see [Updating a project](../guides/updating-a-project.md) and the [CLI reference](../cli.md).

For the exact prompts and defaults, see [Template prompts](../template-prompts.md).
