"""C++ create subcommand: Meson-based C++ library."""

from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from repoman.cli.commands.create._shared import run_create
from repoman.copier import build_preset_data

app = Typer(
    add_completion=True,
    help="""Create a Meson-based C++ library project.

Examples:

    repoman create cpp cpp my-lib
    repoman create cpp cpp my-lib -o ./libs --dry-run
""",
)


def _default_template_path() -> Path:
    """Return the bundled C++ template path."""
    current_file = Path(__file__)
    return current_file.parent.parent.parent.parent / "cpp_template"


@app.command(no_args_is_help=True)
def cpp(
    project_name: str = Argument(..., help="Name of the project to create"),
    template_path: Annotated[
        str | None,
        Option(
            "--template",
            "-t",
            help="Path to custom template (defaults to bundled C++ template)",
        ),
    ] = None,
    output_dir: Annotated[
        str | None,
        Option("--output", "-o", help="Output directory (defaults to current directory)"),
    ] = None,
    force: bool = Option(False, "--force", "-f", help="Overwrite existing files"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be created without creating"),
) -> None:
    """Create a Meson-based C++ library project."""
    template_path_obj = _default_template_path() if template_path is None else Path(template_path)
    output_dir_base = Path.cwd() if output_dir is None else Path(output_dir)
    data = build_preset_data("cpp", project_name)
    run_create(
        project_name=project_name,
        output_dir=output_dir_base,
        template_path=template_path_obj,
        data=data,
        force=force,
        dry_run=dry_run,
    )
