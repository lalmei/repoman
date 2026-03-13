"""Update command for updating repositories from templates."""

from pathlib import Path

from copier import Worker
from copier.errors import CopierError
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Argument, Context, Exit, Option, Typer

from repoman.cli.messages import (
    copier_answers_not_found_for_update,
    dry_run_update,
    error_panel,
    format_next_steps,
    invalid_conflict_mode,
    project_dir_not_found,
    project_path_not_directory,
    project_updated,
    template_path_does_not_exist,
)
from repoman.copier import ExtensionLifecycleError, sync_extensions
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
    skip_extensions: bool = Option(False, "--skip-extensions", help="Skip syncing Copier-managed extensions"),
) -> None:
    """Update an existing Python project using the repoman template."""
    logger, console = get_logger_console()

    # Validate conflict mode
    if conflict not in ["inline", "rej"]:
        console.print(error_panel(invalid_conflict_mode(conflict), console=console))
        raise Exit(1) from None

    # Determine project directory
    project_dir_obj: Path = Path(project_dir).resolve()

    # Validate project directory exists
    if not project_dir_obj.exists():
        console.print(error_panel(project_dir_not_found(project_dir_obj), console=console))
        raise Exit(1) from None

    if not project_dir_obj.is_dir():
        console.print(error_panel(project_path_not_directory(project_dir_obj), console=console))
        raise Exit(1) from None

    # Determine answers file path
    answers_file_path: Path
    if answers_file is None:
        answers_file_path = project_dir_obj / ".copier-answers.yml"
    else:
        answers_file_path = Path(answers_file).resolve()

    # Validate answers file exists (required for copier update)
    if not answers_file_path.exists():
        console.print(error_panel(copier_answers_not_found_for_update(answers_file_path), console=console))
        raise Exit(1) from None

    # Determine template path
    template_path_obj: Path | None = None
    if template_path is not None:
        template_path_obj = Path(template_path).resolve()
        if not template_path_obj.exists():
            console.print(error_panel(template_path_does_not_exist(template_path_obj), console=console))
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
        extension_dry_run_options: dict[str, str | bool | None | int] | None = None
        if not skip_extensions:
            try:
                extension_result = sync_extensions(
                    project_dir=project_dir_obj,
                    force=force,
                    conflict=conflict,
                    dry_run=True,
                )
                extension_dry_run_options = {
                    "extension_count": len(extension_result.synced),
                }
            except ExtensionLifecycleError as e:
                console.print(error_panel(str(e), console=console))
                raise Exit(1) from e

        copier_options_serializable: dict[str, object] = {
            k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items() if v is not None
        }
        if extension_dry_run_options is not None:
            copier_options_serializable["extensions"] = extension_dry_run_options
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

            if not skip_extensions:
                sync_extensions(
                    project_dir=project_dir_obj,
                    force=force,
                    conflict=conflict,
                    dry_run=False,
                )

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
    except ExtensionLifecycleError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
    except (OSError, ValueError, RuntimeError) as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
