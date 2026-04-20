# Template structure

## Conditional structure

- **CI:** Exactly one of `.github/`, `.gitlab/`, or `.azuredevops/` is rendered.
- **CLI:** If `python_package_command_line_name` is set, the template generates `src/{{ python_package_import_name }}/cli/`, `__main__.py`, and a `[project.scripts]` entry in `pyproject.toml`.
- **FastAPI:** If `fastapi_enabled` is true, the template generates `src/{{ python_package_import_name }}/app/` with the ASGI entry point, router, controllers, views, state, exceptions, and utilities.
- **Datasets:** If `dataset_enabled` is true, the template generates `config/dataset_config.json`, `src/{{ python_package_import_name }}/config/dataset_config.py`, and the selected dataset loaders/adapters under `src/{{ python_package_import_name }}/datasets/`.
- **Docs-only:** If `docs_only` is true, source package and test files are omitted.
- **Notebooks:** If `python_notebooks` is true, the template generates a `notebooks/` folder.

## High-level generated layout

With typical defaults the generated project looks like:

```text
my_project/
├── config/
├── docs/
├── make_cmds/
├── notebooks/
├── scripts/
├── src/
│   └── <package>/
│       ├── app/          # optional FastAPI
│       ├── cli/          # optional CLI
│       ├── config/
│       ├── datasets/     # optional dataset support
│       └── utils/
└── tests/
```

## Key generated artifacts

- **`Makefile`** composes the `make_cmds/` fragments and exposes the main developer workflows.
- **`pyproject.toml`** defines package metadata, dependencies, optional CLI entry points, and dependency groups.
- **`src/<package>/config/`** holds the shared config models, plus optional FastAPI and dataset config.
- **`src/<package>/cli/`** contains the Typer application and dynamic command registration when CLI support is enabled.
- **`src/<package>/app/`** contains the FastAPI application when FastAPI is enabled.
- **`src/<package>/datasets/`** contains the selected dataset loaders and helpers when dataset support is enabled.

For prompt-level details, see [Template prompts](template-prompts.md). For generated behavior, see [Template architecture](concepts/template-architecture.md).
