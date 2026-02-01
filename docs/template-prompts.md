# Copier prompts

The following prompts are defined in `src/repoman/copier.yml` (in the repoman repo). They are grouped by purpose.

## CI

| Prompt  | Description                 | Default  |
| ------- | --------------------------- | -------- |
| `ci`    | Which CI system to use      | `github` |
| Choices | `github`, `gitlab`, `azure` | —        |

Only the chosen CI directory (`.github/`, `.gitlab/`, or `.azuredevops/`) is included in the generated project (workflows, issue templates).

## Project

| Prompt                | Description              |
| --------------------- | ------------------------ |
| `project_name`        | Your project name        |
| `project_description` | Your project description |

## Author

| Prompt            | Description                    | Default                              |
| ----------------- | ------------------------------ | ------------------------------------ |
| `author_fullname` | Your full name                 | From Git `user.name` when available  |
| `author_email`    | Your email                     | From Git `user.email` when available |
| `author_username` | Your username (e.g. on GitHub) | Set in template                      |

## Repository

| Prompt                 | Description                      | Default                                    |
| ---------------------- | -------------------------------- | ------------------------------------------ |
| `repository_provider`  | Repository host                  | `github.com`, `gitlab.com`, or `azure.com` |
| `repository_namespace` | Namespace (e.g. GitHub user/org) | `author_username`                          |
| `repository_name`      | Repository name                  | Slugified `project_name`                   |

## Copyright

| Prompt                   | Description            | Default                       |
| ------------------------ | ---------------------- | ----------------------------- |
| `copyright_holder`       | Copyright holder name  | `author_fullname`             |
| `copyright_holder_email` | Copyright holder email | `author_email`                |
| `copyright_date`         | Copyright date         | Current year (from extension) |
| `copyright_license`      | Project license (SPDX) | `ISC`                         |

`copyright_license` offers a long list of choices (e.g. MIT, Apache-2.0, GPL-3.0, BSD-3-Clause). These are used in `pyproject.toml`, LICENSE, and docs.

## Python package

| Prompt                             | Description                                   | Default                    |
| ---------------------------------- | --------------------------------------------- | -------------------------- |
| `python_package_distribution_name` | Name for `pip install NAME`                   | Slugified `project_name`   |
| `python_package_import_name`       | Name for `import NAME` in Python              | Slugified with underscores |
| `python_package_command_line_name` | CLI entry point name (e.g. `my-app`)          | Slugified `project_name`   |
| `python_distribution_name`         | Used for container images (e.g. Azure DevOps) | Same as distribution name  |

If `python_package_command_line_name` is set, the template generates a Typer-based CLI and a `[project.scripts]` entry; otherwise no CLI is generated.

## Container

| Prompt               | Description                          | Default     |
| -------------------- | ------------------------------------ | ----------- |
| `container_registry` | Container registry for Docker images | `docker.io` |

Used in the Makefile for image tagging (e.g. for deployment).

## FastAPI (optional)

| Prompt                     | Description                          | Default |
| -------------------------- | ------------------------------------ | ------- |
| `fastapi_enabled`          | Enable FastAPI application structure | `true`  |
| `fastapi_docs_url`         | OpenAPI docs path                    | `/docs` |
| `fastapi_api_prefix`       | API route prefix                     | `/api`  |
| `fastapi_debug`            | Enable FastAPI debug mode            | `false` |
| `include_health_endpoints` | Include health and ready endpoints   | `true`  |
| `aiohttp_timeout`          | HTTP client timeout (seconds)        | `2`     |
| `aiohttp_pool_size`        | HTTP client pool size                | `100`   |

When `fastapi_enabled` is true, the template generates `src/{{ package }}/app/` with a FastAPI app, ASGI entry, router, config, controllers, views, state, and utils (e.g. aiohttp client). Health/ready endpoints are optional via `include_health_endpoints`.

---

Answers are stored in `.copier-answers.yml` in the generated project. That file is used by `repoman update` to re-apply the template (e.g. after pulling template changes).
