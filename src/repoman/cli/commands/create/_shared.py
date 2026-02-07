"""Shared logic for create command and subcommands."""

from pathlib import Path

from copier import run_copy
from copier.errors import CopierError
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Exit

from repoman.cli.messages import (
    dry_run_create,
    error_panel,
    format_next_steps,
    output_dir_exists_use_force,
    project_created,
    warning_panel,
)
from repoman.copier import build_copier_options, validate_project_name
from repoman.utils.logging import get_logger_console


def run_create(
    project_name: str,
    output_dir: Path,
    template_path: Path,
    data: dict | None,
    force: bool,
    dry_run: bool,
) -> None:
    """Run the create flow: validate, build copier options, run copy or dry-run."""
    _logger, console = get_logger_console()

    try:
        validate_project_name(project_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from None

    output_dir_obj = output_dir / project_name

    if output_dir_obj.exists() and not force:
        console.print(warning_panel(output_dir_exists_use_force(output_dir_obj), console=console))
        raise Exit(1) from None

    copier_options = build_copier_options(project_name, output_dir, template_path, data)

    next_steps = [
        f"cd {output_dir_obj}",
        "Review and customize the generated project",
        "Initialize git repository",
        "Start developing!",
    ]
    steps_text = format_next_steps(next_steps, console=console)

    if dry_run:
        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}
        console.print(
            dry_run_create(
                project_name,
                output_dir_obj,
                template_path,
                copier_options_serializable,
                steps_text,
                _console=console,
            )
        )
        return

    try:
        if copier_options.get("data") is not None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating project...", total=None)
                run_copy(**copier_options)
                progress.update(task, description="Project created successfully!")
        else:
            console.print("Creating project...")
            run_copy(**copier_options)

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
