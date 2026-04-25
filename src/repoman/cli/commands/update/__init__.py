"""Update command for updating repositories from templates."""

from __future__ import annotations

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
from typer import Argument, Context, Exit, Option, Typer

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
    project_dir_not_found,
    project_path_not_directory,
    project_updated,
    repair_requires_commit,
    repair_requires_template_source,
    template_path_does_not_exist,
    update_modes_mutually_exclusive,
)
from repoman.config import load_answers
from repoman.copier import ExtensionLifecycleError, sync_extensions
from repoman.inspection import InspectionError, InspectionReport, inspect_repository
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
)


@app.callback(invoke_without_command=True)
def update(
    ctx: Context,
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
    force: bool = Option(False, "--force", "-f", help="Force overwrite without asking"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be updated without making changes"),
    plan: bool = Option(False, "--plan", help="Show an update plan without writing files"),
    repair: bool = Option(False, "--repair", help="Repair Copier metadata in the answers file"),
    commit: str | None = Option(None, "--commit", help="Copier commit to write when using --repair"),
    conflict: str = Option("inline", "--conflict", help="Conflict resolution mode: 'inline' or 'rej'"),
    skip_extensions: bool = Option(False, "--skip-extensions", help="Skip syncing Copier-managed extensions"),
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
    logger, console = get_logger_console()

    effective_dry_run = dry_run or (ctx.obj or {}).get("dry_run", False)
    if conflict not in ["inline", "rej"]:
        console.print(error_panel(invalid_conflict_mode(conflict), console=console))
        raise Exit(1) from None
    if len([mode for mode in (plan, effective_dry_run, repair) if mode]) > 1:
        console.print(error_panel(update_modes_mutually_exclusive(), console=console))
        raise Exit(1) from None

    project_dir_obj = _resolve_project_dir(Path(project_dir).resolve(), console)
    answers_file_path = _resolve_answers_path(project_dir_obj, answers_file)
    template_path_obj = _resolve_template_path(template_path, logger, console)

    try:
        report = inspect_repository(
            project_dir_obj,
            answers_file=answers_file_path,
            skip_extensions=skip_extensions,
        )
    except InspectionError as exc:
        console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc

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
    if report.fatal:
        console.print(error_panel("\n".join(report.update_readiness.blockers), console=console))
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
        force=force,
        conflict=conflict,
    )

    next_steps = [
        "Review the updated files",
        "Resolve any conflicts if they occurred",
        "Test your project to ensure everything works",
        "Commit the changes",
    ]
    steps_text = format_next_steps(next_steps, console=console)

    if effective_dry_run:
        extension_dry_run_options: dict[str, str | bool | None | int] | None = None
        if not skip_extensions:
            try:
                extension_result = sync_extensions(
                    project_dir=project_dir_obj,
                    force=force,
                    conflict=conflict,
                    dry_run=True,
                )
                extension_dry_run_options = {
                    "extension_count": len(extension_result.synced),
                }
            except ExtensionLifecycleError as exc:
                console.print(error_panel(str(exc), console=console))
                raise Exit(1) from exc

        copier_options_serializable: dict[str, object] = {k: v for k, v in copier_options.items() if v is not None}
        if extension_dry_run_options is not None:
            copier_options_serializable["extensions"] = extension_dry_run_options
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
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Updating project...", total=None)
            with Worker(**copier_options) as worker:  # type: ignore[arg-type]
                worker.run_update()

            if not skip_extensions:
                sync_extensions(
                    project_dir=project_dir_obj,
                    force=force,
                    conflict=conflict,
                    dry_run=False,
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
    except ExtensionLifecycleError as exc:
        console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc
    except (OSError, ValueError, RuntimeError) as exc:
        console.print(error_panel(str(exc), console=console))
        raise Exit(1) from exc


def _resolve_project_dir(project_dir: Path, console: Any) -> Path:
    if not project_dir.exists():
        console.print(error_panel(project_dir_not_found(project_dir), console=console))
        raise Exit(1) from None
    if not project_dir.is_dir():
        console.print(error_panel(project_path_not_directory(project_dir), console=console))
        raise Exit(1) from None
    return project_dir


def _resolve_answers_path(project_dir: Path, answers_file: str | None) -> Path:
    if answers_file is None:
        return project_dir / ".copier-answers.yml"
    return Path(answers_file).resolve()


def _resolve_template_path(template_path: str | None, logger: Any, console: Any) -> Path | None:
    if template_path is None:
        logger.info("Template path will be read from .copier-answers.yml")
        return None
    template_path_obj = Path(template_path).resolve()
    if not template_path_obj.exists():
        console.print(error_panel(template_path_does_not_exist(template_path_obj), console=console))
        raise Exit(1) from None
    logger.info(f"Using custom template at {template_path_obj}")
    return template_path_obj


def _build_copier_options(
    *,
    project_dir: Path,
    answers_file_for_worker: str,
    template_path: Path | None,
    vcs_ref: str | None,
    force: bool,
    conflict: str,
) -> dict[str, str | bool | None]:
    options: dict[str, str | bool | None] = {
        "dst_path": str(project_dir),
        "answers_file": answers_file_for_worker,
        "overwrite": force,
        "quiet": True,
        "conflict": conflict,
        "unsafe": True,
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

    with open(answers_file_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(answers, handle, sort_keys=False)

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
