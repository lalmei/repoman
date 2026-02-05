"""Shared helpers for config subcommands: loading and validating answers/schema."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml
from pydantic import ConfigDict, ValidationError, create_model

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


def _schema_to_model(schema: dict, strict: bool) -> type:
    """Build a dynamic Pydantic model from the copier schema.

    Args:
        schema: From load_prompt_schema(); keys are prompt names, values have type, choices.
        strict: If True, extra keys are forbidden (ConfigDict extra='forbid').

    Returns:
        A Pydantic BaseModel subclass for validating answers.
    """
    extra = "forbid" if strict else "ignore"
    config = ConfigDict(extra=extra)
    fields: dict[str, tuple[type, ...]] = {}

    for key, meta in schema.items():
        if not isinstance(meta, dict):
            continue
        raw_type = meta.get("type", "str")
        choices = meta.get("choices")

        if choices is not None:
            if isinstance(choices, dict):
                allowed = tuple(choices.values())
            else:
                allowed = tuple(choices)
            if allowed:
                field_type: type = Literal[*allowed]
            else:
                field_type = str
        elif raw_type == "bool":
            field_type = bool
        elif raw_type == "int":
            field_type = int
        else:
            field_type = str

        fields[key] = (field_type, ...)

    return create_model(
        "AnswersModel",
        __config__=config,
        **fields,
    )


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
    model = _schema_to_model(schema, strict)

    try:
        model.model_validate(answers)
        return ValidationReport(
            valid=True,
            missing_keys=[],
            extra_keys=[],
            type_errors=[],
        )
    except ValidationError as e:
        missing_keys: list[str] = []
        extra_keys: list[str] = []
        type_errors: list[str] = []

        for err in e.errors():
            loc = err.get("loc", ())
            err_type = err.get("type", "")
            msg = err.get("msg", "")

            key = str(loc[0]) if len(loc) >= 1 else ""

            if err_type in ("missing", "value_error.missing"):
                if key and key not in missing_keys:
                    missing_keys.append(key)
            elif err_type in ("extra_forbidden", "value_error.extra"):
                if key and key not in extra_keys:
                    extra_keys.append(key)
            else:
                type_errors.append(f"{key}: {msg}" if key else msg)

        return ValidationReport(
            valid=False,
            missing_keys=sorted(missing_keys),
            extra_keys=sorted(extra_keys),
            type_errors=type_errors,
        )
