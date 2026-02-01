"""Create command for generating repositories from templates."""

import re
from pathlib import Path

from copier import run_copy
from copier.errors import CopierError
from rich.console import Group
from rich.json import JSON
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from typer import Argument, Context, Exit, Option, Typer

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
        Option("--template", "-t", help="Path to custom template (defaults to main template)"),
    ] = None,
    output_dir: Annotated[
        str | None,
        Option("--output", "-o", help="Output directory (defaults to current directory)"),
    ] = None,
    answers_file: Annotated[
        Path | None,
        Option("--answers", "-a", help="Path to answers file"),
    ] = None,
    force: Annotated[  # noqa: FBT002
        bool,
        Option("--force", "-f", help="Force overwrite of existing files"),
    ] = False,
    dry_run: Annotated[  # noqa: FBT002
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
        console.print(
            Panel(
                Text(f"Invalid project name: {e}", style="red"),
                title="Error",
                border_style="red",
            )
        )
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
        console.print(
            Panel(
                Text(
                    f"Output directory {output_dir_obj} already exists. Use --force to overwrite.",
                    style="yellow",
                ),
                title="Warning",
                border_style="yellow",
            )
        )
        raise Exit(1) from None
    if answers_file is not None:
        answers_path = Path(answers_file).resolve()
        if not answers_path.exists():
            console.print(
                Panel(
                    Text(f"Answers file not found: {answers_path}", style="red"),
                    title="Error",
                    border_style="red",
                )
            )
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

    steps_text = "\n".join(f"  {i + 1}. {step}" for i, step in enumerate(next_steps))

    if dry_run or ctx.obj.get("dry_run", True):
        # Convert Path objects to strings for JSON serialization
        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}

        console.print(
            Panel(
                Group(
                    Text(
                        f"Would create project '{project_name}' in {output_dir_obj}\n"
                        f"Using template: {template_path_obj}\n",
                        style="blue",
                    ),
                    Text("Copier options:", style="blue"),
                    JSON.from_data(copier_options_serializable, indent=2),
                    Text(f"\nNext steps:\n{steps_text}", style="blue"),
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
            run_copy(**copier_options)  # type: ignore[arg-type]  # copier accepts dict with mixed types

            progress.update(task, description="Project created successfully!")

        # Success message
        # Convert Path objects to strings for JSON serialization
        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}

        console.print(
            Panel(
                Group(
                    Text(
                        f"Project '{project_name}' created successfully in {output_dir_obj}\n",
                        style="green",
                    ),
                    Text("Copier options used:", style="green"),
                    JSON.from_data(copier_options_serializable, indent=2),
                    Text(f"\nNext steps:\n{steps_text}", style="green"),
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
        raise Exit(1) from e
    except (OSError, ValueError, RuntimeError) as e:
        # Catch common file system and runtime errors that might occur during project creation
        console.print(
            Panel(
                Text(f"Unexpected error: {e}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise Exit(1) from e
