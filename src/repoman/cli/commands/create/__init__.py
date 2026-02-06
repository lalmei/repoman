"""Create command for generating repositories from templates."""

from pathlib import Path
from typing import Annotated

import yaml
from typer import Argument, Context, Exit, Option, Typer

from repoman.cli.commands.create._shared import build_preset_data, run_create
from repoman.cli.commands.create.cli_only import app as cli_only_app
from repoman.cli.commands.create.docs_only import app as docs_only_app
from repoman.cli.commands.create.fastapi_mvc import app as fastapi_mvc_app
from repoman.cli.commands.create.library import app as library_app
from repoman.cli.commands.create.rag_service import app as rag_service_app
from repoman.cli.messages import answers_file_not_found, error_panel
from repoman.utils.logging import get_logger_console

app = Typer(add_completion=True)

app.add_typer(cli_only_app, name="cli")
app.add_typer(docs_only_app, name="docs-only")
app.add_typer(library_app, name="library")
app.add_typer(fastapi_mvc_app, name="fastapi")
app.add_typer(rag_service_app, name="rag")


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
    preset: Annotated[
        str | None,
        Option(
            "--preset",
            "-p",
            help="Use a preset: cli, docs-only, library, fastapi, rag",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        Option("--dry-run", help="Show what would be created without actually creating"),
    ] = False,
) -> None:
    """Create a new Python project using the repoman template."""
    logger, console = get_logger_console()

    if template_path is None:
        current_file = Path(__file__)
        template_path_obj = current_file.parent.parent.parent.parent
        logger.info(f"Using main template at {template_path_obj}")
    else:
        template_path_obj = Path(template_path)

    output_dir_base = Path.cwd() if output_dir is None else Path(output_dir)

    if answers_file is not None:
        answers_path = Path(answers_file).resolve()
        if not answers_path.exists():
            console.print(error_panel(answers_file_not_found(answers_path), console=console))
            raise Exit(1) from None
        console.print(f"Using answers file: {answers_path}")
        with open(answers_path) as f:
            data = yaml.safe_load(f) or {}
    elif preset is not None:
        preset_key = preset.replace("-", "_")  # docs-only -> docs_only
        valid = ("cli", "docs_only", "library", "fastapi", "rag")
        if preset_key not in valid:
            console.print(
                error_panel(
                    f"Invalid preset '{preset}'. Choose from: cli, docs-only, library, fastapi, rag",
                    console=console,
                )
            )
            raise Exit(1) from None
        data = build_preset_data(preset_key, project_name)
    else:
        data = None

    run_create(
        project_name=project_name,
        output_dir=output_dir_base,
        template_path=template_path_obj,
        data=data,
        force=force,
        dry_run=dry_run or ctx.obj.get("dry_run", True),
    )
