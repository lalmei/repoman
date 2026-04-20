"""Add subcommand for generator - creates new CLI commands from templates."""

import re
from pathlib import Path

import yaml
from typer import Argument, Exit, Option, Typer

from repoman.cli.messages import (
    copier_answers_not_found_with_hint,
    dry_run_command_add,
    error_panel,
    format_next_steps,
    missing_python_package_import_name,
    project_dir_not_found,
    warning_panel,
)
from repoman.cli.messages.error_text import (
    command_file_exists_use_force,
    test_file_exists_use_force,
)
from repoman.cli.messages.success import command_created
from repoman.config.loader import load_answers
from repoman.copier import (
    ExtensionLifecycleError,
    create_command_extension,
)
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="""Add a new CLI command to your project.

Examples:

    repoman generator add ingest --project-dir ./my-app
    repoman generator add my-cmd --dry-run --force
""",
)


def validate_command_name(command_name: str) -> bool:
    """Validate command name for security and safety."""
    if not command_name or not command_name.strip():
        raise ValueError("Command name cannot be empty or whitespace only")

    path_traversal_patterns = [r"\.\./", r"\.\.\\", r"\.\.%2F", r"\.\.%5C"]

    for pattern in path_traversal_patterns:
        if re.search(pattern, command_name, re.IGNORECASE):
            raise ValueError(f"Command name contains path traversal pattern: {pattern}")

    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in command_name:
            raise ValueError(f"Command name contains invalid character: {char}")

    if not command_name.isidentifier():
        raise ValueError(f"Command name '{command_name}' is not a valid Python identifier")

    reserved_names = (
        ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    )
    if command_name.upper() in reserved_names:
        raise ValueError(f"Command name is a reserved system name: {command_name}")

    return True


def detect_project_structure(project_dir: Path, python_package_import_name: str) -> tuple[Path, Path]:
    """Detect the project structure and return paths for commands and tests."""
    commands_dir = project_dir / "src" / python_package_import_name / "cli" / "commands"
    tests_dir = project_dir / "tests" / "test_cli"

    if not commands_dir.exists():
        raise ValueError(
            f"Could not find CLI commands directory. Expected: {commands_dir}\n"
            "Make sure you're in a repoman-generated project."
        )

    return commands_dir, tests_dir


@app.command()
def add(
    command_name: str = Argument(..., help="Name of the command instance to create"),
    project_dir: str | None = Option(
        None,
        "--project-dir",
        "-d",
        help="Project directory (defaults to current directory)",
    ),
    answers_file: str | None = Option(None, "--answers", "-a", help="Path to .copier-answers.yml file"),
    force: bool = Option(False, "--force", "-f", help="Overwrite existing files"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be created without creating"),
) -> None:
    """Add a new CLI command (see command help for examples)."""
    logger, console = get_logger_console()

    try:
        validate_command_name(command_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from None

    project_dir_path: Path = Path.cwd() if project_dir is None else Path(project_dir).resolve()

    if not project_dir_path.exists():
        console.print(error_panel(project_dir_not_found(project_dir_path), console=console))
        raise Exit(1) from None

    answers_file_path: Path = (
        project_dir_path / ".copier-answers.yml" if answers_file is None else Path(answers_file).resolve()
    )

    try:
        answers = load_answers(answers_file_path)
    except FileNotFoundError as e:
        console.print(error_panel(copier_answers_not_found_with_hint(e), console=console))
        raise Exit(1) from e
    except yaml.YAMLError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    python_package_import_name = answers.get("python_package_import_name")
    if not python_package_import_name:
        console.print(error_panel(missing_python_package_import_name(), console=console))
        raise Exit(1) from None

    try:
        _commands_dir, _tests_dir = detect_project_structure(project_dir_path, python_package_import_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    command_output_file = (
        project_dir_path / "src" / python_package_import_name / "cli" / "commands" / command_name / "__init__.py"
    )
    test_output_file = project_dir_path / "tests" / "test_cli" / f"test_{command_name}.py"

    if not force:
        if command_output_file.exists():
            console.print(warning_panel(command_file_exists_use_force(command_output_file), console=console))
            raise Exit(1) from None
        if test_output_file.exists():
            console.print(warning_panel(test_file_exists_use_force(test_output_file), console=console))
            raise Exit(1) from None

    try:
        _instance, copier_options, expected_command_file, expected_test_file = create_command_extension(
            project_dir=project_dir_path,
            base_answers_file=answers_file_path,
            answers=answers,
            command_name=command_name,
            force=force,
            dry_run=dry_run,
        )
    except ExtensionLifecycleError as e:
        console.print(error_panel(str(e), console=console))
        logger.exception("Extension generation failed")
        raise Exit(1) from e

    if dry_run:
        context_lines = (
            "Template context:\n"
            "  - kind: command\n"
            f"  - command_name: {command_name}\n"
            f"  - python_package_import_name: {python_package_import_name}\n"
            "  - copier_template: command\n"
            f"  - extension_answers_file: {copier_options['answers_file']}"
        )
        console.print(
            dry_run_command_add(
                command_name,
                expected_command_file,
                expected_test_file,
                context_lines,
                _console=console,
            )
        )
        return

    next_steps = [
        "Review and customize the generated command",
        "Implement the command functionality",
        "Write tests for your command",
        "The command will be automatically registered by the CLI",
    ]

    steps_text = format_next_steps(next_steps, console=console)

    summary_section = (
        f"Command '{command_name}' created successfully!\n\n"
        f"Created files:\n"
        f"  - {expected_command_file.relative_to(project_dir_path)}\n"
        f"  - {expected_test_file.relative_to(project_dir_path)}"
    )
    body_text = f"{summary_section}\n\nNext steps:\n{steps_text}"
    console.print(
        command_created(
            command_name,
            body_text,
            console=console,
            summary_section=summary_section,
            next_steps_section=steps_text,
        )
    )
