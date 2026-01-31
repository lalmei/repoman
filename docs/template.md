# The template

Repoman uses a single **Copier** template to generate Python projects. This page describes what the template is, how it is configured, what it generates, and how optional features work.

## What the template is

- **Single Copier template** used by `repoman create` and `repoman update`. When you run `repoman create my-project`, Copier runs against this template with your answers and writes the generated project to disk.
- **Location:** The template lives under `src/repoman/main_template/`. Copier is configured in `src/repoman/copier.yml`, which defines prompts, defaults, and `_subdirectory: main_template/` so Copier uses that directory as the template root.
- **Rendering:** All template files use the `.jinja` suffix. Copier + Jinja2 render them with your answers and repoman’s custom Jinja extensions (e.g. `slugify`, `git_user_name`, `current_year`). Answers are stored in `.copier-answers.yml` in the generated project and are used again by `repoman update` to re-apply the template.

## Copier prompts (what you are asked)

The following prompts are defined in [copier.yml](../src/repoman/copier.yml). They are grouped by purpose.

### CI

| Prompt | Description | Default |
|--------|-------------|---------|
| `ci` | Which CI system to use | `github` |
| Choices | `github`, `gitlab`, `azure` | — |

Only the chosen CI directory (`.github/`, `.gitlab/`, or `.azuredevops/`) is included in the generated project (workflows, issue templates).

### Project

| Prompt | Description |
|--------|-------------|
| `project_name` | Your project name |
| `project_description` | Your project description |

### Author

| Prompt | Description | Default |
|--------|-------------|---------|
| `author_fullname` | Your full name | From Git `user.name` when available |
| `author_email` | Your email | From Git `user.email` when available |
| `author_username` | Your username (e.g. on GitHub) | Set in template |

### Repository

| Prompt | Description | Default |
|--------|-------------|---------|
| `repository_provider` | Repository host | `github.com`, `gitlab.com`, or `azure.com` |
| `repository_namespace` | Namespace (e.g. GitHub user/org) | `author_username` |
| `repository_name` | Repository name | Slugified `project_name` |

### Copyright

| Prompt | Description | Default |
|--------|-------------|---------|
| `copyright_holder` | Copyright holder name | `author_fullname` |
| `copyright_holder_email` | Copyright holder email | `author_email` |
| `copyright_date` | Copyright date | Current year (from extension) |
| `copyright_license` | Project license (SPDX) | `ISC` |

`copyright_license` offers a long list of choices (e.g. MIT, Apache-2.0, GPL-3.0, BSD-3-Clause). These are used in `pyproject.toml`, LICENSE, and docs.

### Python package

| Prompt | Description | Default |
|--------|-------------|---------|
| `python_package_distribution_name` | Name for `pip install NAME` | Slugified `project_name` |
| `python_package_import_name` | Name for `import NAME` in Python | Slugified with underscores |
| `python_package_command_line_name` | CLI entry point name (e.g. `my-app`) | Slugified `project_name` |
| `python_distribution_name` | Used for container images (e.g. Azure DevOps) | Same as distribution name |

If `python_package_command_line_name` is set, the template generates a Typer-based CLI and a `[project.scripts]` entry; otherwise no CLI is generated.

### Container

| Prompt | Description | Default |
|--------|-------------|---------|
| `container_registry` | Container registry for Docker images | `docker.io` |

Used in the Makefile for image tagging (e.g. for deployment).

### FastAPI (optional)

| Prompt | Description | Default |
|--------|-------------|---------|
| `fastapi_enabled` | Enable FastAPI application structure | `true` |
| `fastapi_docs_url` | OpenAPI docs path | `/docs` |
| `fastapi_api_prefix` | API route prefix | `/api` |
| `fastapi_debug` | Enable FastAPI debug mode | `false` |
| `include_health_endpoints` | Include health and ready endpoints | `true` |
| `aiohttp_timeout` | HTTP client timeout (seconds) | `2` |
| `aiohttp_pool_size` | HTTP client pool size | `100` |

When `fastapi_enabled` is true, the template generates `src/{{ package }}/app/` with a FastAPI app, ASGI entry, router, config, controllers, views, state, and utils (e.g. aiohttp client). Health/ready endpoints are optional via `include_health_endpoints`.

---

Answers are stored in `.copier-answers.yml` in the generated project. That file is used by `repoman update` to re-apply the template (e.g. after pulling template changes).

## Conditional structure (what changes with answers)

- **CI:** Only one of `.github/`, `.gitlab/`, or `.azuredevops/` is rendered. The rest are omitted. Each includes workflows (e.g. ci, release) and issue templates (bug, feature, docs, change).
- **CLI:** If `python_package_command_line_name` is set, the template generates:
  - `src/{{ python_package_import_name }}/cli/` (main_cli, register, commands/),
  - `__main__.py`,
  - and a `[project.scripts]` entry in `pyproject.toml`.
  Otherwise no CLI code or entry point is generated.
- **FastAPI:** If `fastapi_enabled` is true, the template generates `src/{{ python_package_import_name }}/app/` with the FastAPI app, ASGI, router, health/ready endpoints (when `include_health_endpoints` is true), config, controllers, views, state, exceptions, and utils (e.g. aiohttp client). If false, no `app/` directory is generated.
- **Insiders:** The template supports optional `insiders` and `public_release` variables. When used, some docs or assets can be gated for “insiders” (e.g. sponsors). See the template source and docs for details if you extend the template that way.

## Generated project layout (high-level)

After you run `repoman create my-project` (with typical defaults, e.g. CLI + FastAPI enabled), the generated tree looks like this at a high level. File trees in this documentation use Font Awesome icons for file types (folders, Python, Markdown, config, etc.).

### Instantiated project file tree

:fontawesome-solid-folder: **my_project/**

- :fontawesome-solid-file-code: `.copier-answers.yml`
- :fontawesome-solid-file: `.gitignore`
- :fontawesome-solid-file-lines: `AI_POLICY.md`
- :fontawesome-solid-file-lines: `CHANGELOG.md`
- :fontawesome-solid-file-lines: `CODE_OF_CONDUCT.md`
- :fontawesome-solid-file-lines: `CONTRIBUTING.md`
- :fontawesome-solid-file: `LICENSE`
- :fontawesome-solid-file-code: `Makefile`
- :fontawesome-solid-file-lines: `README.md`
- :fontawesome-solid-folder: **config/**
  - :fontawesome-solid-file-code: `coverage.ini`
  - :fontawesome-solid-file-code: `git-changelog.toml`
  - :fontawesome-solid-file-code: `mkdocs.yml`
  - :fontawesome-solid-file-code: `mypy.ini`
  - :fontawesome-solid-file-code: `pytest.ini`
  - :fontawesome-solid-file-code: `ruff.toml`
  - :fontawesome-solid-folder: **vscode/**
    - :fontawesome-solid-file-code: `launch.json`
    - :fontawesome-solid-file-code: `settings.json`
    - :fontawesome-solid-file-code: `tasks.json`
- :fontawesome-solid-folder: **docs/**
  - :fontawesome-solid-folder: **.overrides/** (partials, main.html)
  - :fontawesome-solid-file-lines: `changelog.md`
  - :fontawesome-solid-file-lines: `contributing.md`
  - :fontawesome-solid-file-lines: `index.md`
  - :fontawesome-solid-folder: **reference/** (API)
  - :fontawesome-brands-css3-alt: `css/` (material.css, mkdocstrings.css)
  - :fontawesome-brands-js: `js/` (feedback.js)
- :fontawesome-solid-folder: **make_cmds/**
  - :fontawesome-solid-file-code: `build.mk`
  - :fontawesome-solid-file-code: `documentation.mk`
  - :fontawesome-solid-file-code: `quality.mk`
  - :fontawesome-solid-file-code: `tests.mk`
  - :fontawesome-solid-file-code: `uv.mk`
- :fontawesome-solid-folder: **scripts/**
  - :fontawesome-brands-python: `colors.py`
  - :fontawesome-brands-python: `gen_credits.py`
  - :fontawesome-brands-python: `get_version.py`
- :fontawesome-solid-folder: **src/**
  - :fontawesome-solid-folder: **my_project/** (package; name from `python_package_import_name`)
    - :fontawesome-brands-python: `__init__.py`
    - :fontawesome-brands-python: `_version.py`
    - :fontawesome-solid-folder: **config/**
      - :fontawesome-brands-python: `__init__.py`
      - :fontawesome-brands-python: `main_config.py`
      - :fontawesome-brands-python: `fastapi_config.py` (if FastAPI enabled)
    - :fontawesome-solid-folder: **utils/**
      - :fontawesome-brands-python: `__init__.py`
      - :fontawesome-brands-python: `logging.py`
      - :fontawesome-solid-folder: **theme/** (terminal colors)
    - :fontawesome-solid-folder: **cli/** (if CLI enabled)
      - :fontawesome-brands-python: `__init__.py`
      - :fontawesome-brands-python: `main_cli.py`
      - :fontawesome-brands-python: `register.py`
      - :fontawesome-solid-folder: **commands/** (info, etc.)
    - :fontawesome-solid-folder: **app/** (if FastAPI enabled)
      - :fontawesome-brands-python: `__init__.py`
      - :fontawesome-brands-python: `asgi.py`
      - :fontawesome-solid-folder: **controllers/**, **views/**, **state/**, **exceptions/**, **utils/**
- :fontawesome-solid-folder: **tests/**
  - :fontawesome-brands-python: `conftest.py`
  - :fontawesome-solid-folder: **test_cli/** (if CLI)
  - :fontawesome-solid-folder: **test_app/** (if FastAPI)
  - :fontawesome-solid-folder: **unit/**, **smoke/** (from template)
- :fontawesome-solid-folder: **.github/** (or `.gitlab/` or `.azuredevops/` per `ci` choice)
  - :fontawesome-solid-folder: **workflows/** (`ci.yml`, `release.yml`)
  - :fontawesome-solid-folder: **ISSUE_TEMPLATE/** (bug, feature, docs, change)

You can compare this with the output of `repoman create my-project` to see the exact files and structure for your choices.

## Key generated artifacts

- **Makefile:** Composes the make_cmds (uv, quality, tests, documentation, build). Defines versioning targets (e.g. bump-patch, bump-minor, bump-major), image tags, and project-specific variables (e.g. `python_package_distribution_name`). Uses `uv` for running commands.
- **pyproject.toml:** Project name, description, authors, license, dependencies (e.g. typer, rich, pydantic; optional fastapi, aiohttp), optional `[project.scripts]` for the CLI, uv config, and dependency-groups (dev, ml, docs, etc.).
- **Package layout:** Config module (main_config, optional fastapi_config), utils (logging, theme), CLI with dynamic command discovery from `cli/commands/`, and optionally a FastAPI app with configurable docs URL and API prefix.

## Adding new CLI commands (generator add)

Generated projects that have a CLI can add new subcommands without editing repoman’s core template:

- **Command:** `repoman generator add <command_name>`
- **What it does:** Uses the **command template** under `src/repoman/extentions/command_template/` (note: the directory is spelled “extentions” in the codebase). It creates a new command module under `src/{{ package }}/cli/commands/<command_name>/` and a test file under `tests/test_cli/test_<command_name>.py`.

So the generated project’s CLI stays extensible by adding commands that follow the same pattern as the built-in ones (e.g. info).

## Custom Jinja extensions

During Copier render, repoman uses custom Jinja extensions (defined in `src/repoman/extensions.py` and referenced in copier `_jinja_extensions`):

- **SlugifyExtension:** Provides `slugify` (e.g. `slugify('_')` for Python import names). Used in defaults for package and CLI names.
- **GitExtension:** Provides `git_user_name` and `git_user_email` for author defaults when Git is configured.
- **CurrentYearExtension:** Provides `current_year` for copyright and other dates.

These are used in `copier.yml` defaults and in template files; you do not need to configure them when running `repoman create` or `repoman update`.
