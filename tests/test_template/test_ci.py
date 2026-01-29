"""Integration tests for running CI commands on instantiated templates."""

from tests.ci_runner import run_make_command


def test_instantiated_template_format_check(setup_template):
    """Test that make format-check runs successfully in instantiated template."""
    result = run_make_command(setup_template, "format-check")

    # Output is automatically visible in pytest output
    # Also capture it for assertions
    assert result.returncode == 0, (
        f"format-check failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_lint(setup_template):
    """Test that make lint runs successfully in instantiated template."""
    result = run_make_command(setup_template, "lint")

    assert result.returncode == 0, (
        f"lint failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_type_check(setup_template):
    """Test that make check-types runs successfully in instantiated template."""
    # Note: Verify exact command name matches template Makefile (may be check-types or type-check)
    result = run_make_command(setup_template, "check-types")

    assert result.returncode == 0, (
        f"type-check failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_instantiated_template_test(setup_template):
    """Test that make test runs successfully in instantiated template."""
    result = run_make_command(setup_template, "test")

    assert result.returncode == 0, (
        f"test failed with exit code {result.returncode}\n"
        f"Command: {result.command}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


def test_cleanup_removes_artifacts(instantiated_template):
    """Test that cleanup removes all artifacts after CI tests."""
    from tests.template_testing import cleanup_project_artifacts

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
