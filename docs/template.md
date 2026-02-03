# The template

Repoman uses a single **Copier** template to generate Python projects. This page describes what the template is, how it is configured, what it generates, and how optional features work.

## What the template is

- **Single Copier template** used by `repoman create` and `repoman update`. When you run `repoman create my-project`, Copier runs against this template with your answers and writes the generated project to disk.
- **Location:** The template lives under `src/repoman/main_template/`. Copier is configured in `src/repoman/copier.yml` (in the repoman repo), which defines prompts, defaults, and `_subdirectory: main_template/` so Copier uses that directory as the template root.
- **Rendering:** All template files use the `.jinja` suffix. Copier + Jinja2 render them with your answers and repoman's custom Jinja extensions (e.g. `slugify`, `git_user_name`, `current_year`). Answers are stored in `.copier-answers.yml` in the generated project and are used again by `repoman update` to re-apply the template.

For the full list of prompts and defaults, see [Template prompts](template-prompts.md). For conditional structure and generated layout, see [Template structure](template-structure.md).

## Adding new CLI commands (generator add)

Generated projects that have a CLI can add new subcommands without editing repoman's core template:

- **Command:** `repoman generator add <command_name>`
- **What it does:** Uses the **command template** under `src/repoman/extentions/command_template/` (the directory is named `extentions` in the repo—historical spelling). It creates a new command module under `src/{{ package }}/cli/commands/<command_name>/` and a test file under `tests/test_cli/test_<command_name>.py`.

So the generated project's CLI stays extensible by adding commands that follow the same pattern (e.g. user-added subcommands).

## Custom Jinja extensions

During Copier render, repoman uses custom Jinja extensions (defined in `src/repoman/extensions.py` and referenced in copier `_jinja_extensions`):

- **SlugifyExtension:** Provides `slugify` (e.g. `slugify('_')` for Python import names). Used in defaults for package and CLI names.
- **GitExtension:** Provides `git_user_name` and `git_user_email` for author defaults when Git is configured.
- **CurrentYearExtension:** Provides `current_year` for copyright and other dates.

These are used in `copier.yml` defaults and in template files; you do not need to configure them when running `repoman create` or `repoman update`.

## See also

- [Template prompts](template-prompts.md)
- [Template structure](template-structure.md)
