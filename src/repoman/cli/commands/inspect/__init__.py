"""Inspect command for diagnosing repoman-managed repositories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typer import Exit, Option, Typer, echo

from repoman.cli.messages import (
    error_panel,
    not_a_git_repository,
    project_dir_not_found,
    project_path_not_directory,
    unknown_format,
)
from repoman.inspection import InspectionError, InspectionReport, inspect_repository
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="""Inspect a repository for repoman lifecycle readiness.

Examples:

    repoman inspect
    repoman inspect ./my-project
    repoman inspect ./my-project --format json
    repoman inspect ./my-project --answers ./my-project/custom-answers.yml
""",
)


@app.callback(invoke_without_command=True)
def inspect_(
    path: Annotated[
        Path,
        Option("--path", "-p", path_type=Path, help="Path to the git repository"),
    ] = Path("."),
    answers_file: Annotated[
        Path | None,
        Option("--answers", "-a", path_type=Path, help="Override path to the answers file"),
    ] = None,
    output_format: Annotated[
        str,
        Option("--format", "-f", help="Output format: table or json"),
    ] = "table",
    no_header: Annotated[
        bool,
        Option("--no-header", help="Hide table headers for terminal output"),
    ] = False,
) -> None:
    """Inspect a repository and report whether it is ready for repoman update."""
    _logger, console = get_logger_console()
    repo_path = path.resolve()

    if not repo_path.exists():
        console.print(error_panel(project_dir_not_found(repo_path), console=console))
        raise Exit(1) from None
    if not repo_path.is_dir():
        console.print(error_panel(project_path_not_directory(repo_path), console=console))
        raise Exit(1) from None
    if not (repo_path / ".git").exists():
        console.print(error_panel(not_a_git_repository(repo_path), console=console))
        raise Exit(1) from None

    try:
        report = inspect_repository(repo_path, answers_file=answers_file)
    except InspectionError as exc:
        console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc

    if output_format == "json":
        echo(json.dumps(report.to_dict(), indent=2))
    elif output_format == "table":
        _print_table(console, report, show_header=not no_header)
    else:
        console.print(error_panel(unknown_format(output_format), console=console))
        raise Exit(1) from None

    if report.fatal:
        raise Exit(1) from None


def _print_table(console: object, report: InspectionReport, *, show_header: bool) -> None:
    if not hasattr(console, "print"):
        return

    summary = Table(show_header=show_header, header_style="bold")
    summary.add_column("Field")
    summary.add_column("Value")
    summary.add_row("Path", report.path)
    summary.add_row("Managed", "yes" if report.managed else "no")
    summary.add_row("Status", report.status)
    summary.add_row("Answers file", report.answers_file.path)
    summary.add_row("Answers exists", "yes" if report.answers_file.exists else "no")
    summary.add_row(
        "Answers in project",
        _bool_text(report.answers_file.within_project),
    )
    summary.add_row("Template source", report.template.src_path or "-")
    summary.add_row("Template commit", report.template.commit or "-")
    summary.add_row("Template ref", report.template.vcs_ref or "-")
    summary.add_row("Docs only", _bool_text(report.features.docs_only))
    summary.add_row("FastAPI", _bool_text(report.features.fastapi_enabled))
    summary.add_row("Dataset", _bool_text(report.features.dataset_enabled))
    summary.add_row("Notebooks", _bool_text(report.features.python_notebooks))
    summary.add_row("CLI enabled", _bool_text(report.features.cli_enabled))
    summary.add_row("Extension manifest", report.extensions.manifest_path)
    summary.add_row("Active extensions", str(len(report.extensions.active)))
    summary.add_row("Update ready", _bool_text(report.update_readiness.ready))
    console.print(summary)

    if report.update_readiness.blockers:
        console.print(
            Panel(
                Text("\n".join(report.update_readiness.blockers), style="red"),
                title="Blockers",
                border_style="red",
            )
        )
    if report.update_readiness.warnings:
        console.print(
            Panel(
                Text("\n".join(report.update_readiness.warnings), style="yellow"),
                title="Warnings",
                border_style="yellow",
            )
        )


def _bool_text(value: bool | None) -> str:
    if value is None:
        return "-"
    return "yes" if value else "no"
