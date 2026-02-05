"""CLI error and warning message text helpers.

All functions return plain strings for use with error_panel(), warning_panel(),
or in raised exceptions (e.g. FileNotFoundError). No Rich types; no console.
"""

from pathlib import Path


def answers_file_not_found(path: Path | str) -> str:
    """Return message for missing answers file. For error_panel or FileNotFoundError.

    Args:
        path: Path to the missing answers file.

    Returns:
        Message string for error_panel.

    Examples:
        >>> answers_file_not_found("/path/to/answers.yml")
        'Answers file not found: /path/to/answers.yml'
    """
    return f"Answers file not found: {path}"


def schema_not_found() -> str:
    """Return message when copier.yml schema cannot be loaded. For error_panel.

    Returns:
        Message string for error_panel.
    """
    return "Could not load schema (copier.yml)."


def schema_not_found_skipping_validation() -> str:
    """Return message when schema load fails and validation is skipped. For warning_panel.

    Returns:
        Message string for warning_panel.
    """
    return "Could not load schema (copier.yml). Skipping validation."


def project_dir_not_found(path: Path | str) -> str:
    """Return message when project directory does not exist. For error_panel.

    Args:
        path: Path to the missing project directory.

    Returns:
        Message string for error_panel.
    """
    return f"Project directory does not exist: {path}"


def project_path_not_directory(path: Path | str) -> str:
    """Return message when project path is not a directory. For error_panel.

    Args:
        path: Path that is not a directory.

    Returns:
        Message string for error_panel.
    """
    return f"Project path is not a directory: {path}"


def output_path_not_file(path: Path | str) -> str:
    """Return message when output path is not a file. For error_panel.

    Args:
        path: Path that is not a file.

    Returns:
        Message string for error_panel.
    """
    return f"Output path is not a file: {path}"


def template_not_found(path: Path | str) -> str:
    """Return message when template file is missing. For error_panel.

    Args:
        path: Path to the missing template file.

    Returns:
        Message string for error_panel.
    """
    return f"Template file not found: {path}"


def template_path_not_file(path: Path | str) -> str:
    """Return message when template path is not a file. For error_panel.

    Args:
        path: Path that is not a file.

    Returns:
        Message string for error_panel.
    """
    return f"Template path is not a file: {path}"


def template_path_does_not_exist(path: Path | str) -> str:
    """Return message when template path does not exist. For error_panel.

    Args:
        path: Path that does not exist.

    Returns:
        Message string for error_panel.
    """
    return f"Template path does not exist: {path}"


def template_dir_not_found(path: Path | str, expected_hint: str) -> str:
    """Return message when command template directory is missing. For error_panel.

    Args:
        path: Path to the missing template directory.
        expected_hint: Hint about expected location.

    Returns:
        Message string for error_panel.
    """
    return f"Template directory not found: {path}\n{expected_hint}"


def invalid_conflict_mode(conflict: str) -> str:
    """Return message for invalid conflict mode. For error_panel.

    Args:
        conflict: The invalid conflict mode value.

    Returns:
        Message string for error_panel.
    """
    return f"Invalid conflict mode: {conflict}. Must be 'inline' or 'rej'."


def copier_answers_not_found_for_update(path: Path | str) -> str:
    """Return message when .copier-answers.yml is missing for update. For error_panel.

    Args:
        path: Path to the missing answers file.

    Returns:
        Message string for error_panel including hint about --answers.

    Examples:
        Output starts with "Copier answers file not found: <path>", followed by
        a blank line and hint lines about .copier-answers.yml and --answers.
    """
    return (
        f"Copier answers file not found: {path}\n\n"
        "The .copier-answers.yml file is required for updating projects.\n"
        "Make sure you're in a repoman-generated project directory,\n"
        "or specify the answers file with --answers."
    )


def copier_answers_not_found_with_hint(e: BaseException | str) -> str:
    """Return message when copier answers file cannot be found, with hint. For error_panel.

    Args:
        e: Exception or error message.

    Returns:
        Message string for error_panel including hint.
    """
    return (
        f"Could not find copier answers file: {e}\n\n"
        "Make sure you're in a repoman-generated project directory,\n"
        "or specify the answers file with --answers."
    )


def missing_python_package_import_name() -> str:
    """Return message when python_package_import_name is missing in answers. For error_panel.

    Returns:
        Message string for error_panel.
    """
    return (
        "Missing 'python_package_import_name' in answers file.\n"
        "This is required to determine where to create the command."
    )


def unknown_format(fmt: str, allowed: str = "table or json") -> str:
    """Return message for unsupported format. For error_panel.

    Args:
        fmt: The unsupported format value.
        allowed: Allowed formats to suggest. Defaults to "table or json".

    Returns:
        Message string for error_panel.
    """
    return f"Unknown format: {fmt}. Use {allowed}."


def invalid_yaml(e: BaseException | str) -> str:
    """Return message for invalid YAML. For error_panel.

    Args:
        e: Exception or error message from YAML parse.

    Returns:
        Message string for error_panel.
    """
    return f"Invalid YAML: {e}"


def file_exists_use_force(path: Path | str) -> str:
    """Return message when file exists and --force is needed. For warning_panel.

    Args:
        path: Path to the existing file.

    Returns:
        Message string for warning_panel.

    Examples:
        >>> file_exists_use_force("/path/config.yml")
        'File already exists: /path/config.yml\\nUse --force to overwrite.'
    """
    return f"File already exists: {path}\nUse --force to overwrite."


def output_dir_exists_use_force(path: Path | str) -> str:
    """Return message when output directory exists and --force is needed. For warning_panel.

    Args:
        path: Path to the existing output directory.

    Returns:
        Message string for warning_panel.
    """
    return f"Output directory {path} already exists. Use --force to overwrite."


def command_file_exists_use_force(path: Path | str) -> str:
    """Return message when command file exists and --force is needed. For warning_panel.

    Args:
        path: Path to the existing command file.

    Returns:
        Message string for warning_panel.
    """
    return f"Command file already exists: {path}\nUse --force to overwrite."


def test_file_exists_use_force(path: Path | str) -> str:
    """Return message when test file exists and --force is needed. For warning_panel.

    Args:
        path: Path to the existing test file.

    Returns:
        Message string for warning_panel.
    """
    return f"Test file already exists: {path}\nUse --force to overwrite."


def key_not_in_template(key: str) -> str:
    """Return message when key is not in template. For warning_panel.

    Args:
        key: The key that was not found.

    Returns:
        Message string for warning_panel.
    """
    return f"Key not in template: {key}"
