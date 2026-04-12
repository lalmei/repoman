# Copier and answers

Repoman uses **Copier** to generate projects. Copier is a template engine: it asks you questions (prompts), stores your answers, and renders the template files with those answers.

## Prompts and answers

When you run `repoman create` or `repoman update`, the prompts you see (project name, author, CI system, optional FastAPI/RAG, etc.) come from the template’s configuration. Your responses are the **answers**. The full list of prompts and defaults is in [Template prompts](../template-prompts.md).

## Where answers are stored

Answers are saved in **`.copier-answers.yml`** in the **generated project** directory (the project you created or are updating). That file records the choices you made so that:

- **`repoman update`** can re-run the template without asking again (it reuses the same answers unless you override them).
- You can edit `.copier-answers.yml` for non-interactive runs (e.g. in CI) and pass it with `--answers`.

Repoman does not store a separate config file for itself; configuration is the template’s answers.

## Internal Copier keys (`_src_path`, `_commit`, `_vcs_ref`)

Besides your prompt answers, `.copier-answers.yml` can contain **metadata** that Copier records:

- **`_src_path`** — Where the template came from (path or URL).
- **`_commit`** — The Git revision of the template used for the last **copy** or **update**.
- **`_vcs_ref`** — May appear alongside other Copier bookkeeping.

For **`repoman update`** (and Copier update), **`_commit` must be present** when **`_src_path` is set**, so Copier can load the previous template revision. If `_commit` is missing, updates fail until you repair the file. See [Copier update metadata](../guides/updating-a-project.md#copier-update-metadata) in *Updating a project* for why this happens, CI stripping pitfalls, and how to set `_commit` using `git describe --tags --always`.

## How repoman update uses answers

When you run `repoman update <project_dir>`:

1. Repoman (and Copier) read `.copier-answers.yml` from that project directory.
2. The template is re-applied with those answers, so only changed template files or answers cause updates.
3. You can override the answers file with `--answers` or the template with `--template`; see [Updating a project](../guides/updating-a-project.md) and the [CLI reference](../cli.md).

For the exact prompts and defaults, see [Template prompts](../template-prompts.md).
