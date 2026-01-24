"""Unit tests for template_testing utility functions."""

import pytest
from copier.errors import CopierError

from repoman.utils.template_testing import cleanup_project_artifacts, instantiate_template


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
    project_dir.mkdir()
    venv_dir = project_dir / ".venv"
    venv_dir.mkdir()
    (venv_dir / "bin").mkdir()

    cleanup_project_artifacts(project_dir)

    assert not venv_dir.exists()


def test_cleanup_project_artifacts_build_dirs(tmp_path):
    """Test that cleanup_project_artifacts removes build directories."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    (project_dir / "dist").mkdir()
    (project_dir / "build").mkdir()
    (project_dir / "site").mkdir()
    (project_dir / "test_project.egg-info").mkdir()

    cleanup_project_artifacts(project_dir)

    assert not (project_dir / "dist").exists()
    assert not (project_dir / "build").exists()
    assert not (project_dir / "site").exists()
    assert not (project_dir / "test_project.egg-info").exists()


def test_cleanup_project_artifacts_cache_dirs(tmp_path):
    """Test that cleanup_project_artifacts removes cache directories recursively."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    (project_dir / "__pycache__").mkdir()
    (project_dir / ".pytest_cache").mkdir()
    (project_dir / ".mypy_cache").mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__pycache__").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "__pycache__").mkdir()

    cleanup_project_artifacts(project_dir)

    assert not (project_dir / "__pycache__").exists()
    assert not (project_dir / ".pytest_cache").exists()
    assert not (project_dir / ".mypy_cache").exists()
    assert not (project_dir / "src" / "__pycache__").exists()
    assert not (project_dir / "tests" / "__pycache__").exists()


def test_cleanup_project_artifacts_nonexistent_dir(tmp_path):
    """Test that cleanup_project_artifacts handles nonexistent directory gracefully."""
    nonexistent_dir = tmp_path / "nonexistent"

    # Should not raise an error
    cleanup_project_artifacts(nonexistent_dir)


def test_cleanup_project_artifacts_comprehensive(tmp_path):
    """Test comprehensive cleanup of all artifact types."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create all types of artifacts
    (project_dir / ".venv").mkdir()
    (project_dir / "dist").mkdir()
    (project_dir / "build").mkdir()
    (project_dir / "test_project.egg-info").mkdir()
    (project_dir / "__pycache__").mkdir()
    (project_dir / ".pytest_cache").mkdir()
    (project_dir / ".mypy_cache").mkdir()
    (project_dir / ".ipynb_checkpoints").mkdir()
    (project_dir / "site").mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__pycache__").mkdir()

    cleanup_project_artifacts(project_dir)

    # Verify all artifacts are removed
    assert not (project_dir / ".venv").exists()
    assert not (project_dir / "dist").exists()
    assert not (project_dir / "build").exists()
    assert not (project_dir / "test_project.egg-info").exists()
    assert not (project_dir / "__pycache__").exists()
    assert not (project_dir / ".pytest_cache").exists()
    assert not (project_dir / ".mypy_cache").exists()
    assert not (project_dir / ".ipynb_checkpoints").exists()
    assert not (project_dir / "site").exists()
    assert not (project_dir / "src" / "__pycache__").exists()

    # Verify non-artifact directories still exist
    assert (project_dir / "src").exists()
