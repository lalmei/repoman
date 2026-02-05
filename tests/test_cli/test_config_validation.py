"""Unit tests for validate_answers (Pydantic-based config validation)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from repoman.cli.commands.config.utils import load_answers, load_prompt_schema, validate_answers


def test_validate_answers_valid_complete() -> None:
    """Valid answers with complete schema returns valid report."""
    schema = {"name": {"type": "str"}, "count": {"type": "int"}}
    answers = {"name": "test", "count": 42}
    report = validate_answers(schema, answers)
    assert report.valid is True
    assert report.missing_keys == []
    assert report.extra_keys == []
    assert report.type_errors == []


def test_validate_answers_missing_key() -> None:
    """Missing required key returns invalid report with key in missing_keys."""
    schema = {"name": {"type": "str"}, "count": {"type": "int"}}
    answers = {"name": "test"}
    report = validate_answers(schema, answers)
    assert report.valid is False
    assert "count" in report.missing_keys
    assert report.extra_keys == []
    assert report.type_errors == []


def test_validate_answers_extra_key_strict() -> None:
    """Extra key with strict=True returns invalid report with key in extra_keys."""
    schema = {"name": {"type": "str"}}
    answers = {"name": "test", "extra": "x"}
    report = validate_answers(schema, answers, strict=True)
    assert report.valid is False
    assert report.missing_keys == []
    assert "extra" in report.extra_keys
    assert report.type_errors == []


def test_validate_answers_extra_key_not_strict() -> None:
    """Extra key with strict=False returns valid report (ignored)."""
    schema = {"name": {"type": "str"}}
    answers = {"name": "test", "extra": "x"}
    report = validate_answers(schema, answers, strict=False)
    assert report.valid is True
    assert report.missing_keys == []
    assert report.extra_keys == []
    assert report.type_errors == []


def test_validate_answers_wrong_type() -> None:
    """Wrong type (e.g. uncoercible string for bool) returns invalid report with type_errors."""
    schema = {"flag": {"type": "bool"}}
    answers = {"flag": "maybe"}  # Pydantic coerces "yes"/"true"/"1"; "maybe" is not valid
    report = validate_answers(schema, answers)
    assert report.valid is False
    assert report.missing_keys == []
    assert report.extra_keys == []
    assert len(report.type_errors) >= 1
    assert "flag" in report.type_errors[0]


def test_validate_answers_wrong_int_type() -> None:
    """String for int field returns type_errors."""
    schema = {"count": {"type": "int"}}
    answers = {"count": "five"}
    report = validate_answers(schema, answers)
    assert report.valid is False
    assert len(report.type_errors) >= 1
    assert "count" in report.type_errors[0]


def test_validate_answers_choices_valid() -> None:
    """Value in choices list is accepted."""
    schema = {"env": {"type": "str", "choices": ["a", "b", "c"]}}
    answers = {"env": "b"}
    report = validate_answers(schema, answers)
    assert report.valid is True


def test_validate_answers_choices_invalid() -> None:
    """Value not in choices returns type_errors."""
    schema = {"env": {"type": "str", "choices": ["a", "b", "c"]}}
    answers = {"env": "x"}
    report = validate_answers(schema, answers)
    assert report.valid is False
    assert len(report.type_errors) >= 1
    assert "env" in report.type_errors[0]


def test_validate_answers_choices_dict() -> None:
    """Choices as dict (label -> value) validates against values."""
    schema = {"license": {"type": "str", "choices": {"MIT License": "MIT", "ISC License": "ISC"}}}
    answers = {"license": "MIT"}
    report = validate_answers(schema, answers)
    assert report.valid is True


def test_validate_answers_empty_schema() -> None:
    """Empty schema with empty answers returns valid."""
    schema = {}
    answers = {}
    report = validate_answers(schema, answers)
    assert report.valid is True


def test_validate_answers_empty_schema_extra_strict() -> None:
    """Empty schema with extra answer and strict=True returns extra_keys."""
    schema = {}
    answers = {"x": 1}
    report = validate_answers(schema, answers, strict=True)
    assert report.valid is False
    assert "x" in report.extra_keys


def test_validate_answers_real_schema_and_fixture() -> None:
    """End-to-end: real copier.yml schema and default_copier_answers.yml validate successfully."""
    schema = load_prompt_schema()
    fixture_path = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    answers = load_answers(fixture_path)
    report = validate_answers(schema, answers)
    assert report.valid is True, f"Validation failed: {report}"


def test_validate_answers_schema_value_not_dict_skipped() -> None:
    """Schema key with non-dict value is skipped (line 63-64)."""
    schema = {"name": {"type": "str"}, "bad": "not a dict"}
    answers = {"name": "test"}
    report = validate_answers(schema, answers)
    # Only "name" is in model; "bad" is skipped so no crash, "name" is present
    assert report.valid is True
    assert report.missing_keys == []


def test_validate_answers_choices_empty() -> None:
    """Schema with empty choices (list or dict) uses str type (line 79)."""
    schema = {"x": {"type": "str", "choices": []}}
    answers = {"x": "any"}
    report = validate_answers(schema, answers)
    assert report.valid is True
    schema2 = {"y": {"choices": {}}}
    answers2 = {"y": "val"}
    report2 = validate_answers(schema2, answers2)
    assert report2.valid is True


def test_validate_answers_type_error_with_empty_loc() -> None:
    """ValidationError with empty loc appends msg only to type_errors (utils line 101)."""
    from pydantic import BaseModel

    class M(BaseModel):
        x: int

    try:
        M.model_validate({"x": "bad"})
    except ValidationError as e:
        # Override errors() to include one with empty loc so type_errors get msg only
        original_errors = e.errors()

        def errors_with_empty_loc() -> list:
            return [{"type": "value_error", "loc": (), "msg": "root error"}] + original_errors

        e.errors = errors_with_empty_loc
        mock_model = MagicMock()
        mock_model.model_validate.side_effect = e
        with patch("repoman.cli.commands.config.utils._schema_to_model", return_value=mock_model):
            report = validate_answers({"a": {"type": "str"}}, {"a": "x"})
        assert report.valid is False
        assert "root error" in report.type_errors
        return
    raise AssertionError("Expected ValidationError")
