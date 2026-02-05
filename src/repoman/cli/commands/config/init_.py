"""Init subcommand for config - generate a template answers file."""

from pathlib import Path
from typing import Annotated

from typer import Context, Exit, Option, Typer

from repoman.cli.messages import (
    command_created,
    error_panel,
    file_exists_use_force,
    format_next_steps,
    output_path_not_file,
    template_not_found,
    template_path_not_file,
    warning_panel,
)
from repoman.resources import get_copier_answers_template
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="Generate a template answers file for non-interactive create",
)


@app.callback(invoke_without_command=True)
def init(
    ctx: Context,
    output: Annotated[
        Path,
        Option(
            "--output",
            "-o",
            path_type=Path,
            help="Output path for the answers file (default: .copier-answers.yml in cwd)",
        ),
    ] = Path(".copier-answers.yml"),
    template: Annotated[
        Path | None,
        Option(
            "--template",
            "-t",
            path_type=Path,
            help="Path to a custom template file (default: use bundled template)",
        ),
    ] = None,
    force: Annotated[  # noqa: FBT002
        bool,
        Option("--force", "-f", help="Overwrite existing file"),
    ] = False,
) -> None:
    """Generate a template answers file for use with repoman create --answers.

    Writes a YAML file with all keys expected by the repoman template. Edit the
    file, then run: repoman create PROJECT_NAME --answers <path-to-this-file>
    """
    logger, console = get_logger_console()

    # Resolve output path: if it's a directory, use <dir>/.copier-answers.yml
    output_resolved = output.resolve()
    if output_resolved.is_dir():
        output_resolved = output_resolved / ".copier-answers.yml"
    elif output_resolved.exists() and not output_resolved.is_file():
        console.print(error_panel(output_path_not_file(output_resolved), console=console))
        raise Exit(1) from None

    # Load template content
    if template is not None:
        template_path = Path(template).resolve()
        if not template_path.exists():
            console.print(error_panel(template_not_found(template_path), console=console))
            raise Exit(1) from None
        if not template_path.is_file():
            console.print(error_panel(template_path_not_file(template_path), console=console))
            raise Exit(1) from None
        logger.info(f"Using custom template at {template_path}")
        content = template_path.read_text(encoding="utf-8")
    else:
        content = get_copier_answers_template()

    # Refuse to overwrite unless --force
    if output_resolved.exists() and not force:
        console.print(warning_panel(file_exists_use_force(output_resolved), console=console))
        raise Exit(1) from None

    dry_run = ctx.obj.get("dry_run", False)
    if dry_run:
        console.print(f"[dim]Dry run: would write template to {output_resolved} ({len(content)} bytes)[/dim]")
        return

    # Write the file
    try:
        output_resolved.parent.mkdir(parents=True, exist_ok=True)
        output_resolved.write_text(content, encoding="utf-8")
    except OSError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    next_steps = [
        f"Edit {output_resolved} with your project values",
        "Run: repoman create PROJECT_NAME --answers " + str(output_resolved),
    ]
    steps_text = format_next_steps(next_steps, console=console)
    body_text = f"Template written to {output_resolved}\n\nNext steps:\n{steps_text}"
    console.print(command_created("config init", body_text, console=console))
