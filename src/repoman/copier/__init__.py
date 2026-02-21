"""Template and copy operations: schema loading, validation, presets, and copier options."""

from __future__ import annotations

from repoman.copier.presets import PRESETS, build_copier_options, build_preset_data
from repoman.copier.schema import load_prompt_schema
from repoman.copier.extension_lifecycle import (
    ExtensionLifecycleError,
    ExtensionSyncResult,
    create_command_extension,
    load_manifest,
    sync_extensions,
)
from repoman.copier.validation import (
    ValidationReport,
    validate_answers,
    validate_project_name,
)

__all__ = [
    "PRESETS",
    "ExtensionLifecycleError",
    "ExtensionSyncResult",
    "ValidationReport",
    "build_copier_options",
    "build_preset_data",
    "create_command_extension",
    "load_manifest",
    "load_prompt_schema",
    "sync_extensions",
    "validate_answers",
    "validate_project_name",
]
