"""CLI dry-run message panels."""

from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.json import JSON
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from repoman.cli.messages.layout import (
    layout_dry_run_command_add,
    layout_dry_run_create,
    layout_dry_run_update,
    use_layout,
)


def dry_run_create(
    project_name: str,
    output_dir: Path | str,
    template_path: Path | str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    _console: Console | None = None,
) -> Panel | Layout:
    """Build a blue dry-run Panel or Layout for project creation.

    Uses a two-panel Layout on wide terminals (console.width >= 100); falls back
    to single Panel on narrow terminals or piped output.

    Args:
        project_name: Name of the project that would be created.
        output_dir: Output directory path.
        template_path: Template path used.
        copier_options_serializable: Copier options safe for JSON serialization.
        next_steps_text: Preformatted next steps (e.g. from format_next_steps).
        _console: Rich Console; used to decide Layout vs Panel. Defaults to None.

    Returns:
        Blue-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow)::

            ╭─ Dry Run ───────────────────────────────────────────╮
            │ Would create project 'my-project' in ./out           │
            │ Using template: /path/to/template                    │
            │ Copier options: { "key": "value" }                   │
            │ Next steps:   • cd my-project                        │
            ╰─────────────────────────────────────────────────────╯

        Layout (wide): Two-panel (summary + next steps | copier options).
    """
    if use_layout(_console):
        return layout_dry_run_create(
            project_name,
            str(output_dir),
            str(template_path),
            copier_options_serializable,
            next_steps_text,
        )
    summary = Text(
        f"Would create project '{project_name}' in {output_dir}\nUsing template: {template_path}\n",
        style="blue",
    )
    return Panel(
        Group(
            summary,
            Text("Copier options:", style="blue"),
            JSON.from_data(copier_options_serializable, indent=2),
            Text(f"\nNext steps:\n{next_steps_text}", style="blue"),
        ),
        title="Dry Run",
        border_style="blue",
    )


def dry_run_update(
    project_dir: Path | str,
    answers_path: Path | str,
    template_path: Path | str | None,
    vcs_ref: str | None,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    _console: Console | None = None,
) -> Panel | Layout:
    """Build a blue dry-run Panel or Layout for project update.

    Uses a two-panel Layout on wide terminals; falls back to single Panel on narrow.

    Args:
        project_dir: Project directory path.
        answers_path: Path to answers file.
        template_path: Template path, or None if from answers file.
        vcs_ref: VCS ref if specified.
        copier_options_serializable: Copier options safe for JSON serialization.
        next_steps_text: Preformatted next steps (e.g. from format_next_steps).
        _console: Rich Console; used to decide Layout vs Panel. Defaults to None.

    Returns:
        Blue-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow): Similar to dry_run_create with update-specific fields.
        Layout (wide): Two-panel (summary + next steps | copier options).
    """
    if use_layout(_console):
        return layout_dry_run_update(
            str(project_dir),
            str(answers_path),
            str(template_path) if template_path else None,
            vcs_ref,
            copier_options_serializable,
            next_steps_text,
        )
    template_line = f"Using template: {template_path}\n" if template_path else "Template: (from answers file)\n"
    vcs_line = f"VCS ref: {vcs_ref}\n" if vcs_ref else ""
    summary = Text(
        f"Would update project in {project_dir}\nUsing answers file: {answers_path}\n{template_line}{vcs_line}",
        style="blue",
    )
    return Panel(
        Group(
            summary,
            Text("Copier options:", style="blue"),
            JSON.from_data(copier_options_serializable, indent=2),
            Text(f"\nNext steps:\n{next_steps_text}", style="blue"),
        ),
        title="Dry Run",
        border_style="blue",
    )


def dry_run_command_add(
    command_name: str,
    command_output_file: Path | str,
    test_output_file: Path | str,
    context_lines: str,
    _console: Console | None = None,
) -> Panel | Layout:
    """Build a blue dry-run Panel or Layout for generator add command.

    Uses a two-panel Layout on wide terminals; falls back to single Panel on narrow.

    Args:
        command_name: Name of the command that would be created.
        command_output_file: Path to command file.
        test_output_file: Path to test file.
        context_lines: Template context summary (e.g. command_name,
            python_package_import_name, etc.).
        _console: Rich Console; used to decide Layout vs Panel. Defaults to None.

    Returns:
        Blue-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow)::

            ╭─ Dry Run ───────────────────────────────────────────╮
            │ Would create command 'mycmd':                        │
            │ Command: src/pkg/cli/commands/mycmd/__init__.py      │
            │ Test: tests/test_cli/test_mycmd.py                   │
            │ command_name: mycmd                                  │
            ╰─────────────────────────────────────────────────────╯

        Layout (wide): Two-panel (summary + paths | template context).
    """
    summary_section = (
        f"Would create command '{command_name}':\n\nCommand: {command_output_file}\nTest: {test_output_file}"
    )
    if use_layout(_console):
        return layout_dry_run_command_add(summary_section, context_lines)
    body = Text(
        f"{summary_section}\n\n{context_lines}",
        style="blue",
    )
    return Panel(body, title="Dry Run", border_style="blue")
