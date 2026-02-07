"""Template and copy operations: schema loading, validation, presets, and copier options."""

from __future__ import annotations

from repoman.copier.presets import PRESETS, build_copier_options, build_preset_data
from repoman.copier.schema import load_prompt_schema
from repoman.copier.validation import (
    ValidationReport,
    validate_answers,
    validate_project_name,
)

__all__ = [
    "PRESETS",
    "ValidationReport",
    "build_copier_options",
    "build_preset_data",
    "load_prompt_schema",
    "validate_answers",
    "validate_project_name",
]
