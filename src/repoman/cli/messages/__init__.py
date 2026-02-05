"""CLI messages package for repoman."""

from repoman.cli.messages.capability import supports_unicode_markdown
from repoman.cli.messages.dry_run import (
    dry_run_command_add,
    dry_run_create,
    dry_run_update,
)
from repoman.cli.messages.error import error_panel
from repoman.cli.messages.error_text import (
    answers_file_not_found,
    command_file_exists_use_force,
    copier_answers_not_found_for_update,
    copier_answers_not_found_with_hint,
    file_exists_use_force,
    invalid_conflict_mode,
    invalid_yaml,
    key_not_in_template,
    missing_python_package_import_name,
    output_dir_exists_use_force,
    output_path_not_file,
    project_dir_not_found,
    project_path_not_directory,
    schema_not_found,
    schema_not_found_skipping_validation,
    template_dir_not_found,
    template_not_found,
    template_path_does_not_exist,
    template_path_not_file,
    test_file_exists_use_force,
    unknown_format,
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
    "command_created",
    "command_file_exists_use_force",
    "copier_answers_not_found_for_update",
    "copier_answers_not_found_with_hint",
    "dry_run_command_add",
    "dry_run_create",
    "dry_run_update",
    "error_panel",
    "file_exists_use_force",
    "format_next_steps",
    "invalid_conflict_mode",
    "invalid_yaml",
    "key_not_in_template",
    "missing_python_package_import_name",
    "output_dir_exists_use_force",
    "output_path_not_file",
    "project_created",
    "project_dir_not_found",
    "project_path_not_directory",
    "project_updated",
    "schema_not_found",
    "schema_not_found_skipping_validation",
    "supports_unicode_markdown",
    "template_dir_not_found",
    "template_not_found",
    "template_path_does_not_exist",
    "template_path_not_file",
    "test_file_exists_use_force",
    "unknown_format",
    "warning_panel",
]
