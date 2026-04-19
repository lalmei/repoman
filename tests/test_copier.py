"""Unit tests for repoman.copier module."""

from __future__ import annotations

from pathlib import Path

import pytest

from repoman.copier import (
    PRESETS,
    build_copier_options,
    build_preset_data,
    load_prompt_schema,
    validate_project_name,
)


def test_validate_project_name_accepts_valid() -> None:
    """Valid project names pass."""
    validate_project_name("my-project")
    validate_project_name("my_project")
    validate_project_name("a")


def test_validate_project_name_empty_raises() -> None:
    """Empty or whitespace-only name raises ValueError."""
    with pytest.raises(ValueError, match="empty or whitespace"):
        validate_project_name("")
    with pytest.raises(ValueError, match="empty or whitespace"):
        validate_project_name("   ")


def test_validate_project_name_path_traversal_raises() -> None:
    """Path traversal patterns raise ValueError."""
    with pytest.raises(ValueError, match="path traversal"):
        validate_project_name("../foo")
    with pytest.raises(ValueError, match="path traversal"):
        validate_project_name("foo/../bar")


def test_validate_project_name_dangerous_chars_raises() -> None:
    """Dangerous characters raise ValueError."""
    with pytest.raises(ValueError, match="invalid character"):
        validate_project_name("foo/bar")
    with pytest.raises(ValueError, match="invalid character"):
        validate_project_name("a*b")


def test_validate_project_name_reserved_raises() -> None:
    """Reserved Windows names raise ValueError."""
    with pytest.raises(ValueError, match="reserved"):
        validate_project_name("CON")
    with pytest.raises(ValueError, match="reserved"):
        validate_project_name("nul")


def test_build_preset_data_includes_base_and_overrides() -> None:
    """build_preset_data merges base template with preset overrides."""
    data = build_preset_data("cli", "my-cli")
    assert "project_name" in data
    assert data.get("fastapi_enabled") is False
    assert data.get("dataset_enabled") is False
    assert "python_package_command_line_name" in data
    assert data["python_package_command_line_name"] == "my-cli"


def test_build_preset_data_fastapi_preset() -> None:
    """FastAPI preset enables FastAPI without dataset extras."""
    data = build_preset_data("fastapi", "my-api")
    assert data.get("fastapi_enabled") is True
    assert data.get("dataset_enabled") is False


def test_build_copier_options_without_data() -> None:
    """build_copier_options without data returns only src_path and dst_path."""
    opts = build_copier_options("p1", Path("/out"), Path("/tpl"), None)
    assert opts["src_path"] == "/tpl"
    assert opts["dst_path"] == "/out/p1"
    assert "data" not in opts


def test_build_copier_options_with_data() -> None:
    """build_copier_options with data sets project_name and includes data and flags."""
    data = {"foo": "bar"}
    opts = build_copier_options("myproj", Path("/out"), Path("/tpl"), data)
    assert opts["src_path"] == "/tpl"
    assert opts["dst_path"] == "/out/myproj"
    assert opts["data"]["project_name"] == "myproj"
    assert opts["data"]["foo"] == "bar"
    assert opts["answers_file"] == ".copier-answers.yml"
    assert opts["overwrite"] is True
    assert opts["unsafe"] is True


def test_build_copier_options_does_not_mutate_input_data() -> None:
    """Passed-in data dict is not mutated (copy is used)."""
    data = {"a": 1}
    build_copier_options("p", Path("/o"), Path("/t"), data)
    assert "project_name" not in data
    assert data == {"a": 1}


def test_load_prompt_schema_default_returns_dict() -> None:
    """load_prompt_schema() with no args returns dict from repoman copier.yml."""
    schema = load_prompt_schema()
    assert isinstance(schema, dict)
    # Repoman template has many keys; meta keys start with _
    for k in schema:
        assert not k.startswith("_")


def test_presets_keys() -> None:
    """PRESETS contains expected preset names."""
    assert set(PRESETS.keys()) == {"cli", "docs_only", "library", "fastapi"}
