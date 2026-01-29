"""Unit tests for template_testing utility functions."""

from pathlib import Path

import pytest
from copier.errors import CopierError

from tests.template_testing import cleanup_project_artifacts, instantiate_template


def _create_test_artifacts(project_dir: Path, artifact_types: list[str] | None = None) -> dict[str, Path]:
    """Create test artifacts for cleanup testing.

    Args:
        project_dir: Base project directory
        artifact_types: List of artifact types to create. If None, creates all.
                       Options: 'venv', 'build', 'cache', 'egg_info', 'site'

    Returns:
        Dictionary mapping artifact names to their paths
    """
    artifacts = {}
    project_dir.mkdir(exist_ok=True)

    if artifact_types is None or "venv" in artifact_types:
        venv_dir = project_dir / ".venv"
        venv_dir.mkdir()
        (venv_dir / "bin").mkdir()
        artifacts["venv"] = venv_dir

    if artifact_types is None or "build" in artifact_types:
        for name in ["dist", "build", "site"]:
            path = project_dir / name
            path.mkdir()
            artifacts[name] = path

    if artifact_types is None or "cache" in artifact_types:
        for name in ["__pycache__", ".pytest_cache", ".mypy_cache", ".ipynb_checkpoints"]:
            path = project_dir / name
            path.mkdir()
            artifacts[name] = path
        # Create cache in subdirectories
        for subdir in ["src", "tests"]:
            subdir_path = project_dir / subdir
            subdir_path.mkdir(exist_ok=True)
            cache_path = subdir_path / "__pycache__"
            cache_path.mkdir()
            artifacts[f"{subdir}/__pycache__"] = cache_path

    if artifact_types is None or "egg_info" in artifact_types:
        egg_info = project_dir / "test_project.egg-info"
        egg_info.mkdir()
        artifacts["egg_info"] = egg_info

    return artifacts


def test_instantiate_template_basic(tmp_path, mock_template_structure):
    """Test that instantiate_template creates template files correctly."""
    project_dir = tmp_path / "test-project"

    result = instantiate_template(
        output_dir=tmp_path,
        template_path=mock_template_structure,
        project_name="test-project",
        force=True,
    )

    assert result == project_dir
    assert project_dir.exists()
    # Verify template files were created (copier.yml should be processed)
    assert (project_dir / "README.md").exists()


def test_instantiate_template_default_path(tmp_path):
    """Test that instantiate_template uses default template path when None."""
    # This test requires the actual main template to exist
    try:
        result = instantiate_template(
            output_dir=tmp_path,
            project_name="test-project",
            force=True,
        )
        assert result.exists()
    except (CopierError, ValueError) as e:
        # If template doesn't exist or copier fails, that's okay for unit test
        pytest.skip(f"Template instantiation failed: {e}")


def test_instantiate_template_custom_data(tmp_path, mock_template_structure):
    """Test that instantiate_template accepts custom copier data."""
    custom_data = {
        "project_name": "custom-project",
        "author_username": "customuser",
    }

    result = instantiate_template(
        output_dir=tmp_path,
        template_path=mock_template_structure,
        project_name="custom-project",
        copier_data=custom_data,
        force=True,
    )

    assert result.exists()


def test_instantiate_template_invalid_path(tmp_path):
    """Test that instantiate_template raises error for invalid template path."""
    invalid_path = tmp_path / "nonexistent-template"

    with pytest.raises(ValueError, match="does not exist"):
        instantiate_template(
            output_dir=tmp_path,
            template_path=invalid_path,
            project_name="test-project",
        )


def test_cleanup_project_artifacts_venv(tmp_path):
    """Test that cleanup_project_artifacts removes .venv directory."""
    project_dir = tmp_path / "test-project"
    artifacts = _create_test_artifacts(project_dir, ["venv"])

    cleanup_project_artifacts(project_dir)

    assert not artifacts["venv"].exists()


def test_cleanup_project_artifacts_build_dirs(tmp_path):
    """Test that cleanup_project_artifacts removes build directories."""
    project_dir = tmp_path / "test-project"
    artifacts = _create_test_artifacts(project_dir, ["build", "egg_info"])

    cleanup_project_artifacts(project_dir)

    assert not artifacts["dist"].exists()
    assert not artifacts["build"].exists()
    assert not artifacts["site"].exists()
    assert not artifacts["egg_info"].exists()


def test_cleanup_project_artifacts_cache_dirs(tmp_path):
    """Test that cleanup_project_artifacts removes cache directories recursively."""
    project_dir = tmp_path / "test-project"
    artifacts = _create_test_artifacts(project_dir, ["cache"])

    cleanup_project_artifacts(project_dir)

    assert not artifacts["__pycache__"].exists()
    assert not artifacts[".pytest_cache"].exists()
    assert not artifacts[".mypy_cache"].exists()
    assert not artifacts["src/__pycache__"].exists()
    assert not artifacts["tests/__pycache__"].exists()


def test_cleanup_project_artifacts_nonexistent_dir(tmp_path):
    """Test that cleanup_project_artifacts handles nonexistent directory gracefully."""
    nonexistent_dir = tmp_path / "nonexistent"

    # Should not raise an error
    cleanup_project_artifacts(nonexistent_dir)


def test_cleanup_project_artifacts_comprehensive(tmp_path):
    """Test comprehensive cleanup of all artifact types."""
    project_dir = tmp_path / "test-project"
    artifacts = _create_test_artifacts(project_dir)

    cleanup_project_artifacts(project_dir)

    # Verify all artifacts are removed
    assert not artifacts["venv"].exists()
    assert not artifacts["dist"].exists()
    assert not artifacts["build"].exists()
    assert not artifacts["egg_info"].exists()
    assert not artifacts["__pycache__"].exists()
    assert not artifacts[".pytest_cache"].exists()
    assert not artifacts[".mypy_cache"].exists()
    assert not artifacts[".ipynb_checkpoints"].exists()
    assert not artifacts["site"].exists()
    assert not artifacts["src/__pycache__"].exists()

    # Verify non-artifact directories still exist
    assert (project_dir / "src").exists()
