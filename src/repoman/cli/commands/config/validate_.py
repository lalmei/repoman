"""Validate subcommand for config - check an answers file against the template schema."""

from pathlib import Path
from typing import Annotated

import yaml
from typer import Exit, Option, Typer

from repoman.cli.commands.config.utils import (
    ValidationReport,
    load_answers,
    load_prompt_schema,
    validate_answers,
)
from repoman.cli.messages import (
    error_panel,
    invalid_yaml,
    schema_not_found_skipping_validation,
    warning_panel,
)
from repoman.cli.messages.layout import layout_validation_failed, use_layout
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="Validate an answers file against the template schema",
)


def _format_report(report: ValidationReport) -> str:
    lines: list[str] = []
    if report.missing_keys:
        lines.append("Missing keys: " + ", ".join(report.missing_keys))
    if report.extra_keys:
        lines.append("Extra keys (not in schema): " + ", ".join(report.extra_keys))
    if report.type_errors:
        lines.extend(report.type_errors)
    return "\n".join(lines) if lines else "All checks passed."


@app.callback(invoke_without_command=True)
def validate(
    answers_file: Annotated[
        Path,
        Option(
            "--answers",
            "-a",
            path_type=Path,
            help="Path to the answers file (default: .copier-answers.yml)",
        ),
    ] = Path(".copier-answers.yml"),
    strict: Annotated[
        bool,
        Option("--strict", help="Fail on extra keys not in schema"),
    ] = False,
    quiet: Annotated[
        bool,
        Option("--quiet", "-q", help="Only exit with code; no success message"),
    ] = False,
) -> None:
    """Validate an answers file for repoman create.

    Loads the file and checks that required keys exist and types match the
    template schema (from copier.yml). Use --strict to also fail on extra keys.
    """
    logger, console = get_logger_console()
    path = answers_file.resolve()

    try:
        answers = load_answers(path)
    except FileNotFoundError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
    except yaml.YAMLError as e:
        console.print(error_panel(invalid_yaml(e), console=console))
        raise Exit(1) from e

    schema = load_prompt_schema()
    if not schema:
        console.print(warning_panel(schema_not_found_skipping_validation(), console=console))
        raise Exit(1)

    report = validate_answers(schema, answers, strict=strict)

    if report.valid:
        if not quiet:
            console.print("[green]Validation passed.[/green]")
        return

    if use_layout(console, min_width=120):
        console.print(layout_validation_failed(report))
    else:
        body = _format_report(report)
        console.print(error_panel(body, console=console))
    raise Exit(1)
