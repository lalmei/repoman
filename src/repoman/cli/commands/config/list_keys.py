"""List-keys subcommand for config - list prompt keys from the template schema."""

from __future__ import annotations

import json
from typing import Annotated

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
        rows = []
        for k in keys:
            meta = schema[k]
            type_ = meta.get("type", "")
            default = meta.get("default", "")
            when = meta.get("when", "")
            if isinstance(default, str) and len(default) > 40:
                default = default[:37] + "..."
            rows.append((k, type_, str(default), str(when)))
        col_widths = [max(len(r[0]) for r in rows) + 2, 6, 20, 30]
        header = ("Key", "Type", "Default", "When")
        console.print("".join(h.ljust(col_widths[i]) for i, h in enumerate(header)))
        console.print("-" * (sum(col_widths)))
        for r in rows:
            console.print("".join(str(r[i]).ljust(col_widths[i]) for i in range(4)))
    else:
        for k in keys:
            console.print(k)
