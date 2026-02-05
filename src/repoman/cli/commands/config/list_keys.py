"""List-keys subcommand for config - list prompt keys from the template schema."""

from __future__ import annotations

import json
from typing import Annotated

from rich.table import Table
from typer import Exit, Option, Typer

from repoman.cli.commands.config.utils import load_prompt_schema
from repoman.cli.messages import error_panel, schema_not_found, unknown_format
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="List prompt keys expected by the template (from copier.yml)",
)


def _serialize_value(v: object) -> object:
    """Make schema values JSON-serializable."""
    if isinstance(v, (str, int, float, bool, type(None))):
        return v
    if isinstance(v, list):
        return [_serialize_value(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _serialize_value(x) for k, x in v.items()}
    return str(v)


@app.callback(invoke_without_command=True)
def list_keys(
    format: Annotated[  # noqa: A002
        str,
        Option(
            "--format",
            "-f",
            help="Output format: table (default) or json",
        ),
    ] = "table",
    include_meta: Annotated[
        bool,
        Option("--include-meta", help="Include type, default, when in output"),
    ] = False,
) -> None:
    """List prompt keys the template expects (from copier.yml).

    Excludes copier meta keys (those starting with _). Use --include-meta to
    show type, default, and when for each key. Use --format json for machine-readable output.
    """
    logger, console = get_logger_console()
    schema = load_prompt_schema()
    if not schema:
        console.print(error_panel(schema_not_found(), console=console))
        raise Exit(1)

    keys = sorted(schema.keys())

    if format == "json":
        if include_meta:
            out = {k: _serialize_value(schema[k]) for k in keys}
        else:
            out = keys
        console.print(json.dumps(out, indent=2))
        return

    if format != "table":
        console.print(error_panel(unknown_format(format), console=console))
        raise Exit(1)

    # Table: key, and optionally type, default, when
    if include_meta:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Key")
        table.add_column("Type")
        table.add_column("Default")
        table.add_column("When")
        for k in keys:
            meta = schema[k]
            type_ = meta.get("type", "")
            default = meta.get("default", "")
            when = meta.get("when", "")
            if isinstance(default, str) and len(default) > 40:
                default = default[:37] + "..."
            table.add_row(k, str(type_), str(default), str(when))
        console.print(table)
    else:
        table = Table(show_header=False)
        table.add_column("Key")
        for k in keys:
            table.add_row(k)
        console.print(table)
