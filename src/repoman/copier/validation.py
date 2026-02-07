"""Schema and project-name validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, ValidationError, create_model

# ASCII control characters: ord < 32 (SPACE)
_CONTROL_CHAR_THRESHOLD = 32


@dataclass
class ValidationReport:
    """Result of validating answers against the prompt schema."""

    valid: bool
    missing_keys: list[str]
    extra_keys: list[str]
    type_errors: list[str]


def _schema_to_model(schema: dict, *, strict: bool) -> type[BaseModel]:
    """Build a dynamic Pydantic model from the copier schema.

    Args:
        schema: From load_prompt_schema(); keys are prompt names, values have type, choices.
        strict: If True, extra keys are forbidden (ConfigDict extra='forbid').

    Returns:
        A Pydantic BaseModel subclass for validating answers.
    """
    extra: Literal["forbid", "ignore"] = "forbid" if strict else "ignore"
    config = ConfigDict(extra=extra)
    fields: dict[str, Any] = {}

    for key, meta in schema.items():
        if not isinstance(meta, dict):
            continue
        raw_type = meta.get("type", "str")
        choices = meta.get("choices")
        field_type: type

        if choices is not None:
            allowed = tuple(choices.values()) if isinstance(choices, dict) else tuple(choices)
            if allowed:
                # Literal[*allowed] requires Python 3.11+. Use dynamic Enum for 3.9 compat.
                choices_enum = Enum(  # type: ignore[misc]
                    f"Choices_{len(fields)}",
                    [(f"v{i}", v) for i, v in enumerate(allowed)],
                )
                field_type = choices_enum
            else:
                field_type = str
        elif raw_type == "bool":
            field_type = bool
        elif raw_type == "int":
            field_type = int
        else:
            field_type = str

        fields[key] = (field_type, ...)

    return create_model("AnswersModel", __config__=config, **fields)


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
    model = _schema_to_model(schema, strict=strict)

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


def validate_project_name(project_name: str) -> bool:
    """Validate project name for security and safety.

    Raises:
        ValueError: If the project name is invalid.
    """
    if not project_name or not project_name.strip():
        raise ValueError("Project name cannot be empty or whitespace only")

    path_traversal_patterns = [
        r"\.\./",
        r"\.\.\\",
        r"\.\.%2F",
        r"\.\.%5C",
        r"\.\.%2f",
        r"\.\.%5c",
        r"\.\.%252F",
        r"\.\.%255C",
        r"\.\.\u2215",
        r"\.\.\uFE68",
        r"\.\.\uFF0F",
        r"\.\.\uFF3C",
    ]
    for pattern in path_traversal_patterns:
        if re.search(pattern, project_name, re.IGNORECASE):
            raise ValueError(f"Project name contains path traversal pattern: {pattern}")

    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in project_name:
            raise ValueError(f"Project name contains invalid character: {char}")

    if any(ord(c) < _CONTROL_CHAR_THRESHOLD for c in project_name):
        raise ValueError("Project name contains control characters")

    reserved = ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    if project_name.upper() in reserved:
        raise ValueError(f"Project name is a reserved system name: {project_name}")

    return True
