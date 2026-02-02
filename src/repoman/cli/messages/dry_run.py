"""CLI dry-run message panels."""

from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.json import JSON
from rich.panel import Panel
from rich.text import Text


def dry_run_create(
    project_name: str,
    output_dir: Path | str,
    template_path: Path | str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    _console: Console | None = None,
) -> Panel:
    """Build a blue dry-run Panel for project creation.

    Parameters
    ----------
    project_name : str
        Name of the project that would be created.
    output_dir : Path | str
        Output directory path.
    template_path : Path | str
        Template path used.
    copier_options_serializable : dict
        Copier options safe for JSON serialization.
    next_steps_text : str
        Preformatted next steps (e.g. from format_next_steps).
    _console : Console | None
        Reserved for API consistency with other message helpers; unused.

    Returns:
    -------
    Panel
        Blue-bordered Panel suitable for console.print().
    """
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
) -> Panel:
    """Build a blue dry-run Panel for project update.

    Parameters
    ----------
    project_dir : Path | str
        Project directory path.
    answers_path : Path | str
        Path to answers file.
    template_path : Path | str | None
        Template path, or None if from answers file.
    vcs_ref : str | None
        VCS ref if specified.
    copier_options_serializable : dict
        Copier options safe for JSON serialization.
    next_steps_text : str
        Preformatted next steps (e.g. from format_next_steps).
    _console : Console | None
        Reserved for API consistency with other message helpers; unused.

    Returns:
    -------
    Panel
        Blue-bordered Panel suitable for console.print().
    """
    template_line = (
        f"Using template: {template_path}\n"
        if template_path
        else "Template: (from answers file)\n"
    )
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
) -> Panel:
    """Build a blue dry-run Panel for generator add command.

    Parameters
    ----------
    command_name : str
        Name of the command that would be created.
    command_output_file : Path | str
        Path to command file.
    test_output_file : Path | str
        Path to test file.
    context_lines : str
        Template context summary (e.g. command_name, python_package_import_name, etc.).
    _console : Console | None
        Reserved for API consistency with other message helpers; unused.

    Returns:
    -------
    Panel
        Blue-bordered Panel suitable for console.print().
    """
    body = Text(
        f"Would create command '{command_name}':\n\n"
        f"Command: {command_output_file}\n"
        f"Test: {test_output_file}\n\n"
        f"{context_lines}",
        style="blue",
    )
    return Panel(body, title="Dry Run", border_style="blue")
