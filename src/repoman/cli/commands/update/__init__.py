"""Update command for updating repositories from templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from copier import Worker
from copier.errors import CopierError
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from typer import Argument, Context, Exit, Option, echo

from repoman.cli.messages import (
    answers_file_must_live_in_project,
    copier_answers_not_found_for_update,
    copier_update_missing_commit_remediation,
    dry_run_update,
    error_panel,
    format_next_steps,
    invalid_conflict_mode,
    invalid_yaml,
    is_cannot_obtain_old_template_references_message,
    project_updated,
    repair_requires_commit,
    repair_requires_template_source,
    template_path_does_not_exist,
    update_modes_mutually_exclusive,
)
from repoman.config import load_answers
from repoman.copier.extension_lifecycle import MIRROR_KEY
from repoman.copier.sources import UPSTREAM_TEMPLATE
from repoman.inspection import InspectionError, InspectionReport, inspect_repository
from repoman.utils.logging import get_logger_console


def update(
    ctx: Context,
    *,
    project_dir: str = Argument(..., help="Path to the project directory to update"),
    template_path: str | None = Option(
        None,
        "--template",
        "-t",
        help="Override template path (normally read from .copier-answers.yml)",
    ),
    vcs_ref: str | None = Option(
        None,
        "--vcs-ref",
        "-r",
        help="Git ref/tag to update to (defaults to latest)",
    ),
    answers_file: str | None = Option(
        None,
        "--answers",
        "-a",
        help="Path to .copier-answers.yml file (defaults to .copier-answers.yml in project_dir)",
    ),
    force: bool = Option(
        False, "--force", "-f", help="Compatibility flag; update already uses saved answers and defaults"
    ),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be updated without making changes"),
    output_format: str = Option("table", "--format", help="Update plan format: table or json"),
    plan: bool = Option(False, "--plan", help="Show an update plan without writing files"),
    repair: bool = Option(False, "--repair", help="Repair Copier metadata in the answers file"),
    commit: str | None = Option(None, "--commit", help="Copier commit to write when using --repair"),
    conflict: str = Option("inline", "--conflict", help="Conflict resolution mode: 'inline' or 'rej'"),
    skip_extensions: bool = Option(False, "--skip-extensions", help="Hide extension follow-up in the update plan"),
    trust: bool = Option(False, "--trust", help="Allow custom template code and migrations"),
) -> None:
    """Update an existing Python project using the repoman template.

    Requires a Copier answers file (default: .copier-answers.yml inside the project).

    Examples:
        repoman update ./my-app
        repoman update ./my-app --plan
        repoman update ./my-app --dry-run
        repoman update ./my-app --repair --commit v1.2.3
        repoman update ./my-app --vcs-ref v1.2.0 --force
        repoman update ./my-app --skip-extensions
    """
    _logger, console = get_logger_console()

    _ = force  # Compatibility with earlier invocations.
    effective_dry_run = dry_run or (ctx.obj or {}).get("dry_run", False)
    json_plan = plan and output_format == "json"
    if output_format != "table" and not json_plan:
        echo("Use --format json with --plan.", err=True)
        raise Exit(1)

    invalid_options = None
    if conflict not in ["inline", "rej"]:
        invalid_options = invalid_conflict_mode(conflict)
    elif sum((plan, effective_dry_run, repair)) > 1:
        invalid_options = update_modes_mutually_exclusive()
    if invalid_options:
        if json_plan:
            echo(json.dumps({"schema_version": 1, "error": {"code": "invalid_options", "message": invalid_options}}))
        else:
            console.print(error_panel(invalid_options, console=console))
        raise Exit(1)

    project_dir_obj = Path(project_dir).resolve()
    answers_file_path = _resolve_answers_path(project_dir_obj, answers_file)
    template_path_obj = Path(template_path).resolve() if template_path else None

    try:
        report = inspect_repository(
            project_dir_obj,
            answers_file=answers_file_path,
            skip_extensions=True,
        )
    except InspectionError as exc:
        if json_plan:
            echo(json.dumps({"schema_version": 1, "error": {"code": "invalid_repository", "message": str(exc)}}))
        else:
            console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc

    if template_path_obj is not None and not template_path_obj.is_dir():
        report.update_readiness.ready = False
        report.update_readiness.blocker_codes.append("invalid_template_path")
        report.update_readiness.blockers.append(template_path_does_not_exist(template_path_obj))
        report.status = "warning"

    if json_plan:
        payload = report.to_dict()
        payload["target"] = {
            "source": str(template_path_obj) if template_path_obj else report.template.src_path,
            "requested_ref": vcs_ref,
            "trust_enabled": trust or (report.template.src_path == UPSTREAM_TEMPLATE and template_path_obj is None),
        }
        echo(json.dumps(payload, indent=2))
        if not report.update_readiness.ready:
            raise Exit(1)
        return

    if plan:
        _print_update_plan(
            console,
            report,
            template_path=template_path_obj,
            vcs_ref=vcs_ref,
            skip_extensions=skip_extensions,
        )
        if report.update_readiness.ready:
            return
        raise Exit(1) from None

    if repair:
        _run_repair(
            console=console,
            answers_file_path=answers_file_path,
            template_path_obj=template_path_obj,
            vcs_ref=vcs_ref,
            commit=commit,
            report=report,
        )
        return

    if not answers_file_path.exists():
        console.print(error_panel(copier_answers_not_found_for_update(answers_file_path), console=console))
        raise Exit(1) from None
    if report.answers_file.within_project is False:
        console.print(error_panel(answers_file_must_live_in_project(answers_file_path), console=console))
        raise Exit(1) from None
    if report.template.src_path and not report.template.commit:
        console.print(
            error_panel(
                copier_update_missing_commit_remediation(answers_basename=answers_file_path.name),
                console=console,
            )
        )
        raise Exit(1) from None
    if report.update_readiness.blockers:
        console.print(error_panel("\n".join(report.update_readiness.blockers), console=console))
        raise Exit(1) from None

    answers_file_for_worker = str(answers_file_path.resolve().relative_to(project_dir_obj.resolve()))
    copier_options = _build_copier_options(
        project_dir=project_dir_obj,
        answers_file_for_worker=answers_file_for_worker,
        template_path=template_path_obj,
        vcs_ref=vcs_ref,
        trusted=trust or (report.template.src_path == UPSTREAM_TEMPLATE and template_path_obj is None),
        conflict=conflict,
    )

    next_steps = [
        "Review the updated files",
        "Resolve any conflicts if they occurred",
        "Test your project to ensure everything works",
        "Commit the changes",
    ]
    if report.extensions.active and not skip_extensions:
        next_steps.append("Run repoman extensions sync after committing the base update")
    steps_text = format_next_steps(next_steps, console=console)

    if effective_dry_run:
        copier_options_serializable: dict[str, object] = {k: v for k, v in copier_options.items() if v is not None}
        if not skip_extensions:
            copier_options_serializable["extensions"] = {"extension_count": len(report.extensions.active)}
        console.print(
            dry_run_update(
                project_dir_obj,
                answers_file_path,
                template_path_obj,
                vcs_ref,
                copier_options_serializable,
                steps_text,
                _console=console,
            )
        )
        return

    try:
        mirror = load_answers(answers_file_path).get(MIRROR_KEY)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Updating project...", total=None)
            with Worker(**copier_options) as worker:  # type: ignore[arg-type]
                worker.run_update()

            if mirror is not None:
                updated_answers = load_answers(answers_file_path)
                updated_answers[MIRROR_KEY] = mirror
                serialized = yaml.safe_dump(updated_answers, sort_keys=False)
                answers_file_path.write_text(
                    "# Changes here will be overwritten by Copier.\n" + serialized, encoding="utf-8"
                )

            progress.update(task, description="Project updated successfully!")

        copier_options_serializable = {k: v for k, v in copier_options.items() if v is not None}
        console.print(
            project_updated(
                project_dir_obj,
                copier_options_serializable,
                steps_text,
                console=console,
            )
        )
    except CopierError as exc:
        message = str(exc)
        if is_cannot_obtain_old_template_references_message(message):
            body = copier_update_missing_commit_remediation(
                answers_basename=answers_file_path.name,
                preceding_error=message,
            )
        else:
            body = message
        console.print(error_panel(body, console=console))
        raise Exit(1) from exc
    except (OSError, ValueError, RuntimeError) as exc:
        console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc


def _resolve_answers_path(project_dir: Path, answers_file: str | None) -> Path:
    if answers_file is None:
        return project_dir / ".copier-answers.yml"
    return Path(answers_file).resolve()


def _build_copier_options(
    *,
    project_dir: Path,
    answers_file_for_worker: str,
    template_path: Path | None,
    vcs_ref: str | None,
    trusted: bool,
    conflict: str,
) -> dict[str, str | bool | None]:
    options: dict[str, str | bool | None] = {
        "dst_path": str(project_dir),
        "answers_file": answers_file_for_worker,
        "overwrite": True,
        "defaults": True,
        "quiet": True,
        "skip_tasks": True,
        "conflict": conflict,
        "unsafe": trusted,
        "src_path": str(template_path) if template_path is not None else None,
    }
    if vcs_ref is not None:
        options["vcs_ref"] = vcs_ref
    return options


def _print_update_plan(
    console: Any,
    report: InspectionReport,
    *,
    template_path: Path | None,
    vcs_ref: str | None,
    skip_extensions: bool,
) -> None:
    summary = Table(show_header=True, header_style="bold")
    summary.add_column("Field")
    summary.add_column("Value")
    summary.add_row("Path", report.path)
    summary.add_row("Managed", _bool_text(report.managed))
    summary.add_row("Status", report.status)
    summary.add_row("Answers file", report.answers_file.path)
    summary.add_row(
        "Template source",
        str(template_path) if template_path is not None else (report.template.src_path or "-"),
    )
    summary.add_row("Template commit", report.template.commit or "-")
    summary.add_row("Template ref", vcs_ref or report.template.vcs_ref or "-")
    summary.add_row("Extensions", "skipped" if skip_extensions else _extension_plan_text(report))
    summary.add_row("Update ready", _bool_text(report.update_readiness.ready))

    next_steps = [
        "Run repoman update once blockers are resolved",
        "Use --dry-run for Copier options preview",
        "Review and test the project after the update",
    ]
    body: list[RenderableType] = [
        Text("Plan for repoman update", style="blue"),
        summary,
    ]
    if report.update_readiness.blockers:
        body.append(
            Panel(
                Text("\n".join(report.update_readiness.blockers), style="red"),
                title="Blockers",
                border_style="red",
            )
        )
    if report.update_readiness.warnings:
        body.append(
            Panel(
                Text("\n".join(report.update_readiness.warnings), style="yellow"),
                title="Warnings",
                border_style="yellow",
            )
        )
    body.append(
        Text(
            f"Next steps:\n{format_next_steps(next_steps, console=console)}",
            style="blue",
        )
    )
    console.print(Panel(Group(*body), title="Update Plan", border_style="blue"))


def _extension_plan_text(report: InspectionReport) -> str:
    if not report.extensions.exists:
        return "none"
    if not report.extensions.active:
        return "manifest present, no active extensions"
    return ", ".join(extension.id for extension in report.extensions.active)


def _run_repair(
    *,
    console: Any,
    answers_file_path: Path,
    template_path_obj: Path | None,
    vcs_ref: str | None,
    commit: str | None,
    report: InspectionReport,
) -> None:
    if not answers_file_path.exists():
        console.print(error_panel(copier_answers_not_found_for_update(answers_file_path), console=console))
        raise Exit(1) from None
    if report.answers_file.within_project is False:
        console.print(error_panel(answers_file_must_live_in_project(answers_file_path), console=console))
        raise Exit(1) from None
    if commit is None or not commit.strip():
        console.print(error_panel(repair_requires_commit(), console=console))
        raise Exit(1) from None

    try:
        answers = load_answers(answers_file_path)
    except yaml.YAMLError as exc:
        console.print(error_panel(invalid_yaml(exc), console=console))
        raise Exit(1) from exc

    selected_template_source = str(template_path_obj) if template_path_obj is not None else report.template.src_path
    if not selected_template_source:
        console.print(error_panel(repair_requires_template_source(), console=console))
        raise Exit(1) from None

    changes: list[str] = []
    if answers.get("_src_path") != selected_template_source:
        answers["_src_path"] = selected_template_source
        changes.append(f"_src_path: {selected_template_source}")
    clean_commit = commit.strip()
    if answers.get("_commit") != clean_commit:
        answers["_commit"] = clean_commit
        changes.append(f"_commit: {clean_commit}")
    if vcs_ref is not None and answers.get("_vcs_ref") != vcs_ref:
        answers["_vcs_ref"] = vcs_ref
        changes.append(f"_vcs_ref: {vcs_ref}")

    if changes:
        answers_file_path.write_text(yaml.safe_dump(answers, sort_keys=False), encoding="utf-8")

    if not changes:
        changes_text = "No Copier metadata changes were necessary."
    else:
        changes_text = "Updated metadata:\n" + "\n".join(f"  - {change}" for change in changes)
    console.print(
        Panel(
            Text(
                f"Repaired Copier metadata in {answers_file_path}\n\n{changes_text}",
                style="green",
            ),
            title="Success",
            border_style="green",
        )
    )


def _bool_text(value: bool) -> str:
    return "yes" if value else "no"
