"""Validate subcommand for config - check an answers file against the template schema."""

from pathlib import Path
from typing import Annotated

import yaml
from typer import Exit, Option, Typer

from repoman.cli.messages import (
    copier_commit_missing_validate_warning,
    copier_update_missing_commit_remediation,
    error_panel,
    invalid_yaml,
    schema_not_found_skipping_validation,
    warning_panel,
)
from repoman.config import load_answers, missing_commit_for_copier_update
from repoman.copier import ValidationReport, load_prompt_schema, validate_answers
from repoman.utils.logging import get_logger_console
from repoman.utils.ui.layout import layout_validation_failed, use_layout

app = Typer(
    add_completion=True,
    help="""Validate an answers file against the template schema.

Examples:

    repoman config validate
    repoman config validate -a ./.copier-answers.yml
    repoman config validate --strict --quiet
    repoman config validate --fail-missing-copier-commit
""",
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
    fail_missing_copier_commit: Annotated[
        bool,
        Option(
            "--fail-missing-copier-commit",
            help="Fail if `_src_path` is set but `_commit` is missing (needed for repoman update)",
        ),
    ] = False,
) -> None:
    """Validate an answers file for repoman create.

    Loads the file and checks that required keys exist and types match the
    template schema (from copier.yml). Use --strict to also fail on extra keys.
    """
    _logger, console = get_logger_console()
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
        if missing_commit_for_copier_update(answers):
            if fail_missing_copier_commit:
                console.print(
                    error_panel(
                        copier_update_missing_commit_remediation(answers_basename=path.name),
                        console=console,
                    )
                )
                raise Exit(1)
            if not quiet:
                console.print(warning_panel(copier_commit_missing_validate_warning(), console=console))
        if not quiet:
            console.print("[green]Validation passed.[/green]")
        return

    if use_layout(console, min_width=120):
        layout, height = layout_validation_failed(report)
        console.print(layout, height=height)
    else:
        body = _format_report(report)
        console.print(error_panel(body, console=console))
    raise Exit(1)
