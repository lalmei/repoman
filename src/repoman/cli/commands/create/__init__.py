"""Create command for generating repositories from templates."""

import re
from pathlib import Path
from typing import Annotated

import yaml
from copier import run_copy
from copier.errors import CopierError
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, Context, Exit, Option, Typer

from repoman.cli.messages import (
    answers_file_not_found,
    dry_run_create,
    error_panel,
    format_next_steps,
    output_dir_exists_use_force,
    project_created,
    warning_panel,
)
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
        r"\.\.\u2215",  # ..\u2215 (Unicode division slash, looks like /)
        r"\.\.\uFE68",  # ..\uFE68 (Unicode small reverse solidus, looks like \)
        r"\.\.\uFF0F",  # ..\uFF0F (Full-width solidus, looks like /)
        r"\.\.\uFF3C",  # ..\uFF3C (Full-width reverse solidus, looks like \)
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
    control_char_threshold = 32
    if any(ord(char) < control_char_threshold for char in project_name):
        raise ValueError("Project name contains control characters")

    # Check for reserved names (Windows)
    reserved_names = (
        ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    )
    if project_name.upper() in reserved_names:
        raise ValueError(f"Project name is a reserved system name: {project_name}")

    return True


app = Typer(add_completion=True)


@app.callback(invoke_without_command=True)
def create(
    ctx: Context,
    project_name: str = Argument(..., help="Name of the project to create"),
    template_path: Annotated[
        str | None,
        Option(
            "--template",
            "-t",
            help="Path to custom template (defaults to main template)",
        ),
    ] = None,
    output_dir: Annotated[
        str | None,
        Option("--output", "-o", help="Output directory (defaults to current directory)"),
    ] = None,
    answers_file: Annotated[
        Path | None,
        Option("--answers", "-a", help="Path to answers file"),
    ] = None,
    force: Annotated[
        bool,
        Option("--force", "-f", help="Force overwrite of existing files"),
    ] = False,
    dry_run: Annotated[
        bool,
        Option("--dry-run", help="Show what would be created without actually creating"),
    ] = False,
) -> None:
    """Create a new Python project using the repoman template."""
    logger, console = get_logger_console()

    # Validate project name for security
    try:
        validate_project_name(project_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from None

    # Determine template path
    template_path_obj: Path
    if template_path is None:
        # Use the main template included with repoman
        current_file = Path(__file__)
        template_path_obj = current_file.parent.parent.parent.parent
        logger.info(f"Using main template at {template_path_obj}")
    else:
        template_path_obj = Path(template_path)

    # Determine output directory
    output_dir_obj: Path = Path.cwd() / project_name if output_dir is None else Path(output_dir) / project_name

    # Check if output directory exists
    if output_dir_obj.exists() and not force:
        console.print(warning_panel(output_dir_exists_use_force(output_dir_obj), console=console))
        raise Exit(1) from None
    if answers_file is not None:
        answers_path = Path(answers_file).resolve()
        if not answers_path.exists():
            console.print(error_panel(answers_file_not_found(answers_path), console=console))
            raise Exit(1) from None
        console.print(f"Using answers file: {answers_path}")
        with open(answers_path) as f:
            answers_data = yaml.safe_load(f) or {}
        # CLI project_name overrides the answers file so the created project name matches
        answers_data["project_name"] = project_name
        # Copier expects answers_file relative to dst_path (project root). We pass the
        # loaded content as data; Copier will write answers to dst_path/.copier-answers.yml
        copier_options = {
            "src_path": str(template_path_obj),
            "dst_path": str(output_dir_obj),
            "data": answers_data,
            "answers_file": ".copier-answers.yml",
            "overwrite": True,
            "defaults": True,
            "quiet": False,
            "unsafe": True,
        }
    else:
        # Prepare copier options
        copier_options = {
            "src_path": str(template_path_obj),
            "dst_path": str(output_dir_obj),
        }

    # Prepare next steps (used in both dry-run and success messages)
    next_steps = [
        f"cd {output_dir_obj}",
        "Review and customize the generated project",
        "Initialize git repository",
        "Start developing!",
    ]

    steps_text = format_next_steps(next_steps, console=console)

    if dry_run or ctx.obj.get("dry_run", True):
        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}
        console.print(
            dry_run_create(
                project_name,
                output_dir_obj,
                template_path_obj,
                copier_options_serializable,
                steps_text,
                _console=console,
            )
        )
        return

    # Create the project
    try:
        if answers_file is not None:
            # Non-interactive: safe to use Progress (no Copier prompts)
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating project...", total=None)

                # Run copier
                run_copy(**copier_options)  # type: ignore[arg-type]  # copier accepts dict with mixed types

                progress.update(task, description="Project created successfully!")
        else:
            # Interactive: skip Progress to avoid stdin/stdout conflict with Copier prompts
            console.print("Creating project...")
            run_copy(**copier_options)  # type: ignore[arg-type]  # copier accepts dict with mixed types

        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}
        console.print(
            project_created(
                project_name,
                output_dir_obj,
                copier_options_serializable,
                steps_text,
                console=console,
            )
        )

    except CopierError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
    except (OSError, ValueError, RuntimeError) as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
