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
    layout_command_created,
    layout_project_created,
    layout_project_updated,
    use_layout,
)


def format_next_steps(steps: list[str], console: Console | None = None) -> str:
    r"""Format a list of next steps as a single string for use in panels.

    When the console supports Unicode, uses bullet "•"; otherwise uses
    numbered lines "  1. step", "  2. step", ...

    Args:
        steps: List of step description strings.
        console: Rich Console; when supported, uses Unicode bullet.
            Defaults to None.

    Returns:
        Formatted steps string.

    Examples:
        With Unicode: "  • cd my-project\\n  • make install"
        Without Unicode: "  1. cd my-project\\n  2. make install"
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
) -> Union[Panel, Layout]:
    """Build a green success Panel or Layout for project creation.

    Uses a two-panel Layout on wide terminals (console.width >= 100); falls back
    to single Panel on narrow terminals or piped output.

    Args:
        project_name: Name of the created project.
        output_dir: Output directory path.
        copier_options_serializable: Copier options safe for JSON serialization.
        next_steps_text: Preformatted next steps (e.g. from format_next_steps).
        console: Rich Console; when supported, summary may include Unicode (✓).
            Defaults to None.

    Returns:
        Green-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow terminal)::

            ╭─ Success ────────────────────────────────────────────╮
            │ ✓ Project 'my-project' created successfully in ./out │
            │ Copier options used:                                 │
            │ { "key": "value" }                                   │
            │ Next steps:                                          │
            │   • cd my-project                                    │
            ╰─────────────────────────────────────────────────────╯

        Layout (wide terminal, two panels side-by-side)::

            ╭─ Success — Summary & Next Steps ───╮ ╭─ Copier Options ──────╮
            │ ✓ Project 'my-project' created in  │ │ { "src_path": ... }   │
            │   ./out                            │ │                       │
            │ Next steps:                        │ │                       │
            │   • cd my-project                  │ │                       │
            ╰────────────────────────────────────╯ ╰───────────────────────╯
    """
    use_unicode = supports_unicode_markdown(console)
    if use_layout(console):
        return layout_project_created(
            project_name,
            str(output_dir),
            copier_options_serializable,
            next_steps_text,
            console,
            use_unicode=use_unicode,
        )
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
) -> Union[Panel, Layout]:
    """Build a green success Panel or Layout for project update.

    Uses a two-panel Layout on wide terminals; falls back to single Panel on narrow.

    Args:
        project_dir: Project directory path.
        copier_options_serializable: Copier options safe for JSON serialization.
        next_steps_text: Preformatted next steps (e.g. from format_next_steps).
        console: Rich Console; when supported, summary may include Unicode (✓).
            Defaults to None.

    Returns:
        Green-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow): Same structure as project_created.
        Layout (wide): Two-panel (summary + next steps | copier options).
    """
    use_unicode = supports_unicode_markdown(console)
    if use_layout(console):
        return layout_project_updated(
            str(project_dir),
            copier_options_serializable,
            next_steps_text,
            console,
            use_unicode=use_unicode,
        )
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


def command_created(
    _command_name: str,
    body_text: str,
    console: Console | None = None,
    *,
    summary_section: str | None = None,
    next_steps_section: str | None = None,
) -> Union[Panel, Layout]:
    """Build a green success Panel or Layout for command creation (generator add, config init).

    When summary_section and next_steps_section are provided and use_layout(console),
    returns a two-panel Layout; otherwise returns a single Panel from body_text.

    Args:
        _command_name: Name of the created command (kept for API consistency;
            body_text carries the message).
        body_text: Full body (created files, next steps, etc.) for Panel fallback.
        console: Rich Console; when supported, may include Unicode (✓).
            Defaults to None.
        summary_section: Optional. Summary + created files for Layout left panel.
        next_steps_section: Optional. Next steps for Layout right panel.

    Returns:
        Green-bordered Panel or Layout suitable for console.print().

    Examples:
        Panel (narrow or no summary_section/next_steps_section)::

            ╭─ Success ─────────────────────────────╮
            │ ✓ Command 'mycmd' created             │
            │ Created files: ...                    │
            │ Next steps: ...                       │
            ╰───────────────────────────────────────╯

        Layout (wide, with summary_section and next_steps_section)::

            ╭─ Success — Created Files ─────╮ ╭─ Next Steps ─────────────────╮
            │ ✓ Command 'mycmd' created     │ │   • Review and customize     │
            │ Created files:                │ │   • Implement functionality  │
            │   - src/pkg/cli/.../mycmd/    │ │                              │
            ╰───────────────────────────────╯ ╰──────────────────────────────╯
    """
    use_unicode = supports_unicode_markdown(console)
    if use_layout(console) and summary_section is not None and next_steps_section is not None:
        return layout_command_created(
            summary_section,
            next_steps_section,
            use_unicode=use_unicode,
        )
    prefix = "✓ " if use_unicode else ""
    content = Text(f"{prefix}{body_text}", style="green") if prefix else Text(body_text, style="green")
    return Panel(content, title="Success", border_style="green")
