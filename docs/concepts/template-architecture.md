# Template architecture

This page describes the main optional parts of the repoman template. Template source lives under `src/repoman/main_template/`; generated code ends up under `src/<package>/` in the created project.

## FastAPI template

When `fastapi_enabled` is true, the template generates an `app/` package with a conventional FastAPI setup:

- **Entry point:** `app/asgi.py` exposes `get_application()`.
- **Lifespan:** Startup loads `Config()`, stores it on `app.state.config`, and initializes the shared `AiohttpClient`. Shutdown closes the client.
- **Router:** `app/router.py` applies the configured API prefix and mounts health/ready endpoints when `include_health_endpoints` is true.
- **Supporting modules:** Controllers, views, exceptions, state helpers, and the aiohttp client live under `app/`.

## Configuration

Shared configuration is loaded through `Config()` in `config/main_config.py`.

- **`FastAPIConfig`** is included when FastAPI support is enabled.
- **`DatasetConfig`** is included when dataset support is enabled.

## Dataset template

When `dataset_enabled` is true, the template generates a dataset module and configuration artifacts for the selected modalities:

- **Config model:** `config/dataset_config.py`
- **Default config file:** `config/dataset_config.json`
- **Loaders and helpers:** `src/<package>/datasets/`

Supported modalities are:

- `image`
- `text`
- `tabular`
- `mesh`

The dataset loader factory dispatches by `DatasetConfig.modality` and only exposes loaders for the enabled modalities in the generated project.

## Layering

Repoman keeps interface code separate from reusable logic:

- **CLI layer:** Typer and Rich usage stays in `cli/`.
- **FastAPI layer:** HTTP wiring stays in `app/`.
- **Core/config/data logic:** Shared logic stays in `config/`, `datasets/`, and other package modules.

For conditional file layout, see [Template structure](../template-structure.md).
