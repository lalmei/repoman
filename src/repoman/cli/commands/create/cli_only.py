"""CLI-only create subcommand: plain CLI project (no FastAPI, RAG, dataset)."""

from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from repoman.cli.commands.create._shared import run_create
from repoman.copier import build_preset_data

app = Typer(
    add_completion=True,
    help="""Create a plain CLI project (no FastAPI, RAG, or dataset).

Examples:

    repoman create cli cli my-app
    repoman create cli cli my-app -o ~/projects --dry-run
""",
)


@app.command(no_args_is_help=True)
def cli(
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
    force: bool = Option(False, "--force", "-f", help="Overwrite existing files"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be created without creating"),
) -> None:
    """Create a plain CLI project with no FastAPI, RAG, or dataset modules.

    Examples:

        repoman create cli cli my-app
        repoman create cli cli my-app --force
    """
    current_file = Path(__file__)
    template_path_obj = current_file.parent.parent.parent.parent if template_path is None else Path(template_path)
    output_dir_base = Path.cwd() if output_dir is None else Path(output_dir)
    data = build_preset_data("cli", project_name)
    run_create(
        project_name=project_name,
        output_dir=output_dir_base,
        template_path=template_path_obj,
        data=data,
        force=force,
        dry_run=dry_run,
    )
