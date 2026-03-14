# Template structure

## Conditional structure (what changes with answers)

- **CI:** Only one provider-specific CI setup is rendered. GitHub uses `.github/`, GitLab uses `.gitlab-ci.yml` plus optional `.gitlab/` metadata, and Azure uses `.azuredevops/`. The other provider CI files are omitted.
- **CLI:** If `python_package_command_line_name` is set, the template generates:
  - `src/{{ python_package_import_name }}/cli/` (main_cli, register, commands/),
  - `__main__.py`,
  - and a `[project.scripts]` entry in `pyproject.toml`.
    Otherwise no CLI code or entry point is generated.
- **FastAPI:** If `fastapi_enabled` is true, the template generates `src/{{ python_package_import_name }}/app/` with the FastAPI app, ASGI, router, health/ready endpoints (when `include_health_endpoints` is true), config, controllers, views, state, exceptions, and utils (e.g. aiohttp client). If false, no `app/` directory is generated.
- **RAG:** If `rag_enabled` is true, the template generates `src/{{ python_package_import_name }}/rag/` (service, container, pipelines, ports/adapters), CLI subcommands `rag ingest` and `rag query`, optional `RAGConfig` and `rag_config`, and when FastAPI is enabled, API routes under `/rag` (health, query, ingest). If false, no RAG code or routes are generated. See [Template architecture](concepts/template-architecture.md) for details.
- **Insiders:** The template supports optional `insiders` and `public_release` variables. When used, some docs or assets can be gated for "insiders" (e.g. sponsors). See the template source and docs for details if you extend the template that way.
- **Notebooks:** If `python_notebooks` is true, the template generates a `notebooks/` folder. The example notebook is stored in the template as `example_notebook.ipynb.jinja` and is rendered to `example_notebook.ipynb` in the instantiated project.

## Generated project layout (high-level)

After you run `repoman create --project_name my-project` (with typical defaults, e.g. CLI + FastAPI enabled), the generated tree looks like this at a high level. Regenerate with `make docs-trees`.

### Instantiated project file tree

<!-- TREE_START:instantiated -->
```
my_project
├── AI_POLICY.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── config
│   ├── coverage.ini
│   ├── dataset_config.json
│   ├── git-changelog.toml
│   ├── mkdocs.yml
│   ├── mypy.ini
│   ├── pytest.ini
│   ├── ruff.toml
│   └── vscode
│       ├── launch.json
│       ├── settings.json
│       └── tasks.json
├── CONTRIBUTING.md
├── docs
│   ├── ai_policy.md
│   ├── changelog.md
│   ├── code_of_conduct.md
│   ├── contributing.md
│   ├── credits.md
│   ├── css
│   │   ├── material.css
│   │   └── mkdocstrings.css
│   ├── index.md
│   ├── js
│   │   └── feedback.js
│   ├── license.md
│   └── reference
│       ├── api.md
│       └── architecture.md
├── LICENSE
├── make_cmds
│   ├── build.mk
│   ├── documentation.mk
│   ├── notebooks.mk
│   ├── quality.mk
│   ├── tests.mk
│   └── uv.mk
├── Makefile
├── notebooks
│   └── example_notebook.ipynb
├── pyproject.toml
├── README.md
├── scripts
│   ├── colors.py
│   └── gen_credits.py
├── src
│   └── test_project
│       ├── __init__.py
│       ├── __main__.py
│       ├── _version.py
│       ├── app
│       │   ├── __init__.py
│       │   ├── asgi.py
│       │   ├── controllers
│       │   │   ├── __init__.py
│       │   │   ├── health_check.py
│       │   │   ├── rag
│       │   │   └── ready.py
│       │   ├── exceptions
│       │   │   ├── __init__.py
│       │   │   └── http.py
│       │   ├── router.py
│       │   ├── state
│       │   │   ├── __init__.py
│       │   │   └── app_state.py
│       │   ├── utils
│       │   │   ├── __init__.py
│       │   │   └── aiohttp_client.py
│       │   └── views
│       │       ├── __init__.py
│       │       ├── error.py
│       │       └── ready.py
│       ├── cli
│       │   ├── __init__.py
│       │   ├── commands
│       │   │   ├── __init__.py
│       │   │   └── rag
│       │   ├── main_cli.py
│       │   ├── messages
│       │   │   ├── __init__.py
│       │   │   ├── capability.py
│       │   │   ├── error.py
│       │   │   ├── layout.py
│       │   │   ├── message.py
│       │   │   └── warning.py
│       │   └── register.py
│       ├── config
│       │   ├── __init__.py
│       │   ├── dataset_config.py
│       │   ├── fastapi_config.py
│       │   ├── main_config.py
│       │   └── rag_config.py
│       ├── config.py
│       ├── datasets
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── loaders.py
│       │   ├── rag_eval.py
│       │   ├── tabular.py
│       │   ├── text.py
│       │   └── types.py
│       ├── py.typed
│       ├── rag
│       │   ├── __init__.py
│       │   ├── adapters
│       │   │   ├── __init__.py
│       │   │   ├── docstore_sqlite.py
│       │   │   ├── embedder_sentence_transformers.py
│       │   │   ├── llm_stub.py
│       │   │   ├── reranker_sentence_transformers.py
│       │   │   └── vector_faiss.py
│       │   ├── core
│       │   │   ├── __init__.py
│       │   │   ├── pipeline
│       │   │   ├── ports
│       │   │   └── types.py
│       │   ├── eval
│       │   │   └── __init__.py
│       │   ├── infra
│       │   │   ├── __init__.py
│       │   │   └── config.py
│       │   ├── prompts
│       │   │   ├── __init__.py
│       │   │   ├── builder.py
│       │   │   └── templates
│       │   ├── service.py
│       │   └── wiring
│       │       ├── __init__.py
│       │       └── container.py
│       └── utils
│           ├── __init__.py
│           ├── logging.py
│           ├── progress_bar.py
│           └── theme
│               ├── __init__.py
│               ├── terminal_colors.py
│               └── theme.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures
│   │   ├── eval_sample.jsonl
│   │   ├── rag_sample.txt
│   │   └── text_sample.jsonl
│   ├── test_app
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_aiohttp_client.py
│   │   ├── test_asgi.py
│   │   ├── test_exceptions.py
│   │   ├── test_health_ready.py
│   │   ├── test_rag_routes.py
│   │   ├── test_router.py
│   │   ├── test_state.py
│   │   └── test_views_error.py
│   ├── test_cli
│   │   ├── __init__.py
│   │   ├── test_cli.py
│   │   ├── test_command_registration.py
│   │   └── test_messages.py
│   ├── test_config.py
│   ├── test_datasets
│   │   ├── __init__.py
│   │   ├── test_loaders.py
│   │   └── test_tabular.py
│   ├── test_rag
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_chunking.py
│   │   ├── test_rag_commands.py
│   │   ├── test_rag_eval.py
│   │   ├── test_rag_integration.py
│   │   └── test_retrieve.py
│   ├── test_utils
│   │   ├── __init__.py
│   │   ├── test_logging.py
│   │   ├── test_progress_bar.py
│   │   └── test_theme.py
│   └── test_version.py
└── uv.lock
```
<!-- TREE_END -->

You can compare this with the output of `repoman create --project_name my-project` to see the exact files and structure for your choices.

## Key generated artifacts

- **Makefile:** Composes the make_cmds (uv, quality, tests, documentation, build). Defines versioning targets (e.g. bump-patch, bump-minor, bump-major), image tags, and project-specific variables (e.g. `python_package_distribution_name`). Uses `uv` for running commands.
- **pyproject.toml:** Project name, description, authors, license, dependencies (e.g. typer, rich, pydantic; optional fastapi, aiohttp), optional `[project.scripts]` for the CLI, uv config, and dependency-groups (dev, ml, docs, etc.).
- **Package layout:** Config module (main_config, optional fastapi_config), utils (logging, theme), CLI with dynamic command discovery from `cli/commands/`, and optionally a FastAPI app with configurable docs URL and API prefix.
