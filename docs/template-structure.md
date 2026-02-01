# Template structure

## Conditional structure (what changes with answers)

- **CI:** Only one of `.github/`, `.gitlab/`, or `.azuredevops/` is rendered. The rest are omitted. Each includes workflows (e.g. ci, release) and issue templates (bug, feature, docs, change).
- **CLI:** If `python_package_command_line_name` is set, the template generates:
  - `src/{{ python_package_import_name }}/cli/` (main_cli, register, commands/),
  - `__main__.py`,
  - and a `[project.scripts]` entry in `pyproject.toml`.
    Otherwise no CLI code or entry point is generated.
- **FastAPI:** If `fastapi_enabled` is true, the template generates `src/{{ python_package_import_name }}/app/` with the FastAPI app, ASGI, router, health/ready endpoints (when `include_health_endpoints` is true), config, controllers, views, state, exceptions, and utils (e.g. aiohttp client). If false, no `app/` directory is generated.
- **Insiders:** The template supports optional `insiders` and `public_release` variables. When used, some docs or assets can be gated for "insiders" (e.g. sponsors). See the template source and docs for details if you extend the template that way.

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
      - :fontawesome-solid-folder: **commands/** (user-defined subcommands)
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
