"""CLI messages package for repoman.

Centralizes user-facing error, warning, success, and dry-run messages.
Commands import helpers from this package for consistent styling and layout.

Modules:
    error: error_panel() — red panels for errors.
    warning: warning_panel() — yellow panels for warnings.
    success: project_created(), project_updated(), command_created() — green panels.
    dry_run: dry_run_create(), dry_run_update(), dry_run_command_add() — blue panels.
    layout: use_layout() and layout builders — multi-panel Layout for wide terminals.
    error_text: Pure string helpers (e.g. answers_file_not_found()) for panel content.
    capability: supports_unicode_markdown() — Unicode/terminal capability detection.
"""

from repoman.cli.messages.capability import supports_unicode_markdown
from repoman.cli.messages.dry_run import (
    dry_run_command_add,
    dry_run_create,
    dry_run_update,
)
from repoman.cli.messages.error import error_panel
from repoman.cli.messages.error_text import (
    answers_file_must_live_in_project,
    answers_file_not_found,
    command_file_exists_use_force,
    copier_answers_not_found_for_update,
    copier_answers_not_found_with_hint,
    copier_commit_missing_validate_warning,
    copier_update_missing_commit_remediation,
    file_exists_use_force,
    invalid_conflict_mode,
    invalid_yaml,
    is_cannot_obtain_old_template_references_message,
    key_not_in_template,
    missing_python_package_import_name,
    not_a_git_repository,
    output_dir_exists_use_force,
    output_path_not_file,
    project_dir_not_found,
    project_path_not_directory,
    repair_requires_commit,
    repair_requires_template_source,
    schema_not_found,
    schema_not_found_skipping_validation,
    template_dir_not_found,
    template_not_found,
    template_path_does_not_exist,
    template_path_not_file,
    test_file_exists_use_force,
    unknown_format,
    update_modes_mutually_exclusive,
)
from repoman.cli.messages.success import (
    command_created,
    format_next_steps,
    project_created,
    project_updated,
)
from repoman.cli.messages.warning import warning_panel

__all__ = [
    "answers_file_not_found",
    "answers_file_must_live_in_project",
    "command_created",
    "command_file_exists_use_force",
    "copier_answers_not_found_for_update",
    "copier_answers_not_found_with_hint",
    "copier_commit_missing_validate_warning",
    "copier_update_missing_commit_remediation",
    "dry_run_command_add",
    "dry_run_create",
    "dry_run_update",
    "error_panel",
    "file_exists_use_force",
    "format_next_steps",
    "invalid_conflict_mode",
    "invalid_yaml",
    "is_cannot_obtain_old_template_references_message",
    "key_not_in_template",
    "missing_python_package_import_name",
    "not_a_git_repository",
    "output_dir_exists_use_force",
    "output_path_not_file",
    "project_created",
    "project_dir_not_found",
    "project_path_not_directory",
    "project_updated",
    "repair_requires_commit",
    "repair_requires_template_source",
    "schema_not_found",
    "schema_not_found_skipping_validation",
    "supports_unicode_markdown",
    "template_dir_not_found",
    "template_not_found",
    "template_path_does_not_exist",
    "template_path_not_file",
    "test_file_exists_use_force",
    "unknown_format",
    "update_modes_mutually_exclusive",
    "warning_panel",
]
