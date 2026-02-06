"""Library create subcommand: minimal Python library (backbone only)."""

from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from repoman.cli.commands.create._shared import build_preset_data, run_create

app = Typer(
    add_completion=True,
    help="Create a minimal Python library (backbone only, no CLI/FastAPI/RAG/dataset).",
)


@app.command(no_args_is_help=True)
def library(
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
        Option(
            "--output", "-o", help="Output directory (defaults to current directory)"
        ),
    ] = None,
    force: bool = Option(False, "--force", "-f", help="Overwrite existing files"),
    dry_run: bool = Option(
        False, "--dry-run", help="Show what would be created without creating"
    ),
) -> None:
    """Create a minimal Python library with no CLI, FastAPI, RAG, or dataset."""
    current_file = Path(__file__)
    template_path_obj = (
        current_file.parent.parent.parent.parent
        if template_path is None
        else Path(template_path)
    )
    output_dir_base = Path.cwd() if output_dir is None else Path(output_dir)
    data = build_preset_data("library", project_name)
    run_create(
        project_name=project_name,
        output_dir=output_dir_base,
        template_path=template_path_obj,
        data=data,
        force=force,
        dry_run=dry_run,
    )
