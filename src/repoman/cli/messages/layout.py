"""CLI layout utilities for Rich multi-panel output.

Provides helpers to build Layout-based output for wide terminals, with
fallback to single-panel output for narrow terminals or piped output.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from repoman.cli.commands.config.utils import ValidationReport

from rich.console import Console
from rich.json import JSON
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text


def use_layout(console: Console | None, min_width: int = 100) -> bool:
    """Return True when Layout should be used instead of single-panel output.

    Uses Layout when the console is wide enough; otherwise falls back to
    single-panel layout to avoid cramped output.

    Args:
        console: The Rich Console instance, or None.
        min_width: Minimum console width (in characters) to use Layout.
            Defaults to 100.

    Returns:
        True if Layout should be used; False for single-panel fallback.
    """
    if console is None:
        return False
    width = getattr(console, "width", None)
    if width is None or width < min_width:
        return False
    return True


def _make_two_panel_layout(
    left_content: Any,
    right_content: Any,
    *,
    left_title: str = "Summary",
    right_title: str = "Details",
    left_style: str = "green",
    right_style: str = "green",
) -> Layout:
    """Build a two-panel horizontal Layout.

    Args:
        left_content: Rich renderable for the left panel.
        right_content: Rich renderable for the right panel.
        left_title: Panel title for the left side.
        right_title: Panel title for the right side.
        left_style: Border style for the left panel.
        right_style: Border style for the right panel.

    Returns:
        A Layout with two side-by-side panels.
    """
    layout = Layout()

    left_panel = Panel(left_content, title=left_title, border_style=left_style)
    right_panel = Panel(right_content, title=right_title, border_style=right_style)

    layout.split_row(
        Layout(left_panel, name="left", ratio=1),
        Layout(right_panel, name="right", ratio=1, minimum_size=40),
    )
    return layout


def layout_project_created(
    project_name: str,
    output_dir: str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    console: Console | None,
    *,
    use_unicode: bool,
) -> Layout:
    """Build a two-panel Layout for project creation success.

    Returns:
        Layout with summary + next steps (left) and copier options JSON (right).

    Examples:
        Layout (wide terminal)::

            ╭─ Success — Summary & Next Steps ───╮ ╭─ Copier Options ──────╮
            │ ✓ Project 'my-project' created    │ │ { "src_path": ... }   │
            │   in ./out                         │ │ { "dst_path": ... }   │
            │ Next steps:                        │ │                       │
            │   • cd my-project                  │ │                       │
            ╰────────────────────────────────────╯ ╰───────────────────────╯
    """
    prefix = "✓ " if use_unicode else ""
    summary = Text(
        f"{prefix}Project '{project_name}' created successfully in {output_dir}\n\nNext steps:\n{next_steps_text}",
        style="green",
    )
    json_content = JSON.from_data(copier_options_serializable, indent=2)
    return _make_two_panel_layout(
        summary,
        json_content,
        left_title="Success — Summary & Next Steps",
        right_title="Copier Options",
        left_style="green",
        right_style="green",
    )


def layout_project_updated(
    project_dir: str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
    console: Console | None,
    *,
    use_unicode: bool,
) -> Layout:
    """Build a two-panel Layout for project update success.

    Returns:
        Layout with summary + next steps (left) and copier options JSON (right).
    """
    prefix = "✓ " if use_unicode else ""
    summary = Text(
        f"{prefix}Project updated successfully in {project_dir}\n\nNext steps:\n{next_steps_text}",
        style="green",
    )
    json_content = JSON.from_data(copier_options_serializable, indent=2)
    return _make_two_panel_layout(
        summary,
        json_content,
        left_title="Success — Summary & Next Steps",
        right_title="Copier Options",
        left_style="green",
        right_style="green",
    )


def layout_dry_run_create(
    project_name: str,
    output_dir: str,
    template_path: str,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
) -> Layout:
    """Build a two-panel Layout for create dry-run.

    Returns:
        Layout with summary + next steps (left) and copier options JSON (right).
    """
    summary = Text(
        f"Would create project '{project_name}' in {output_dir}\n"
        f"Using template: {template_path}\n\n"
        f"Next steps:\n{next_steps_text}",
        style="blue",
    )
    json_content = JSON.from_data(copier_options_serializable, indent=2)
    return _make_two_panel_layout(
        summary,
        json_content,
        left_title="Dry Run — Summary & Next Steps",
        right_title="Copier Options",
        left_style="blue",
        right_style="blue",
    )


def layout_dry_run_update(
    project_dir: str,
    answers_path: str,
    template_path: str | None,
    vcs_ref: str | None,
    copier_options_serializable: dict[str, Any],
    next_steps_text: str,
) -> Layout:
    """Build a two-panel Layout for update dry-run.

    Returns:
        Layout with summary + next steps (left) and copier options JSON (right).
    """
    template_line = f"Using template: {template_path}\n" if template_path else "Template: (from answers file)\n"
    vcs_line = f"VCS ref: {vcs_ref}\n" if vcs_ref else ""
    summary = Text(
        f"Would update project in {project_dir}\n"
        f"Using answers file: {answers_path}\n"
        f"{template_line}{vcs_line}\n"
        f"Next steps:\n{next_steps_text}",
        style="blue",
    )
    json_content = JSON.from_data(copier_options_serializable, indent=2)
    return _make_two_panel_layout(
        summary,
        json_content,
        left_title="Dry Run — Summary & Next Steps",
        right_title="Copier Options",
        left_style="blue",
        right_style="blue",
    )


def layout_validation_failed(report: "ValidationReport") -> tuple[Layout, int]:
    """Build a three-column Layout for config validate failure.

    Args:
        report: ValidationReport with missing_keys, extra_keys, type_errors.

    Returns:
        (Layout, height): Layout with Missing Keys (left), Extra Keys (center),
        Type Errors (right), and its height in lines (for console.print(..., height=...)).

    Examples:
        Layout (wide terminal)::

            ╭─ Missing Keys ────────╮ ╭─ Extra Keys ───╮ ╭─ Type Errors ───────────╮
            │   • project_name     │ │   • debug_mode │ │   • project_name: ...   │
            │   • ci_provider      │ │                │ │   • ci: not in choices  │
            ╰──────────────────────╯ ╰────────────────╯ ╰─────────────────────────╯
    """
    missing_text = Text(
        "\n".join(f"  • {k}" for k in report.missing_keys) if report.missing_keys else "  (none)",
        style="red",
    )
    extra_text = Text(
        "\n".join(f"  • {k}" for k in report.extra_keys) if report.extra_keys else "  (none)",
        style="red",
    )
    type_errors_text = Text(
        "\n".join(f"  • {e}" for e in report.type_errors) if report.type_errors else "  (none)",
        style="red",
    )

    # Height = panel top border + content lines + panel bottom border.
    # Rich Layout defaults to full terminal height; fix size so there's no extra whitespace.
    content_lines = max(
        len(report.missing_keys) or 1,
        len(report.extra_keys) or 1,
        len(report.type_errors) or 1,
    )
    row_height = 2 + content_lines

    row_layout = Layout()
    row_layout.split_row(
        Layout(
            Panel(missing_text, title="Missing Keys", border_style="red"),
            name="missing",
            ratio=1,
            minimum_size=20,
        ),
        Layout(
            Panel(extra_text, title="Extra Keys", border_style="red"),
            name="extra",
            ratio=1,
            minimum_size=20,
        ),
        Layout(
            Panel(type_errors_text, title="Type Errors", border_style="red"),
            name="type_errors",
            ratio=1,
            minimum_size=25,
        ),
    )
    root = Layout()
    root.split_column(Layout(row_layout, name="row", size=row_height))
    return root, row_height


def layout_command_created(
    summary_section: str,
    next_steps_section: str,
    *,
    use_unicode: bool,
) -> Layout:
    """Build a two-panel Layout for command creation success.

    Args:
        summary_section: Summary + created files for left panel.
        next_steps_section: Next steps for right panel.
        use_unicode: Whether to use Unicode prefix (✓) in summary.

    Returns:
        Layout with Created Files (left) and Next Steps (right).
    """
    prefix = "✓ " if use_unicode else ""
    left_content = Text(f"{prefix}{summary_section}", style="green")
    right_content = Text(next_steps_section, style="green")
    return _make_two_panel_layout(
        left_content,
        right_content,
        left_title="Success — Created Files",
        right_title="Next Steps",
        left_style="green",
        right_style="green",
    )


def layout_config_show_template(raw_yaml: str, key_count: int) -> tuple[Layout, int]:
    """Build a Layout for config show full template: summary header + YAML content.

    Args:
        raw_yaml: Raw YAML string of template answers.
        key_count: Number of keys in the template.

    Returns:
        (Layout, height): Layout with header (top) and YAML syntax panel (bottom),
        and its height in lines (for console.print(..., height=...)).

    Examples:
        Layout (wide terminal, top header + bottom YAML panel)::

            ╭──────────────────────────────────────────────────╮
            │ Template answers (12 keys)                        │
            ╰──────────────────────────────────────────────────╯
            ╭──────────────────────────────────────────────────╮
            │ project_name: my-awesome-project                  │
            │ ci: github                                        │
            │ ...                                               │
            ╰──────────────────────────────────────────────────╯
    """
    from rich.syntax import Syntax

    header_text = Text(f"Template answers ({key_count} keys)", style="bold")
    header = Panel(header_text, border_style="bright_blue")
    syntax = Syntax(raw_yaml, "yaml", line_numbers=False)
    content_panel = Panel(syntax, border_style="bright_blue")
    # Fix content height so layout doesn't fill terminal (no trailing whitespace).
    yaml_lines = len(raw_yaml.splitlines()) or 1
    content_height = 2 + yaml_lines
    total_height = 3 + content_height  # header size=3 + content panel
    layout = Layout()
    layout.split_column(
        Layout(header, name="header", size=3),
        Layout(content_panel, name="content", size=content_height),
    )
    return layout, total_height


def layout_dry_run_command_add(
    summary_section: str,
    context_section: str,
) -> Layout:
    """Build a two-panel Layout for generator add dry-run.

    Args:
        summary_section: Summary + command/test paths for left panel.
        context_section: Template context for right panel.

    Returns:
        Layout with Summary (left) and Template Context (right).
    """
    left_content = Text(summary_section, style="blue")
    right_content = Text(context_section, style="blue")
    return _make_two_panel_layout(
        left_content,
        right_content,
        left_title="Dry Run — Summary",
        right_title="Template Context",
        left_style="blue",
        right_style="blue",
    )
