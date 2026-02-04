"""Shared helpers for config subcommands: loading and validating answers/schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from repoman.cli.messages import answers_file_not_found

# Repoman package root (where copier.yml lives)
_REPOMAN_ROOT = Path(__file__).resolve().parent.parent.parent.parent


@dataclass
class ValidationReport:
    """Result of validating answers against the prompt schema."""

    valid: bool
    missing_keys: list[str]
    extra_keys: list[str]
    type_errors: list[str]


def load_answers(path: Path) -> dict:
    """Load answers from a YAML file.

    Args:
        path: Path to the answers file (e.g. .copier-answers.yml).

    Returns:
        Dictionary of answers (empty dict if file is empty).

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if not path.exists():
        raise FileNotFoundError(answers_file_not_found(path))
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_prompt_schema() -> dict:
    """Load prompt schema from repoman's copier.yml (keys and type info).

    Returns:
        Dict mapping prompt key -> schema entry (type, help, default, when, etc.).
        Only includes top-level keys that are not copier meta (do not start with _).
    """
    copier_path = _REPOMAN_ROOT / "copier.yml"
    if not copier_path.exists():
        return {}
    with open(copier_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: v for k, v in data.items() if isinstance(v, dict) and not k.startswith("_")}


def validate_answers(
    schema: dict,
    answers: dict,
    *,
    strict: bool = False,
) -> ValidationReport:
    """Validate answers against the prompt schema.

    Args:
        schema: From load_prompt_schema(); keys are expected prompt names.
        answers: User answers dict.
        strict: If True, extra keys in answers are reported and make the report invalid.

    Returns:
        ValidationReport with valid flag, missing_keys, extra_keys, type_errors.
    """
    expected_keys = set(schema)
    answer_keys = set(answers)

    missing_keys = sorted(expected_keys - answer_keys)
    extra_keys = sorted(answer_keys - expected_keys) if strict else []

    type_errors: list[str] = []
    for key in expected_keys & answer_keys:
        expected_type = schema[key].get("type", "str")
        value = answers[key]
        if expected_type == "bool" and not isinstance(value, bool):
            type_errors.append(f"{key}: expected bool, got {type(value).__name__}")
        elif expected_type == "int" and not isinstance(value, int):
            type_errors.append(f"{key}: expected int, got {type(value).__name__}")
        elif expected_type == "str" and value is not None and not isinstance(value, str):
            type_errors.append(f"{key}: expected str, got {type(value).__name__}")

    valid = len(missing_keys) == 0 and len(extra_keys) == 0 and len(type_errors) == 0
    return ValidationReport(
        valid=valid,
        missing_keys=missing_keys,
        extra_keys=extra_keys,
        type_errors=type_errors,
    )
