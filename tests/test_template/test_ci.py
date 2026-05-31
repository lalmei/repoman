"""Integration tests for running CI commands on instantiated templates."""

from pathlib import Path
from typing import Any

from repoman.utils.logging import get_logger_console
from tests.ci_runner import CommandResult, parse_coverage_percent, run_make_command
from tests.template_testing import instantiate_template


def _read_text(path: Path) -> str:
    """Read a generated text file using UTF-8."""
    return path.read_text(encoding="utf-8")


def _expected_repo_url(provider: str, namespace: str, name: str) -> str:
    """Return the normalized repository URL for a generated project."""
    host_by_provider = {
        "github": "github.com",
        "gitlab": "gitlab.com",
        "azure": "azure.com",
    }
    return f"https://{host_by_provider[provider]}/{namespace}/{name}"


def _expected_docs_url(provider: str, namespace: str, name: str) -> str:
    """Return the normalized docs URL for a generated project."""
    if provider == "github":
        return f"https://{namespace}.github.io/{name}"
    if provider == "gitlab":
        return f"https://{namespace}.gitlab.io/{name}"
    return _expected_repo_url(provider, namespace, name)


def test_instantiated_template_format_check(setup_template: Any) -> None:
    """Test that make format-check runs successfully in instantiated template."""
    result: CommandResult = run_make_command(setup_template, "format-check")

    # Output is automatically visible in pytest output
    # Also capture it for assertions
    assert result.returncode == 0, (
        f"format-check failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_lint(setup_template: Any) -> None:
    """Test that make lint runs successfully in instantiated template."""
    result: CommandResult = run_make_command(setup_template, "lint")

    assert result.returncode == 0, (
        f"lint failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_type_check(setup_template: Any) -> None:
    """Test that make check-types runs successfully in instantiated template."""
    # Note: Verify exact command name matches template Makefile (may be check-types or type-check)
    result: CommandResult = run_make_command(setup_template, "check-types")

    assert result.returncode == 0, (
        f"type-check failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_test(setup_template: Any) -> None:
    """Test that make test runs successfully in instantiated template."""
    result: CommandResult = run_make_command(setup_template, "test")

    assert result.returncode == 0, (
        f"test failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_test_coverage(setup_template: Any) -> None:
    """Test that make test-coverage-report runs successfully in instantiated template and expose coverage %."""
    result: CommandResult = run_make_command(setup_template, "test-coverage-report")

    assert result.returncode == 0, (
        f"test-coverage-report failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    coverage_pct = parse_coverage_percent(result.stdout)
    if coverage_pct is not None:
        logger, console = get_logger_console(__name__)
        console.print(f"[blue]Instantiated template line coverage:[/blue] [bold]{coverage_pct:.2f}%[/bold]")
        logger.info("Instantiated template line coverage: %s%%", coverage_pct)


def test_instantiated_template_notebook_executes(setup_template: Any) -> None:
    """Test that make check-notebooks runs successfully in instantiated template (python_notebooks: true)."""
    result: CommandResult = run_make_command(setup_template, "check-notebooks")

    assert result.returncode == 0, (
        f"check-notebooks failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_without_fastapi(tmp_path: Path) -> None:
    """When fastapi_enabled is false, no app folder is created and CI still passes."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={"fastapi_enabled": False},
    )
    src_package = project_dir / "src" / "test_project"
    assert not (src_package / "app").exists(), "app folder must not exist when fastapi_enabled is false"
    assert not (project_dir / "compose.yml").exists()
    assert not (project_dir / "Dockerfile.prod").exists()
    assert not (project_dir / ".env.prod.example").exists()

    # Setup and format so generated code passes format-check and lint (no fix)
    for make_target in ("setup", "format"):
        result = run_make_command(project_dir, make_target)
        assert result.returncode == 0, f"make {make_target} failed: {result.stderr}"

    for make_target in ("format-check", "lint", "check-types"):
        result = run_make_command(project_dir, make_target)
        assert result.returncode == 0, (
            f"make {make_target} failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def test_fastapi_template_renders_local_prod_stack_files(tmp_path: Path) -> None:
    """FastAPI projects should render local production compose assets."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={"fastapi_enabled": True, "dataset_enabled": False},
    )

    makefile = _read_text(project_dir / "Makefile")
    compose = _read_text(project_dir / "compose.yml")
    dockerfile = _read_text(project_dir / "Dockerfile.prod")
    env_example = _read_text(project_dir / ".env.prod.example")
    readme = _read_text(project_dir / "README.md")

    assert "include make_cmds/prod.mk" in makefile
    assert "docker compose --env-file" in _read_text(project_dir / "make_cmds" / "prod.mk")
    assert "OPENAI_API_KEY: ${OPENAI_API_KEY:-}" in compose
    assert "dockerfile: Dockerfile.prod" in compose
    assert 'CMD ["uv", "run", "uvicorn"' in dockerfile
    assert "RUN uv sync --no-dev --no-editable --no-default-groups" in dockerfile
    assert "OPENAI_API_KEY=replace-me" in env_example
    assert "make prod" in readme


def test_cli_only_template_omits_optional_feature_references(tmp_path: Path) -> None:
    """CLI-only projects should not render optional feature files or stale references."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "dataset_enabled": False,
        },
    )

    package_dir = project_dir / "src" / "test_project"
    assert not (package_dir / "app").exists()
    assert not (package_dir / "datasets").exists()
    assert not (project_dir / "config" / "dataset_config.json").exists()

    cli_init = _read_text(package_dir / "cli" / "__init__.py")
    assert "dataset command" not in cli_init
    assert "my_dataset" not in cli_init

    main_config = _read_text(package_dir / "config" / "main_config.py")
    assert "Template note" not in main_config
    assert "JsonConfigSettingsSource" not in main_config
    assert "json_file=" not in main_config

    architecture = _read_text(project_dir / "docs" / "reference" / "architecture.md")
    assert "## CLI" in architecture
    assert "## Configuration" in architecture
    assert "## FastAPI app" not in architecture
    assert "## Datasets" not in architecture

    layering = _read_text(project_dir / "config" / "cursor" / "rules" / "layering.mdc")
    assert "`config` and domain modules" in layering

    coverage = _read_text(project_dir / "config" / "coverage.ini")
    assert "main_template" not in coverage


def test_github_template_renders_docs_workflow(tmp_path: Path) -> None:
    """GitHub projects should render the Pages docs workflow."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
    )

    docs_workflow = _read_text(project_dir / ".github" / "workflows" / "docs.yml")
    assert "name: docs" in docs_workflow
    assert "actions/upload-pages-artifact@v3" in docs_workflow
    assert "actions/deploy-pages@v4" in docs_workflow
    assert "python scripts/generate_coverage_badge.py coverage.xml docs/coverage-badge.json" in docs_workflow


def test_template_badges_and_urls_render_for_github(tmp_path: Path) -> None:
    """GitHub projects should render provider-aware badges and normalized URLs."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
    )

    readme = _read_text(project_dir / "README.md")
    pyproject = _read_text(project_dir / "pyproject.toml")
    mkdocs = _read_text(project_dir / "config" / "mkdocs.yml")
    docs_url = _expected_docs_url("github", "testuser", "test-project")
    repo_url = _expected_repo_url("github", "testuser", "test-project")

    assert "[![ci](https://github.com/testuser/test-project/actions/workflows/ci.yml/badge.svg)]" in readme
    assert (
        f"[![documentation](https://img.shields.io/badge/docs-properdocs-708FCC.svg?style=flat)]({docs_url}/)" in readme
    )
    assert "[![pypi version](https://img.shields.io/pypi/v/test-project.svg)]" in readme
    assert "[![license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)" in readme
    assert "[![python](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg?style=flat)](#installation)" in readme
    assert (
        f"[![coverage](https://img.shields.io/endpoint?url={docs_url}/coverage-badge.json)]({docs_url}/coverage/)"
        in readme
    )

    assert f'Homepage = "{docs_url}"' in pyproject
    assert f'Documentation = "{docs_url}"' in pyproject
    assert f'Changelog = "{docs_url}/changelog"' in pyproject
    assert f'Repository = "{repo_url}"' in pyproject
    assert f'Issues = "{repo_url}/issues"' in pyproject
    assert f'Discussions = "{repo_url}/discussions"' in pyproject
    assert 'Funding = "https://github.com/sponsors/testuser"' in pyproject

    assert f'site_url: "{docs_url}"' in mkdocs
    assert f'repo_url: "{repo_url}"' in mkdocs
    assert 'site_dir: "site"' in mkdocs
    assert "icon: fontawesome/brands/github" in mkdocs
    assert "link: https://github.com/testuser" in mkdocs


def test_template_badges_and_urls_render_for_gitlab(tmp_path: Path) -> None:
    """GitLab projects should render docs and metadata without GitHub-only badges."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={"repository_provider": "gitlab", "ci": "gitlab.com"},
    )

    readme = _read_text(project_dir / "README.md")
    pyproject = _read_text(project_dir / "pyproject.toml")
    mkdocs = _read_text(project_dir / "config" / "mkdocs.yml")
    docs_url = _expected_docs_url("gitlab", "testuser", "test-project")
    repo_url = _expected_repo_url("gitlab", "testuser", "test-project")

    assert "[![ci]" not in readme
    assert (
        f"[![documentation](https://img.shields.io/badge/docs-properdocs-708FCC.svg?style=flat)]({docs_url}/)" in readme
    )
    assert "[![pypi version](https://img.shields.io/pypi/v/test-project.svg)]" in readme
    assert "[![license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)" in readme
    assert "[![python](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg?style=flat)](#installation)" in readme
    assert "coverage-badge.json" not in readme

    assert f'Homepage = "{docs_url}"' in pyproject
    assert f'Documentation = "{docs_url}"' in pyproject
    assert f'Changelog = "{docs_url}/changelog"' in pyproject
    assert f'Repository = "{repo_url}"' in pyproject
    assert f'Issues = "{repo_url}/-/issues"' in pyproject
    assert "Discussions =" not in pyproject
    assert "Funding =" not in pyproject

    assert f'site_url: "{docs_url}"' in mkdocs
    assert f'repo_url: "{repo_url}"' in mkdocs
    assert 'site_dir: ""' in mkdocs
    assert "icon: fontawesome/brands/gitlab" in mkdocs
    assert "link: https://gitlab.com/testuser" in mkdocs


def test_template_badges_and_urls_render_for_azure(tmp_path: Path) -> None:
    """Azure projects should keep provider-agnostic badges and repo-backed docs URLs."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "repository_provider": "azure",
            "ci": "azure.com",
            "deployments": [],
            "container_registry": "example.azurecr.io",
        },
    )

    readme = _read_text(project_dir / "README.md")
    pyproject = _read_text(project_dir / "pyproject.toml")
    mkdocs = _read_text(project_dir / "config" / "mkdocs.yml")
    docs_url = _expected_docs_url("azure", "testuser", "test-project")
    repo_url = _expected_repo_url("azure", "testuser", "test-project")

    assert "[![ci]" not in readme
    assert (
        f"[![documentation](https://img.shields.io/badge/docs-properdocs-708FCC.svg?style=flat)]({docs_url}/)" in readme
    )
    assert "[![pypi version](https://img.shields.io/pypi/v/test-project.svg)]" in readme
    assert "[![license](https://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)" in readme
    assert "[![python](https://img.shields.io/badge/python-%3E%3D3.11-blue.svg?style=flat)](#installation)" in readme
    assert "coverage-badge.json" not in readme

    assert f'Homepage = "{docs_url}"' in pyproject
    assert f'Documentation = "{docs_url}"' in pyproject
    assert f'Changelog = "{repo_url}"' in pyproject
    assert f'Repository = "{repo_url}"' in pyproject
    assert f'Issues = "{repo_url}"' in pyproject
    assert "Discussions =" not in pyproject
    assert "Funding =" not in pyproject

    assert f'site_url: "{docs_url}"' in mkdocs
    assert f'repo_url: "{repo_url}"' in mkdocs
    assert 'site_dir: ""' in mkdocs
    assert "icon: fontawesome/brands/azure" in mkdocs
    assert "link: https://azure.com/testuser" in mkdocs


def test_docs_only_template_omits_python_and_coverage_badges(tmp_path: Path) -> None:
    """Docs-only projects should not render Python or coverage badges."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={"docs_only": True},
    )

    readme = _read_text(project_dir / "README.md")

    assert "[![documentation]" in readme
    assert "[![license]" in readme
    assert "[![python]" not in readme
    assert "[![coverage]" not in readme


def test_private_template_omits_public_endpoint_badges(tmp_path: Path) -> None:
    """Private Insiders projects should not render public PyPI or coverage badges."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={"insiders": True, "public_release": False},
    )

    readme = _read_text(project_dir / "README.md")
    docs_url = _expected_docs_url("github", "testuser", "test-project")

    assert "[![documentation]" in readme
    assert "[![license]" in readme
    assert "[![python]" in readme
    assert "[![pypi version]" not in readme
    assert "[![coverage]" not in readme
    assert f"See Insiders [explanation]({docs_url}/insiders/)" in readme


def test_template_drops_python_310_from_ci_and_metadata(tmp_path: Path) -> None:
    """Generated projects should target Python 3.11+ in CI and packaging metadata."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
    )

    github_ci = _read_text(project_dir / ".github" / "workflows" / "ci.yml")
    pyproject = _read_text(project_dir / "pyproject.toml")

    assert '"3.10"' not in github_ci
    assert 'requires-python = ">=3.11"' in pyproject
    assert "Programming Language :: Python :: 3.10" not in pyproject


def test_dataset_template_renders_dataset_files_only_when_enabled(tmp_path: Path) -> None:
    """Dataset-specific config artifacts should only exist in dataset-enabled projects."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"

    disabled_dir = instantiate_template(
        output_dir=tmp_path / "disabled",
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "dataset_enabled": False,
        },
    )
    assert not (disabled_dir / "config" / "dataset_config.json").exists()

    enabled_dir = instantiate_template(
        output_dir=tmp_path / "enabled",
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "dataset_enabled": True,
            "dataset_modality_image": True,
            "dataset_modality_text": True,
            "dataset_modality_tabular": True,
            "dataset_modality_mesh": True,
        },
    )
    dataset_config = enabled_dir / "config" / "dataset_config.json"
    assert dataset_config.exists()
    assert '"modality": "image"' in _read_text(dataset_config)

    architecture = _read_text(enabled_dir / "docs" / "reference" / "architecture.md")
    assert "## Datasets" in architecture


def test_feature_enabled_template_keeps_optional_architecture_sections(tmp_path: Path) -> None:
    """FastAPI and dataset-enabled projects should still render their architecture docs."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": True,
            "dataset_enabled": True,
            "dataset_modality_image": True,
            "dataset_modality_text": True,
            "dataset_modality_tabular": True,
            "dataset_modality_mesh": True,
        },
    )

    architecture = _read_text(project_dir / "docs" / "reference" / "architecture.md")
    assert "## FastAPI app" in architecture
    assert "## Datasets" in architecture

    layering = _read_text(project_dir / "config" / "cursor" / "rules" / "layering.mdc")
    assert "`app`" in layering
    assert "`datasets`" in layering


def test_dataset_mesh_only_omits_optional_dl_dependencies(tmp_path: Path) -> None:
    """Mesh-only dataset selection should not add torchvision or pandas to the dl group."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path / "mesh-only",
        project_name="mesh-only",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "dataset_enabled": True,
            "dataset_modality_image": False,
            "dataset_modality_text": False,
            "dataset_modality_tabular": False,
            "dataset_modality_mesh": True,
        },
    )
    pyproject = _read_text(project_dir / "pyproject.toml")
    assert "torchvision" not in pyproject
    assert "pandas" not in pyproject
    assert "torch>=" in pyproject


def test_cleanup_removes_artifacts(instantiated_template: Any) -> None:
    """Test that cleanup removes all artifacts after CI tests."""
    from tests.template_testing import cleanup_project_artifacts  # noqa: PLC0415

    # Create some artifacts (exist_ok in case e.g. copier task already created .venv)
    (instantiated_template / ".venv").mkdir(exist_ok=True)
    (instantiated_template / "dist").mkdir(exist_ok=True)
    (instantiated_template / "__pycache__").mkdir(exist_ok=True)
    (instantiated_template / ".pytest_cache").mkdir(exist_ok=True)
    (instantiated_template / "site").mkdir(exist_ok=True)

    # Run cleanup
    cleanup_project_artifacts(instantiated_template)

    # Verify artifacts are removed
    assert not (instantiated_template / ".venv").exists(), ".venv should be removed"
    assert not (instantiated_template / "dist").exists(), "dist should be removed"
    assert not (instantiated_template / "__pycache__").exists(), "__pycache__ should be removed"
    assert not (instantiated_template / ".pytest_cache").exists(), ".pytest_cache should be removed"
    assert not (instantiated_template / "site").exists(), "site should be removed"
