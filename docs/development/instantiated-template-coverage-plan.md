# Instantiated Template Test Coverage Plan

**Current coverage:** 55.78%  
**Target:** 100%

This document plans the remaining tests needed to achieve 100% test coverage for the **instantiated template**—i.e., the project generated when repoman's main template is instantiated with default answers (`fastapi_enabled: true`, `include_health_endpoints: true`, `python_package_command_line_name: test-project`).

## Overview

Tests live in the template and are instantiated with the project. To improve coverage, we add or extend test files in:

- `src/repoman/main_template/tests/`
- Optionally: `src/repoman/main_template/tests/{% if fastapi_enabled %}test_app{% endif %}/` (new directory for FastAPI tests)

The template uses conditional blocks (`{% if fastapi_enabled %}`, `{% if python_package_command_line_name %}`), so some test files only exist when those options are enabled.

---

## Phase 1: FastAPI App Tests (Highest Impact)

**~200 statements currently at 0% coverage**

### 1.1 Create `test_app` directory and conftest

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/conftest.py.jinja` (new)

- Fixture: `client` → `TestClient(get_application())`
- Ensures all app tests use the same app instance

### 1.2 ASGI / App lifecycle

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_asgi.py.jinja` (new)

Covers: `app/asgi.py` (29 statements), `app/__init__.py`, `app/state/__init__.py`

| Test                                           | Purpose                                                           |
| ---------------------------------------------- | ----------------------------------------------------------------- |
| `test_get_application_returns_fastapi_app`     | Call `get_application()`, assert type and metadata                |
| `test_get_application_with_custom_config`      | Pass `config=Config()` to `get_application(config=...)`           |
| `test_lifespan_startup_stores_config`          | Use `TestClient` with lifespan, verify `app.state.config`         |
| `test_lifespan_shutdown_closes_aiohttp_client` | Verify `AiohttpClient.close_aiohttp_client` is called on shutdown |

### 1.3 Health and Ready endpoints

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_health_ready.py.jinja` (new)

Covers: `app/controllers/health_check.py`, `app/controllers/ready.py`, `app/views/ready.py`

| Test                          | Purpose                                                           |
| ----------------------------- | ----------------------------------------------------------------- |
| `test_healthcheck_returns_ok` | `GET /api/healthcheck` → 200, `{"healthcheck": "Everything OK!"}` |
| `test_ready_returns_ok`       | `GET /api/ready` → 200, `{"status": "ok"}`                        |

### 1.4 Exception handler

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_exceptions.py.jinja` (new)

Covers: `app/exceptions/http.py`, `app/exceptions/__init__.py`

| Test                                                       | Purpose                                                       |
| ---------------------------------------------------------- | ------------------------------------------------------------- |
| `test_http_exception_init_and_repr`                        | Create `HTTPException(404, "Not found")`, assert `__repr__`   |
| `test_http_exception_handler_returns_json_response`        | Raise `HTTPException` in a route, assert response body/status |
| `test_http_exception_handler_re_raises_non_http_exception` | Raise `ValueError`, assert it is re-raised (not converted)    |

### 1.5 Router

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_router.py.jinja` (new)

Covers: `app/router.py`, `app/controllers/__init__.py`, `app/views/__init__.py`

| Test                              | Purpose                                             |
| --------------------------------- | --------------------------------------------------- |
| `test_root_api_router_has_prefix` | Import router, assert `prefix` from config          |
| `test_health_routes_registered`   | `GET /api/healthcheck`, `GET /api/ready` return 200 |

### 1.6 AiohttpClient

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_aiohttp_client.py.jinja` (new)

Covers: `app/utils/aiohttp_client.py` (53 statements), `app/utils/__init__.py`

| Test                                      | Purpose                                                                 |
| ----------------------------------------- | ----------------------------------------------------------------------- |
| `test_get_aiohttp_client_creates_session` | First call creates `ClientSession`, subsequent calls return same        |
| `test_get_aiohttp_client_with_config`     | Pass `fastapi_config` and assert timeout/connector used                 |
| `test_close_aiohttp_client`               | Call `close_aiohttp_client()`, assert session is closed and set to None |
| `test_get_request`                        | Mock aiohttp, call `AiohttpClient.get(url)`, assert request made        |
| `test_post_request`                       | Same for `post`                                                         |
| `test_put_request`                        | Same for `put`                                                          |
| `test_delete_request`                     | Same for `delete`                                                       |
| `test_patch_request`                      | Same for `patch`                                                        |

**Note:** HTTP methods can be tested via `respx` or `aioresponses` to avoid real network calls.

### 1.7 Error views

**File:** `tests/{% if fastapi_enabled %}test_app{% endif %}/test_views_error.py.jinja` (new)

Covers: `app/views/error.py`, `app/views/__init__.py`

| Test               | Purpose                                                    |
| ------------------ | ---------------------------------------------------------- |
| `test_error_model` | Create `ErrorModel`, `ErrorResponse`, assert serialization |

---

## Phase 2: Config and Internal

**~10 statements**

### 2.1 Config

**File:** `tests/test_config.py.jinja` (new) or extend `conftest`

Covers: `config.py` (root, lines 3–9)

| Test                   | Purpose                             |
| ---------------------- | ----------------------------------- |
| `test_config_defaults` | `Config()` has `log_format` default |

## Phase 3: CLI Gaps

**Partially covered: `cli/register.py` 33%, `cli/main_cli.py` 62%**

### 3.1 `cli/register.py` (lines 31–59)

| Test                                                    | Purpose                                              |
| ------------------------------------------------------- | ---------------------------------------------------- |
| `test_register_commands_skips_module_without_app`       | Module with no `app` attr is skipped                 |
| `test_register_commands_handles_duplicate_command_name` | Duplicate name logs warning, skips                   |
| `test_register_commands_handles_import_error`           | Invalid module logs warning, continues               |
| `test_register_commands_handles_attribute_error`        | Bad module structure, continues                      |
| `test_register_commands_with_custom_path`               | `_register_commands(app, path=...)` uses custom path |

**File:** Extend `tests/{% if python_package_command_line_name %}test_cli{% endif %}/test_command_registration.py.jinja`

### 3.2 `cli/main_cli.py` (lines 117–135)

| Test                              | Purpose                                                       |
| --------------------------------- | ------------------------------------------------------------- |
| `test_main_with_verbose`          | `cli --verbose` sets DEBUG level                              |
| `test_main_with_validation_error` | Invalid config → ValidationError, `config` is None in ctx.obj |
| `test_main_sets_ctx_obj`          | `ctx.obj` contains `verbose`, `dry_run`, `theme`, `config`    |

**File:** Extend `tests/{% if python_package_command_line_name %}test_cli{% endif %}/test_cli.py.jinja`

---

## Phase 4: Logging (76.79% → 100%)

**Missing:** lines 135–140, 154–155, 160→159, 167–181

| Test                                                   | Purpose                                                                      |
| ------------------------------------------------------ | ---------------------------------------------------------------------------- |
| `test_get_logger_console_invalid_log_level`            | `get_logger_console(log_level="INVALID")` falls back to INFO                 |
| `test_get_logger_console_same_name_log_level_mismatch` | `name == package_name` and `log_level != root_logger.level` triggers warning |
| `test_get_logger_console_no_rich_handler_fallback`     | Force no rich handler in root_logger, assert fallback console creation       |
| `test_get_logger_console_console_from_handler`         | Branch where handler.get_name() == "rich" returns early                      |

**File:** Extend `tests/test_utils/test_logging.py.jinja`

---

## Phase 5: Progress bar (97.62% → 100%)

**Missing:** branch 94→97 (e.g. `progress is None` when `use_progress_bar` is True)

| Test                                     | Purpose                                                                                      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------- |
| `test_update_before_start_progress_none` | Call `update()` before `start()` when `use_progress_bar=True`; no crash, progress stays None |

**File:** Extend `tests/test_utils/test_progress_bar.py.jinja`

---

## Implementation Order

1. **Phase 1** – FastAPI tests (largest coverage gain)
2. **Phase 2** – Config (small, quick)
3. **Phase 4** – Logging (clear missing branches)
4. **Phase 5** – Progress bar (single branch)
5. **Phase 3** – CLI (requires careful mocking)

---

## Template Structure for New Files

### Conditional test directory

The template uses `{% if fastapi_enabled %}test_app{% endif %}/` so that when `fastapi_enabled` is false, no `test_app` directory is created. This matches the conditional `app/` folder.

### Copier answers consistency

Ensure `default_copier_answers.yml` keeps:

- `fastapi_enabled: true`
- `include_health_endpoints: true`
- `python_package_command_line_name: test-project`

---

## Verification

After adding tests:

```bash
make update-instantiated-template-coverage
```

Then inspect `docs/development/testing.md` for the updated coverage value. Run:

```bash
uv run pytest tests/test_template/test_ci.py::test_instantiated_template_test_coverage -v
```

The coverage report (term-missing) is streamed during the run. For a quick local check, instantiate manually and run:

```bash
cd <instantiated_project>
make test-coverage-report
```

---

## Summary Table

| Module                      | Current    | Target   | New Tests     |
| --------------------------- | ---------- | -------- | ------------- |
| app/asgi.py                 | 0%         | 100%     | 4             |
| app/**init**.py             | 0%         | 100%     | (via asgi)    |
| app/controllers/\*          | 0%         | 100%     | 2             |
| app/exceptions/\*           | 0%         | 100%     | 3             |
| app/router.py               | 0%         | 100%     | 2             |
| app/utils/aiohttp_client.py | 0%         | 100%     | 8             |
| app/views/\*                | 0%         | 100%     | 3             |
| app/state/**init**.py       | 100%       | 100%     | —             |
| config.py                   | 0%         | 100%     | 1             |
| cli/register.py             | 33%        | 100%     | 5             |
| cli/main_cli.py             | 62%        | 100%     | 3             |
| utils/logging.py            | 77%        | 100%     | 4             |
| utils/progress_bar.py       | 98%        | 100%     | 1             |
| **TOTAL**                   | **55.78%** | **100%** | **~36 tests** |
