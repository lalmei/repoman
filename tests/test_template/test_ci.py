"""Integration tests for running CI commands on instantiated templates."""

from pathlib import Path
from typing import Any

from repoman.utils.logging import get_logger_console
from tests.ci_runner import CommandResult, parse_coverage_percent, run_make_command
from tests.template_testing import instantiate_template


def _read_text(path: Path) -> str:
    """Read a generated text file using UTF-8."""
    return path.read_text(encoding="utf-8")


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


def test_cli_only_template_omits_optional_feature_references(tmp_path: Path) -> None:
    """CLI-only projects should not render optional feature files or stale references."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "rag_enabled": False,
            "dataset_enabled": False,
        },
    )

    package_dir = project_dir / "src" / "test_project"
    assert not (package_dir / "app").exists()
    assert not (package_dir / "rag").exists()
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
    assert "## RAG pipeline" not in architecture
    assert "## Datasets" not in architecture
    assert "Enable FastAPI or RAG when generating the project" not in architecture

    layering = _read_text(project_dir / "config" / "cursor" / "rules" / "layering.mdc")
    assert "app, rag, datasets" not in layering
    assert "`config` and domain modules" in layering

    coverage = _read_text(project_dir / "config" / "coverage.ini")
    assert "main_template" not in coverage
    assert "RAG + datasets" not in coverage


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


def test_dataset_template_renders_dataset_files_only_when_enabled(tmp_path: Path) -> None:
    """Dataset-specific config artifacts should only exist in dataset-enabled projects."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"

    disabled_dir = instantiate_template(
        output_dir=tmp_path / "disabled",
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": False,
            "rag_enabled": False,
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
            "rag_enabled": False,
            "dataset_enabled": True,
        },
    )
    dataset_config = enabled_dir / "config" / "dataset_config.json"
    assert dataset_config.exists()
    assert '"modality": "image"' in _read_text(dataset_config)

    architecture = _read_text(enabled_dir / "docs" / "reference" / "architecture.md")
    assert "## Datasets" in architecture


def test_feature_enabled_template_keeps_optional_architecture_sections(tmp_path: Path) -> None:
    """FastAPI and RAG-enabled projects should still render their architecture docs."""
    answers_file = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    project_dir = instantiate_template(
        output_dir=tmp_path,
        project_name="test-project",
        answers_file=answers_file,
        copier_data={
            "fastapi_enabled": True,
            "rag_enabled": True,
            "dataset_enabled": True,
        },
    )

    architecture = _read_text(project_dir / "docs" / "reference" / "architecture.md")
    assert "## FastAPI app" in architecture
    assert "## RAG pipeline" in architecture
    assert "## Datasets" in architecture

    layering = _read_text(project_dir / "config" / "cursor" / "rules" / "layering.mdc")
    assert "`app`" in layering
    assert "`rag`" in layering
    assert "`datasets`" in layering


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
