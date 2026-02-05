"""Add subcommand for generator - creates new CLI commands from templates."""

import re
from pathlib import Path

import jinja2
import yaml
from jinja2 import Environment, FileSystemLoader
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, Exit, Option, Typer

from repoman.cli.messages import (
    answers_file_not_found,
    command_created,
    command_file_exists_use_force,
    copier_answers_not_found_with_hint,
    dry_run_command_add,
    error_panel,
    format_next_steps,
    missing_python_package_import_name,
    project_dir_not_found,
    template_dir_not_found,
    test_file_exists_use_force,
    warning_panel,
)
from repoman.extensions import CurrentYearExtension, GitExtension, SlugifyExtension
from repoman.utils.logging import get_logger_console

app = Typer(add_completion=True, help="Add a new CLI command to your project")


def validate_command_name(command_name: str) -> bool:
    """Validate command name for security and safety.

    Args:
        command_name: The command name to validate

    Returns:
        True if the command name is valid, False otherwise

    Raises:
        ValueError: If the command name contains invalid characters or path traversal attempts
    """
    if not command_name or not command_name.strip():
        raise ValueError("Command name cannot be empty or whitespace only")

    # Check for path traversal patterns
    path_traversal_patterns = [
        r"\.\./",  # ../ (Unix path traversal)
        r"\.\.\\",  # ..\ (Windows path traversal)
        r"\.\.%2F",  # ..%2F (URL-encoded forward slash)
        r"\.\.%5C",  # ..%5C (URL-encoded backslash)
    ]

    for pattern in path_traversal_patterns:
        if re.search(pattern, command_name, re.IGNORECASE):
            raise ValueError(f"Command name contains path traversal pattern: {pattern}")

    # Check for other dangerous characters
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in command_name:
            raise ValueError(f"Command name contains invalid character: {char}")

    # Check if it's a valid Python identifier
    if not command_name.isidentifier():
        raise ValueError(f"Command name '{command_name}' is not a valid Python identifier")

    # Check for reserved names (Windows)
    reserved_names = (
        ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    )
    if command_name.upper() in reserved_names:
        raise ValueError(f"Command name is a reserved system name: {command_name}")

    return True


def load_copier_answers(answers_file: Path) -> dict:
    """Load copier answers from YAML file.

    Args:
        answers_file: Path to the .copier-answers.yml file

    Returns:
        Dictionary containing the answers

    Raises:
        FileNotFoundError: If the answers file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    if not answers_file.exists():
        raise FileNotFoundError(answers_file_not_found(answers_file))

    with open(answers_file) as f:
        return yaml.safe_load(f) or {}


def detect_project_structure(project_dir: Path, python_package_import_name: str) -> tuple[Path, Path]:
    """Detect the project structure and return paths for commands and tests.

    Args:
        project_dir: Root directory of the project
        python_package_import_name: The Python package import name

    Returns:
        Tuple of (commands_dir, tests_dir)

    Raises:
        ValueError: If the project structure is not found
    """
    commands_dir = project_dir / "src" / python_package_import_name / "cli" / "commands"
    tests_dir = project_dir / "tests" / "test_cli"

    if not commands_dir.exists():
        # Try alternative structure
        raise ValueError(
            f"Could not find CLI commands directory. Expected: {commands_dir}\n"
            "Make sure you're in a repoman-generated project."
        )

    return commands_dir, tests_dir


@app.command()
def add(
    command_name: str = Argument(..., help="Name of the command to create"),
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
    """Add a new CLI command to your repoman-generated project.

    This command uses templates from repoman to generate:
    - A new command module in src/{package}/cli/commands/{command_name}/
    - A test file in tests/test_cli/test_{command_name}.py
    """
    logger, console = get_logger_console()

    # Validate command name
    try:
        validate_command_name(command_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from None

    # Determine project directory
    project_dir_path: Path = Path.cwd() if project_dir is None else Path(project_dir).resolve()

    if not project_dir_path.exists():
        console.print(error_panel(project_dir_not_found(project_dir_path), console=console))
        raise Exit(1) from None

    # Determine answers file path
    answers_file_path: Path = (
        project_dir_path / ".copier-answers.yml" if answers_file is None else Path(answers_file).resolve()
    )

    # Load copier answers
    try:
        answers = load_copier_answers(answers_file_path)
    except FileNotFoundError as e:
        console.print(error_panel(copier_answers_not_found_with_hint(e), console=console))
        raise Exit(1) from e
    except yaml.YAMLError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    # Extract required context
    python_package_import_name = answers.get("python_package_import_name")
    if not python_package_import_name:
        console.print(error_panel(missing_python_package_import_name(), console=console))
        raise Exit(1) from None

    python_package_command_line_name = answers.get("python_package_command_line_name", python_package_import_name)
    command_description = answers.get("command_description", f"{command_name} command")

    # Detect project structure
    try:
        commands_dir, tests_dir = detect_project_structure(project_dir_path, python_package_import_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    # Locate template directory
    # The template directory is literally named "{{command_name}}"
    current_file = Path(__file__)
    template_base = current_file.parent.parent.parent.parent / "extentions" / "command_template"
    template_dir = template_base / "{{command_name}}"

    if not template_dir.exists():
        console.print(
            error_panel(
                template_dir_not_found(
                    template_dir,
                    "Expected: extentions/command_template/{{command_name}}/",
                ),
                console=console,
            )
        )
        raise Exit(1)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        extensions=[CurrentYearExtension, GitExtension, SlugifyExtension],
        keep_trailing_newline=True,
        autoescape=True,  # Enable autoescape to prevent XSS vulnerabilities
    )

    # Prepare template context
    template_context = {
        "command_name": command_name,
        "python_package_import_name": python_package_import_name,
        "python_package_command_line_name": python_package_command_line_name,
        "command_description": command_description,
        **answers,  # Include all answers for potential use in templates
    }

    # Determine output paths
    command_output_dir = commands_dir / command_name
    command_output_file = command_output_dir / "__init__.py"
    test_output_file = tests_dir / f"test_{command_name}.py"

    # Check if files already exist
    if not force:
        if command_output_file.exists():
            console.print(warning_panel(command_file_exists_use_force(command_output_file), console=console))
            raise Exit(1) from None
        if test_output_file.exists():
            console.print(warning_panel(test_file_exists_use_force(test_output_file), console=console))
            raise Exit(1) from None

    # Render templates
    try:
        command_template = env.get_template("__init__.py.jinja")
        # The test template filename is literally "test_{{command_name}}.py.jinja"
        # We need to load it by its actual filename
        test_template_filename = "test_{{command_name}}.py.jinja"
        template_path = template_dir / test_template_filename
        if not template_path.exists():
            raise FileNotFoundError(f"Test template not found: {template_path}")  # noqa: TRY301 - Simple error, no need to abstract
        test_template = env.get_template(test_template_filename)

        rendered_command = command_template.render(**template_context)
        rendered_test = test_template.render(**template_context)
    except (FileNotFoundError, jinja2.TemplateNotFound, jinja2.TemplateError) as e:
        console.print(error_panel(str(e), console=console))
        logger.exception("Template rendering error")
        raise Exit(1) from e

    if dry_run:
        context_lines = (
            f"Template context:\n"
            f"  - command_name: {command_name}\n"
            f"  - python_package_import_name: {python_package_import_name}\n"
            f"  - python_package_command_line_name: {python_package_command_line_name}"
        )
        console.print(
            dry_run_command_add(
                command_name,
                command_output_file,
                test_output_file,
                context_lines,
                _console=console,
            )
        )
        return

    # Create files
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating command files...", total=None)

            # Create command directory and file
            command_output_dir.mkdir(parents=True, exist_ok=True)
            command_output_file.write_text(rendered_command, encoding="utf-8")

            # Create test directory and file
            tests_dir.mkdir(parents=True, exist_ok=True)
            test_output_file.write_text(rendered_test, encoding="utf-8")

            progress.update(task, description="Command created successfully!")

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
            f"  - {command_output_file.relative_to(project_dir_path)}\n"
            f"  - {test_output_file.relative_to(project_dir_path)}"
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

    except (OSError, PermissionError) as e:
        console.print(error_panel(str(e), console=console))
        logger.exception("File creation error")
        raise Exit(1) from e
