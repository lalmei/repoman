"""Copier command for generating repositories from templates."""

import re
from pathlib import Path

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from typer import Argument, Context, Exit, Option, Typer

from copier import run_copy
from copier.errors import CopierError
from repoman.utils.logging import get_logger_console


def validate_project_name(project_name: str) -> bool:
    """Validate project name for security and safety.

    Args:
        project_name: The project name to validate

    Returns:
        True if the project name is valid, False otherwise

    Raises:
        ValueError: If the project name contains invalid characters or path traversal attempts
    """
    if not project_name or not project_name.strip():
        raise ValueError("Project name cannot be empty or whitespace only")

    # Check for path traversal patterns
    path_traversal_patterns = [
        r"\.\./",  # ../ (Unix path traversal)
        r"\.\.\\",  # ..\ (Windows path traversal)
        r"\.\.%2F",  # ..%2F (URL-encoded forward slash)
        r"\.\.%5C",  # ..%5C (URL-encoded backslash)
        r"\.\.%2f",  # ..%2f (lowercase URL-encoded forward slash)
        r"\.\.%5c",  # ..%5c (lowercase URL-encoded backslash)
        r"\.\.%252F",  # ..%252F (double URL-encoded forward slash)
        r"\.\.%255C",  # ..%255C (double URL-encoded backslash)
        r"\.\.∕",  # ..∕ (Unicode forward slash)
        r"\.\.﹨",  # ..﹨ (Unicode backslash)
        r"\.\.／",  # ..／ (Full-width forward slash)
        r"\.\.＼",  # ..＼ (Full-width backslash)
    ]

    for pattern in path_traversal_patterns:
        if re.search(pattern, project_name, re.IGNORECASE):
            raise ValueError(f"Project name contains path traversal pattern: {pattern}")

    # Check for other dangerous characters
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in project_name:
            raise ValueError(f"Project name contains invalid character: {char}")

    # Check for control characters
    if any(ord(char) < 32 for char in project_name):
        raise ValueError("Project name contains control characters")

    # Check for reserved names (Windows)
    reserved_names = (
        ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    )
    if project_name.upper() in reserved_names:
        raise ValueError(f"Project name is a reserved system name: {project_name}")

    return True


app = Typer(add_completion=True, no_args_is_help=True)


@app.callback(invoke_without_command=True, no_args_is_help=True)
def create_project(
    ctx: Context,
    project_name: str = Argument(..., help="Name of the project to create"),
    template_path: str | None = Option(
        None,
        "--template",
        "-t",
        help="Path to custom template (defaults to main template)",
    ),
    output_dir: str | None = Option(None, "--output", "-o", help="Output directory (defaults to current directory)"),
    answers_file: str | None = Option(None, "--answers", "-a", help="Path to answers file"),
    force: bool = Option(False, "--force", "-f", help="Force overwrite of existing files"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be created without actually creating"),
) -> None:
    """Create a new Python project using the repoman template."""
    logger, console = get_logger_console()

    # Validate project name for security
    try:
        validate_project_name(project_name)
    except ValueError as e:
        console.print(
            Panel(
                Text(f"Invalid project name: {e}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise Exit(1)

    # Determine template path
    if template_path is None:
        # Use the main template included with repoman
        current_file = Path(__file__)
        template_path = current_file.parent.parent / "main_template"
        logger.info(f"Using main template at {template_path}")

    # Determine output directory
    if output_dir is None:
        output_dir = Path.cwd() / project_name
    else:
        output_dir = Path(output_dir) / project_name

    # Check if output directory exists
    if output_dir.exists() and not force:
        console.print(
            Panel(
                Text(
                    f"Output directory {output_dir} already exists. Use --force to overwrite.",
                    style="yellow",
                ),
                title="Warning",
                border_style="yellow",
            )
        )
        raise Exit(1)

    # Prepare copier options
    copier_options = {
        "src_path": str(template_path),
        "dst_path": str(output_dir),
        "answers_file": answers_file,
        "overwrite": force,  # Make copier non-interactive by using force flag
        "quiet": True,  # Suppress interactive output
        "data": {
            "project_name": project_name,
            "repository_provider": "github",
            "ci": "github",
            "author_username": "user",
            "project_description": f"Project {project_name}",
            "copyright_license": "MIT",
            "insiders": False,
            "public_release": False,
        },
    }

    if dry_run:
        console.print(
            Panel(
                Text(
                    f"Would create project '{project_name}' in {output_dir}\n"
                    f"Using template: {template_path}\n"
                    f"Copier options: {copier_options}",
                    style="blue",
                ),
                title="Dry Run",
                border_style="blue",
            )
        )
        return

    # Create the project
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Creating project...", total=None)

            # Run copier
            run_copy(**copier_options)

            progress.update(task, description="Project created successfully!")

        # Success message
        console.print(
            Panel(
                Text(
                    f"Project '{project_name}' created successfully in {output_dir}\n\n"
                    f"Next steps:\n"
                    f"  cd {output_dir}\n"
                    f"  # Review and customize the generated project\n"
                    f"  # Initialize git repository\n"
                    f"  # Start developing!",
                    style="green",
                ),
                title="Success",
                border_style="green",
            )
        )

    except CopierError as e:
        console.print(
            Panel(
                Text(f"Error creating project: {e}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise Exit(1)
    except Exception as e:
        console.print(
            Panel(
                Text(f"Unexpected error: {e}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise Exit(1)
