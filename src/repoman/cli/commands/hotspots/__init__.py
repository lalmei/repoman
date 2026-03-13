"""Hotspots command for finding refactoring candidates in git repositories."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.table import Table
from typer import Exit, Option, Typer

from repoman.cli.messages import error_panel
from repoman.hotspots import HotspotResult, find_hotspots, generate_report
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="Find code hotspots that may need refactoring using git history analysis",
)


@app.callback(invoke_without_command=True)
def hotspots(
    path: Annotated[
        Path,
        Option(
            "--path",
            "-p",
            path_type=Path,
            help="Path to the git repository (default: current directory)",
        ),
    ] = Path("."),
    limit: Annotated[
        int,
        Option(
            "--limit",
            "-n",
            help="Maximum number of files to show",
            min=1,
        ),
    ] = 20,
    since: Annotated[
        str | None,
        Option(
            "--since",
            help="Start date (YYYY-MM-DD) for commit range",
        ),
    ] = None,
    to: Annotated[
        str | None,
        Option(
            "--to",
            help="End date (YYYY-MM-DD) for commit range",
        ),
    ] = None,
    extensions: Annotated[
        str | None,
        Option(
            "--extensions",
            "-e",
            help="Comma-separated file extensions to include (e.g. .py,.ts)",
        ),
    ] = None,
    output_format: Annotated[
        str,
        Option(
            "--format",
            "-f",
            help="Output format: table, json, or html",
        ),
    ] = "table",
    output_dir: Annotated[
        Path,
        Option(
            "--output",
            "-o",
            path_type=Path,
            help="Output directory for html report (default: hotspot_report)",
        ),
    ] = Path("hotspot_report"),
    no_header: Annotated[
        bool,
        Option(
            "--no-header",
            help="Hide column headers (for piping)",
        ),
    ] = False,
) -> None:
    """Find code hotspots that may need refactoring.

    Analyzes git history using commits count, code churn, and contributor count
    to identify files with high change activity. These files are often good
    candidates for refactoring.
    """
    logger, console = get_logger_console()
    repo_path = path.resolve()

    if not repo_path.exists():
        console.print(error_panel(f"Path does not exist: {repo_path}", console=console))
        raise Exit(1) from None

    if not repo_path.is_dir():
        console.print(error_panel(f"Path is not a directory: {repo_path}", console=console))
        raise Exit(1) from None

    git_dir = repo_path / ".git"
    if not git_dir.exists():
        console.print(
            error_panel(
                f"Not a git repository (no .git directory): {repo_path}",
                console=console,
            )
        )
        raise Exit(1) from None

    since_dt: datetime | None = None
    to_dt: datetime | None = None
    if since is not None:
        try:
            since_dt = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            console.print(
                error_panel(
                    f"Invalid --since date format (use YYYY-MM-DD): {since}",
                    console=console,
                )
            )
            raise Exit(1) from None
    if to is not None:
        try:
            to_dt = datetime.strptime(to, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError:
            console.print(error_panel(f"Invalid --to date format (use YYYY-MM-DD): {to}", console=console))
            raise Exit(1) from None

    ext_list: list[str] | None = None
    if extensions is not None:
        ext_list = [ext.strip() for ext in extensions.split(",") if ext.strip()]

    try:
        results = find_hotspots(
            repo_path,
            since=since_dt,
            to=to_dt,
            file_extensions=ext_list,
        )
    except Exception as e:
        logger.exception("Hotspot analysis failed")
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    results = results[:limit]

    if output_format == "json":
        _print_json(console, results)
    elif output_format == "html":
        out = output_dir.resolve()
        out.mkdir(parents=True, exist_ok=True)
        generate_report(results, repo_path, out, since=since_dt, to=to_dt)
        index_path = out / "index.html"
        console.print(f"Report written to {index_path}")
    else:
        _print_table(console, results, show_header=not no_header)


def _print_table(console: Console, results: list[HotspotResult], *, show_header: bool = True) -> None:
    table = Table(show_header=show_header, header_style="bold")
    table.add_column("File", style="cyan")
    table.add_column("Commits", justify="right")
    table.add_column("Churn", justify="right")
    table.add_column("Contributors", justify="right")

    for r in results:
        table.add_row(
            r.file_path,
            str(r.commits_count),
            str(r.code_churn),
            str(r.contributors_count),
        )

    console.print(table)


def _print_json(console: Console, results: list[HotspotResult]) -> None:
    data = [
        {
            "file": r.file_path,
            "commits": r.commits_count,
            "churn": r.code_churn,
            "contributors": r.contributors_count,
        }
        for r in results
    ]
    console.print(json.dumps(data, indent=2))
