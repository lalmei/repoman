"""Compliance analysis commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typer import Exit, Option, Typer

from repoman.cli.messages import error_panel
from repoman.compliance import (
    BUILTIN_PROFILES,
    ComplianceConfigError,
    analyze_compliance,
    build_starter_config,
    manual_controls_for_profiles,
    reports_to_json,
    reports_to_markdown,
    write_reports,
)
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="""Analyze a git repository against built-in compliance profiles.

The v0 feature is a readiness check, not a certification claim.

Examples:

    repoman compliance check --path .
    repoman compliance check --profile soc2-software --tier-target bronze
    repoman compliance check --format markdown --output compliance.md
    repoman compliance init --profile soc2-software
""",
)


@app.command("check")
def check(
    path: Annotated[
        Path,
        Option("--path", "-p", path_type=Path, help="Path to the git repository"),
    ] = Path("."),
    profile: Annotated[
        list[str] | None,
        Option("--profile", help="Profile id to run. Repeat for multiple profiles."),
    ] = None,
    output_format: Annotated[
        str,
        Option("--format", "-f", help="Output format: table, json, markdown, or html"),
    ] = "table",
    output: Annotated[
        Path | None,
        Option("--output", "-o", path_type=Path, help="Output file or directory for non-table formats"),
    ] = None,
    compliance_file: Annotated[
        Path | None,
        Option("--compliance-file", path_type=Path, help="Override path to compliance.yml"),
    ] = None,
    tier_target: Annotated[
        str | None,
        Option("--tier-target", help="Optional target tier: bronze, silver, or gold"),
    ] = None,
    fail_on: Annotated[
        str,
        Option("--fail-on", help="Exit-code gate: unmet, unknown, or tier"),
    ] = "tier",
    strict: Annotated[
        bool,
        Option("--strict", help="Treat unknown controls as gate failures"),
    ] = False,
    no_header: Annotated[
        bool,
        Option("--no-header", help="Hide table headers for terminal output"),
    ] = False,
) -> None:
    """Run compliance analysis."""
    logger, console = get_logger_console()
    repo_path = path.resolve()
    selected_profiles = profile or list(BUILTIN_PROFILES)

    try:
        reports = analyze_compliance(
            repo_path,
            profile_ids=selected_profiles,
            compliance_file=compliance_file.resolve() if compliance_file is not None else None,
            requested_tier=tier_target,  # type: ignore[arg-type]
            fail_on=fail_on,  # type: ignore[arg-type]
            strict=strict,
        )
    except ComplianceConfigError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(2) from e
    except Exception as e:
        logger.exception("Compliance analysis failed")
        console.print(error_panel(str(e), console=console))
        raise Exit(2) from e

    if output_format == "table":
        _print_table(console, reports, show_header=not no_header)
    elif output_format == "json":
        if output is None:
            print(reports_to_json(reports))
        else:
            target = write_reports(reports, "json", output)
            console.print(f"Report written to {target}")
    elif output_format == "markdown":
        if output is None:
            print(reports_to_markdown(reports))
        else:
            target = write_reports(reports, "markdown", output)
            console.print(f"Report written to {target}")
    elif output_format == "html":
        target_dir = output or Path("compliance_report")
        target = write_reports(reports, "html", target_dir)
        console.print(f"Report written to {target}")
    else:
        console.print(error_panel(f"Unsupported format: {output_format}", console=console))
        raise Exit(2) from None

    if any(not report.gate.passed for report in reports):
        raise Exit(1) from None


@app.command("init")
def init_(
    path: Annotated[
        Path,
        Option("--path", "-p", path_type=Path, help="Repository path where the starter file should be written"),
    ] = Path("."),
    profile: Annotated[
        list[str] | None,
        Option("--profile", help="Profile id to include. Repeat for multiple profiles."),
    ] = None,
    output: Annotated[
        Path,
        Option("--output", "-o", path_type=Path, help="Destination compliance.yml path"),
    ] = Path("compliance.yml"),
    force: Annotated[
        bool,
        Option("--force", "-f", help="Overwrite an existing file"),
    ] = False,
) -> None:
    """Write a starter compliance.yml with manual controls."""
    _logger, console = get_logger_console()
    repo_path = path.resolve()
    selected_profiles = profile or list(BUILTIN_PROFILES)
    for profile_id in selected_profiles:
        if profile_id not in BUILTIN_PROFILES:
            console.print(error_panel(f"Unknown profile '{profile_id}'", console=console))
            raise Exit(2) from None

    destination = output if output.is_absolute() else repo_path / output
    if destination.exists() and not force:
        console.print(error_panel(f"File already exists: {destination}", console=console))
        raise Exit(2) from None

    content = build_starter_config(selected_profiles, manual_controls_for_profiles(selected_profiles))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    console.print(
        Panel(
            Text(
                f"Starter compliance config written to {destination}\n\n"
                "This file is a readiness checklist, not a certification claim.",
                style="green",
            ),
            title="Success",
            border_style="green",
        )
    )


def _print_table(console: Console, reports, *, show_header: bool) -> None:
    for report in reports:
        summary = Table(show_header=show_header, header_style="bold")
        summary.add_column("Profile")
        summary.add_column("Achieved")
        summary.add_column("Target")
        summary.add_column("Met", justify="right")
        summary.add_column("Waived", justify="right")
        summary.add_column("Unknown", justify="right")
        summary.add_column("Unmet", justify="right")
        summary.add_column("Gate")
        summary.add_row(
            report.profile_id,
            report.achieved_tier or "none",
            report.requested_tier or "n/a",
            str(report.summary_counts["met"]),
            str(report.summary_counts["waived"]),
            str(report.summary_counts["unknown"]),
            str(report.summary_counts["unmet"]),
            "pass" if report.gate.passed else "fail",
        )
        console.print(
            Panel(
                Text(report.disclaimer, style="yellow"),
                title=f"{report.profile_title}",
                border_style="blue",
            )
        )
        console.print(summary)

        sections = Table(show_header=show_header, header_style="bold")
        sections.add_column("Section")
        sections.add_column("Blocking")
        sections.add_column("Unknown")
        for section in report.sections:
            sections.add_row(
                section.name,
                ", ".join(section.blocking_controls) or "-",
                ", ".join(section.unknown_controls) or "-",
            )
        console.print(sections)

        if report.blocking_controls:
            console.print(f"Blocking controls: {json.dumps(report.blocking_controls)}")
        if report.advisory_controls:
            console.print(f"Advisory controls: {json.dumps(report.advisory_controls)}")
