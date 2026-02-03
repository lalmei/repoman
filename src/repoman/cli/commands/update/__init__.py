"""Update command for updating repositories from templates."""

from pathlib import Path

from copier import Worker
from copier.errors import CopierError
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, Context, Exit, Option, Typer

from repoman.cli.messages import (
    dry_run_update,
    error_panel,
    format_next_steps,
    project_updated,
)
from repoman.utils.logging import get_logger_console

app = Typer(add_completion=True)


@app.callback(invoke_without_command=True)
def update(
    ctx: Context,
    project_dir: str = Argument(..., help="Path to the project directory to update"),
    template_path: str | None = Option(
        None,
        "--template",
        "-t",
        help="Override template path (normally read from .copier-answers.yml)",
    ),
    vcs_ref: str | None = Option(
        None,
        "--vcs-ref",
        "-r",
        help="Git ref/tag to update to (defaults to latest)",
    ),
    answers_file: str | None = Option(
        None,
        "--answers",
        "-a",
        help="Path to .copier-answers.yml file (defaults to .copier-answers.yml in project_dir)",
    ),
    force: bool = Option(False, "--force", "-f", help="Force overwrite without asking"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be updated without making changes"),
    conflict: str = Option("inline", "--conflict", help="Conflict resolution mode: 'inline' or 'rej'"),
) -> None:
    """Update an existing Python project using the repoman template."""
    logger, console = get_logger_console()

    # Validate conflict mode
    if conflict not in ["inline", "rej"]:
        console.print(
            error_panel(
                f"Invalid conflict mode: {conflict}. Must be 'inline' or 'rej'.",
                console=console,
            )
        )
        raise Exit(1) from None

    # Determine project directory
    project_dir_obj: Path = Path(project_dir).resolve()

    # Validate project directory exists
    if not project_dir_obj.exists():
        console.print(error_panel(f"Project directory does not exist: {project_dir_obj}", console=console))
        raise Exit(1) from None

    if not project_dir_obj.is_dir():
        console.print(error_panel(f"Project path is not a directory: {project_dir_obj}", console=console))
        raise Exit(1) from None

    # Determine answers file path
    answers_file_path: Path
    if answers_file is None:
        answers_file_path = project_dir_obj / ".copier-answers.yml"
    else:
        answers_file_path = Path(answers_file).resolve()

    # Validate answers file exists (required for copier update)
    if not answers_file_path.exists():
        console.print(
            error_panel(
                f"Copier answers file not found: {answers_file_path}\n\n"
                "The .copier-answers.yml file is required for updating projects.\n"
                "Make sure you're in a repoman-generated project directory,\n"
                "or specify the answers file with --answers.",
                console=console,
            )
        )
        raise Exit(1) from None

    # Determine template path
    template_path_obj: Path | None = None
    if template_path is not None:
        template_path_obj = Path(template_path).resolve()
        if not template_path_obj.exists():
            console.print(
                error_panel(
                    f"Template path does not exist: {template_path_obj}",
                    console=console,
                )
            )
            raise Exit(1) from None
        logger.info(f"Using custom template at {template_path_obj}")
    else:
        logger.info("Template path will be read from .copier-answers.yml")

    # Prepare copier update options
    copier_options: dict[str, str | bool | None] = {
        "dst_path": str(project_dir_obj),
        "answers_file": str(answers_file_path),
        "overwrite": force,
        "quiet": True,  # Suppress interactive output
        "conflict": conflict,
        "unsafe": True,  # Template uses _jinja_extensions; required like create command
    }

    # Add optional parameters
    if template_path_obj is not None:
        copier_options["src_path"] = str(template_path_obj)
    else:
        # When src_path is None, copier reads it from the answers file
        copier_options["src_path"] = None

    if vcs_ref is not None:
        copier_options["vcs_ref"] = vcs_ref

    # Prepare next steps (used in both dry-run and success messages)
    next_steps = [
        "Review the updated files",
        "Resolve any conflicts if they occurred",
        "Test your project to ensure everything works",
        "Commit the changes",
    ]

    steps_text = format_next_steps(next_steps, console=console)

    if dry_run or ctx.obj.get("dry_run", False):
        copier_options_serializable = {
            k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items() if v is not None
        }
        console.print(
            dry_run_update(
                project_dir_obj,
                answers_file_path,
                template_path_obj,
                vcs_ref,
                copier_options_serializable,
                steps_text,
                _console=console,
            )
        )
        return

    # Update the project
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Updating project...", total=None)

            # Run copier update using Worker class
            # When src_path is None, copier reads it from the answers file
            with Worker(**copier_options) as worker:  # type: ignore[arg-type]  # copier accepts dict with mixed types
                worker.run_update()

            progress.update(task, description="Project updated successfully!")

        copier_options_serializable = {
            k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items() if v is not None
        }
        console.print(
            project_updated(
                project_dir_obj,
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
