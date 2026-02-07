"""Validation of answers files against the template schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from repoman.config.loader import load_answers

if TYPE_CHECKING:
    from pathlib import Path
from repoman.copier import ValidationReport, load_prompt_schema, validate_answers


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
