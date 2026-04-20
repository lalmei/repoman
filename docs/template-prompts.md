# Copier prompts

The following prompts are defined in `src/repoman/copier.yml`.

## Core project prompts

Repoman prompts for:

- CI host (`ci`)
- project metadata (`project_name`, `project_description`)
- author and repository metadata
- license and copyright data
- Python package and CLI names
- container registry

## Optional features

### FastAPI

| Prompt                     | Description                          | Default |
| -------------------------- | ------------------------------------ | ------- |
| `fastapi_enabled`          | Enable FastAPI application structure | `true`  |
| `fastapi_docs_url`         | OpenAPI docs path                    | `/docs` |
| `fastapi_api_prefix`       | API route prefix                     | `/api`  |
| `fastapi_debug`            | Enable FastAPI debug mode            | `false` |
| `include_health_endpoints` | Include health and ready endpoints   | `true`  |
| `aiohttp_timeout`          | HTTP client timeout (seconds)        | `2`     |
| `aiohttp_pool_size`        | HTTP client pool size                | `100`   |

### Notebooks

| Prompt             | Description                       | Default |
| ------------------ | --------------------------------- | ------- |
| `python_notebooks` | Include Jupyter notebooks support | `false` |

### Datasets

| Prompt                     | Description                                                | Default |
| -------------------------- | ---------------------------------------------------------- | ------- |
| `dataset_enabled`          | Include dataset module for PyTorch data loading and config | `false` |
| `dataset_modality_image`   | Image classification datasets                              | `true`  |
| `dataset_modality_text`    | Text datasets                                              | `true`  |
| `dataset_modality_tabular` | Tabular datasets                                           | `true`  |
| `dataset_modality_mesh`    | 3D mesh datasets                                           | `true`  |

When `dataset_enabled` is true, at least one dataset modality must be selected.

## Where answers are stored

Generated projects store answers in `.copier-answers.yml`. Repoman uses that file for `repoman update` and for non-interactive workflows.
