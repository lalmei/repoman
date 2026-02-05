"""CLI success message utilities."""

from pathlib import Path
from typing import Any, Union

from rich.console import Console, Group
from rich.json import JSON
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

from repoman.cli.messages.capability import supports_unicode_markdown
from repoman.cli.messages.layout import (
    layout_project_created,
    layout_project_updated,
    use_layout,
)


def format_next_steps(steps: list[str], console: Console | None = None) -> str:
    """Format a list of next steps as a single string for use in panels.

    When the console supports Unicode, uses bullet "•"; otherwise uses
    numbered lines "  1. step", "  2. step", ...

    Parameters
    ----------
    steps : list[str]
        List of step description strings.
    console : Console | None
        Rich Console; when supported, uses Unicode bullet.

    Returns:
    -------
    str
        Formatted steps string.

    Example:
    -------
    With Unicode: ``"  • cd my-project\\n  • make install"``
    Without Unicode: ``"  1. cd my-project\\n  2. make install"``
    """
    use_unicode = supports_unicode_markdown(console)
    if use_unicode:
        return "\n".join(f"  • {step}" for step in steps)
    return "\n".join(f"  {i + 1}. {step}" for i, step in enumerate(steps))


def project_created(
    project_name: str,
    output_dir: Path | str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    console: Console | None = None,
) -> Panel:
    """Build a green success Panel for project creation.

    Parameters
    ----------
    project_name : str
        Name of the created project.
    output_dir : Path | str
        Output directory path.
    copier_options_serializable : dict
        Copier options safe for JSON serialization.
    next_steps_text : str
        Preformatted next steps (e.g. from format_next_steps).
    console : Console | None
        Rich Console; when supported, summary may include Unicode (✓).

    Returns:
    -------
    Panel
        Green-bordered Panel suitable for console.print().

    Example:
    -------
    When rendered (plain text; terminal uses green border)::

        ╭─ Success ────────────────────────────────────────────╮
        │ Project 'my-project' created successfully in ./out   │
        │ Copier options used:                                 │
        │ { "key": "value" }                                   │
        │ Next steps:                                          │
        │   • cd my-project                                    │
        │   • make install                                     │
        ╰─────────────────────────────────────────────────────╯
    """
    use_unicode = supports_unicode_markdown(console)
    prefix = "✓ " if use_unicode else ""
    summary = Text(
        f"{prefix}Project '{project_name}' created successfully in {output_dir}\n",
        style="green",
    )
    return Panel(
        Group(
            summary,
            Text("Copier options used:", style="green"),
            JSON.from_data(copier_options_serializable, indent=2),
            Text(f"\nNext steps:\n{next_steps_text}", style="green"),
        ),
        title="Success",
        border_style="green",
    )


def project_updated(
    project_dir: Path | str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    console: Console | None = None,
) -> Panel:
    """Build a green success Panel for project update.

    Parameters
    ----------
    project_dir : Path | str
        Project directory path.
    copier_options_serializable : dict
        Copier options safe for JSON serialization.
    next_steps_text : str
        Preformatted next steps (e.g. from format_next_steps).
    console : Console | None
        Rich Console; when supported, summary may include Unicode (✓).

    Returns:
    -------
    Panel
        Green-bordered Panel suitable for console.print().

    Example:
    -------
    When rendered (plain text; terminal uses green border)::

        ╭─ Success ────────────────────────────────────────────╮
        │ Project updated successfully in ./my-project         │
        │ Copier options used:                                 │
        │ { "key": "value" }                                   │
        │ Next steps:                                          │
        │   • make install                                     │
        ╰─────────────────────────────────────────────────────╯
    """
    use_unicode = supports_unicode_markdown(console)
    prefix = "✓ " if use_unicode else ""
    summary = Text(
        f"{prefix}Project updated successfully in {project_dir}\n",
        style="green",
    )
    return Panel(
        Group(
            summary,
            Text("Copier options used:", style="green"),
            JSON.from_data(copier_options_serializable, indent=2),
            Text(f"\nNext steps:\n{next_steps_text}", style="green"),
        ),
        title="Success",
        border_style="green",
    )


def command_created(_command_name: str, body_text: str, console: Console | None = None) -> Panel:
    """Build a green success Panel for command creation (generator add).

    Parameters
    ----------
    _command_name : str
        Name of the created command (kept for API consistency; body_text carries the message).
    body_text : str
        Full body (created files, next steps, etc.).
    console : Console | None
        Rich Console; when supported, may include Unicode (✓) in title or body.

    Returns:
    -------
    Panel
        Green-bordered Panel suitable for console.print().

    Example:
    -------
    When rendered (plain text; terminal uses green border)::

        ╭─ Success ─────────────────────────────╮
        │ Created src/pkg/cli/commands/mycmd/    │
        │ Next steps: run tests                 │
        ╰───────────────────────────────────────╯
    """
    use_unicode = supports_unicode_markdown(console)
    prefix = "✓ " if use_unicode else ""
    content = Text(f"{prefix}{body_text}", style="green") if prefix else Text(body_text, style="green")
    return Panel(content, title="Success", border_style="green")
