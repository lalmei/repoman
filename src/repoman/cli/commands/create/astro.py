"""Generate a static Astro personal site."""

import re
from pathlib import Path
from typing import Annotated

from typer import Argument, BadParameter, Context, Option

from repoman.cli.commands.create._shared import run_create
from repoman.copier.sources import ASTRO_TEMPLATE


def create_astro(
    ctx: Context,
    project_name: Annotated[str, Argument(help="Name of the project to create")],
    output_dir: Annotated[Path | None, Option("--output", "-o", help="Base output directory")] = None,
    force: Annotated[bool, Option("--force", "-f", help="Overwrite existing files")] = False,
    dry_run: Annotated[bool, Option("--dry-run", help="Preview generation without creating files")] = False,
) -> None:
    """Create a static Astro personal site."""
    if not re.fullmatch(r"[a-z][a-z0-9-]*", project_name):
        raise BadParameter(
            "Use lowercase letters, digits, and hyphens, starting with a letter.", param_hint="project_name"
        )
    run_create(
        project_name=project_name,
        output_dir=output_dir or Path.cwd(),
        template_path=ASTRO_TEMPLATE,
        data={"repoman_astro": True},
        force=force,
        dry_run=dry_run or (ctx.obj or {}).get("dry_run", False),
    )
