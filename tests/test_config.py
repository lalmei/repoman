"""Unit tests for repoman.config module."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from repoman.config import load_answers, validate_answers_file


def test_load_answers_file_exists(tmp_path: Path) -> None:
    """load_answers returns dict from existing YAML file."""
    p = tmp_path / "answers.yml"
    p.write_text("foo: bar\ncount: 42\n")
    data = load_answers(p)
    assert data == {"foo": "bar", "count": 42}


def test_load_answers_empty_file(tmp_path: Path) -> None:
    """load_answers returns empty dict for empty file."""
    p = tmp_path / "empty.yml"
    p.write_text("")
    data = load_answers(p)
    assert data == {}


def test_load_answers_file_not_found() -> None:
    """load_answers raises FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError, match="Answers file not found"):
        load_answers(Path("/nonexistent/answers.yml"))


def test_load_answers_invalid_yaml(tmp_path: Path) -> None:
    """load_answers raises yaml.YAMLError for invalid YAML."""
    p = tmp_path / "bad.yml"
    p.write_text("foo: [unclosed\n")
    with pytest.raises(yaml.YAMLError):
        load_answers(p)


def test_validate_answers_file_valid_uses_fixture() -> None:
    """validate_answers_file returns valid report for fixture file with full answers."""
    fixture_path = Path(__file__).parent / "fixtures" / "default_copier_answers.yml"
    report = validate_answers_file(fixture_path)
    assert report.valid is True, f"Expected valid: {report}"


def test_validate_answers_file_missing_keys(tmp_path: Path) -> None:
    """validate_answers_file returns invalid report when required keys missing."""
    p = tmp_path / "answers.yml"
    p.write_text("{}")
    report = validate_answers_file(p)
    assert report.valid is False
    assert len(report.missing_keys) >= 1


def test_validate_answers_file_nonexistent() -> None:
    """validate_answers_file raises FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError, match="Answers file not found"):
        validate_answers_file(Path("/nonexistent/answers.yml"))
