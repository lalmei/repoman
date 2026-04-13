"""Show subcommand for config - print bundled template answers or a single key."""

from pathlib import Path
from typing import Annotated

import yaml
from typer import Exit, Option, Typer

from repoman.cli.messages import (
    file_exists_use_force,
    key_not_in_template,
    warning_panel,
)
from repoman.cli.messages.layout import layout_config_show_template, use_layout
from repoman.resources import get_copier_answers_template
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="""Print the bundled template answers or a single key.

Examples:

    repoman config show
    repoman config show --key python_package_import_name
    repoman config show -o ./answers-dump.yml
""",
)


@app.callback(invoke_without_command=True)
def show(
    key: Annotated[
        str | None,
        Option("--key", "-k", help="Show only this key's value"),
    ] = None,
    output: Annotated[
        Path | None,
        Option(
            "--output",
            "-o",
            path_type=Path,
            help="Write output to this path instead of stdout",
        ),
    ] = None,
    force: Annotated[
        bool,
        Option("--force", "-f", help="Overwrite existing file when using --output"),
    ] = False,
) -> None:
    """Print the bundled template answers for repoman create.

    With --key, print only that key's value. With --output, write to a file
    (refuse to overwrite unless --force).
    """
    _logger, console = get_logger_console()
    raw = get_copier_answers_template()
    data = yaml.safe_load(raw) or {}

    if key is not None:
        if key not in data:
            console.print(warning_panel(key_not_in_template(key), console=console))
            raise Exit(1)
        text = str(data[key]) if data[key] is not None else ""
        if output is None:
            console.print(text)
        else:
            out_path = output.resolve()
            if out_path.exists() and not force:
                console.print(warning_panel(file_exists_use_force(out_path), console=console))
                raise Exit(1)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            if not force or out_path.exists():
                console.print(f"Wrote to {out_path}")
        return

    # Full template
    if output is None:
        if use_layout(console):
            layout, height = layout_config_show_template(raw, len(data))
            console.print(layout, height=height)
        else:
            console.print(raw)
        return

    out_path = output.resolve()
    if out_path.exists() and not force:
        console.print(warning_panel(file_exists_use_force(out_path), console=console))
        raise Exit(1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(raw, encoding="utf-8")
    console.print(f"Wrote template to {out_path}")
