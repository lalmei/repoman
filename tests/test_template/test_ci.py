"""Integration tests for running CI commands on instantiated templates."""

from pathlib import Path
from typing import Any

from repoman.utils.logging import get_logger_console
from tests.ci_runner import CommandResult, parse_coverage_percent, run_make_command
from tests.template_testing import instantiate_template


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

    # Setup and format/fix so generated code passes format-check and lint
    for make_target in ("setup", "format", "fix"):
        result = run_make_command(project_dir, make_target)
        assert result.returncode == 0, f"make {make_target} failed: {result.stderr}"

    for make_target in ("format-check", "lint", "check-types"):
        result = run_make_command(project_dir, make_target)
        assert result.returncode == 0, (
            f"make {make_target} failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def test_cleanup_removes_artifacts(instantiated_template: Any) -> None:
    """Test that cleanup removes all artifacts after CI tests."""
    from tests.template_testing import cleanup_project_artifacts  # noqa: PLC0415

    # Create some artifacts
    (instantiated_template / ".venv").mkdir()
    (instantiated_template / "dist").mkdir()
    (instantiated_template / "__pycache__").mkdir()
    (instantiated_template / ".pytest_cache").mkdir()
    (instantiated_template / "site").mkdir()

    # Run cleanup
    cleanup_project_artifacts(instantiated_template)

    # Verify artifacts are removed
    assert not (instantiated_template / ".venv").exists(), ".venv should be removed"
    assert not (instantiated_template / "dist").exists(), "dist should be removed"
    assert not (instantiated_template / "__pycache__").exists(), "__pycache__ should be removed"
    assert not (instantiated_template / ".pytest_cache").exists(), ".pytest_cache should be removed"
    assert not (instantiated_template / "site").exists(), "site should be removed"
