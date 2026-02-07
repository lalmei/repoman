"""Project configuration: loading and validating answers files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path
from pydantic import BaseModel

from repoman.copier import ValidationReport, load_prompt_schema, validate_answers


class Config(BaseModel):
    """Configuration model for repoman (log format, etc.)."""

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


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
        raise FileNotFoundError(f"Answers file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def validate_answers_file(
    path: Path,
    template_path: Path | None = None,
    *,
    strict: bool = False,
) -> ValidationReport:
    """Load an answers file and validate it against the template schema.

    Args:
        path: Path to the answers file (e.g. .copier-answers.yml).
        template_path: Directory containing copier.yml for schema. If None, use repoman default.
        strict: If True, extra keys in answers are reported and make the report invalid.

    Returns:
        ValidationReport with valid flag, missing_keys, extra_keys, type_errors.
    """
    answers = load_answers(path)
    schema = load_prompt_schema(template_path)
    return validate_answers(schema, answers, strict=strict)


__all__ = [
    "Config",
    "load_answers",
    "validate_answers_file",
]
