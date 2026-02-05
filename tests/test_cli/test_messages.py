"""Tests for CLI message helpers (capability, dry_run, success)."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console
from rich.layout import Layout

from repoman.cli.messages import (
    answers_file_not_found,
    file_exists_use_force,
    invalid_yaml,
    project_dir_not_found,
    schema_not_found,
    schema_not_found_skipping_validation,
    unknown_format,
)
from repoman.cli.messages import success as success_messages
from repoman.cli.messages.capability import supports_unicode_markdown
from repoman.cli.messages.dry_run import (
    dry_run_command_add,
    dry_run_create,
    dry_run_update,
)
from repoman.cli.messages.layout import use_layout
from repoman.cli.messages.success import (
    command_created,
    format_next_steps,
    project_created,
    project_updated,
)

# --- layout ---


def test_use_layout_none_console() -> None:
    """use_layout with None console returns False."""
    assert use_layout(None) is False


def test_use_layout_narrow_console() -> None:
    """use_layout with width < min_width returns False."""
    console = MagicMock(spec=Console)
    console.width = 80
    assert use_layout(console, min_width=100) is False


def test_use_layout_wide_console() -> None:
    """use_layout with width >= min_width returns True."""
    console = MagicMock(spec=Console)
    console.width = 120
    assert use_layout(console, min_width=100) is True


def test_use_layout_width_none() -> None:
    """use_layout when console width is None returns False."""
    console = MagicMock(spec=Console)
    console.width = None
    assert use_layout(console) is False


def test_project_created_returns_layout_when_wide(tmp_path: Path) -> None:
    """project_created returns Layout when console is wide enough."""
    console = MagicMock(spec=Console)
    console.width = 120
    console.encoding = "utf-8"
    console.legacy_windows = False
    console.is_terminal = True
    result = project_created(
        "p",
        tmp_path / "out",
        {"key": "val"},
        "  • step",
        console=console,
    )

    assert isinstance(result, Layout)


# --- capability ---


def test_supports_unicode_markdown_none() -> None:
    """None console returns False."""
    assert supports_unicode_markdown(None) is False


def test_supports_unicode_markdown_non_utf_encoding() -> None:
    """Console with non-UTF encoding returns False."""
    console = MagicMock(spec=Console)
    console.encoding = "ascii"
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_encoding_object_non_utf() -> None:
    """Console with encoding object whose name is not UTF returns False."""

    class NonUtfEncoding:
        name = "cp1252"

    console = MagicMock(spec=Console)
    console.encoding = NonUtfEncoding()
    console.legacy_windows = False
    console.is_terminal = True
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_encoding_raises_type_error() -> None:
    """Console whose encoding.name raises TypeError returns False."""

    class BadEncoding:
        @property
        def name(self) -> str:
            raise TypeError("encoding.name not available")

    console = MagicMock(spec=Console)
    console.encoding = BadEncoding()
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_encoding_object_empty_name() -> None:
    """Console with encoding object and empty name returns False (not utf)."""
    console = MagicMock(spec=Console)
    console.encoding = MagicMock()
    console.encoding.name = ""
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_legacy_windows() -> None:
    """Console with legacy_windows True returns False."""
    console = MagicMock(spec=Console)
    console.encoding = "utf-8"
    console.legacy_windows = True
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_not_terminal() -> None:
    """Console with is_terminal False returns False."""
    console = MagicMock(spec=Console)
    console.encoding = "utf-8"
    console.legacy_windows = False
    console.is_terminal = False
    assert supports_unicode_markdown(console) is False


def test_supports_unicode_markdown_utf_and_terminal() -> None:
    """Console with UTF encoding and terminal returns True."""
    console = MagicMock(spec=Console)
    console.encoding = "utf-8"
    console.legacy_windows = False
    console.is_terminal = True
    assert supports_unicode_markdown(console) is True


def test_supports_unicode_markdown_encoding_defaults_to_terminal_true() -> None:
    """Console without is_terminal attribute defaults to True (terminal)."""
    console = MagicMock(spec=Console)
    console.encoding = "utf-8"
    console.legacy_windows = False
    del console.is_terminal
    assert supports_unicode_markdown(console) is True


# --- dry_run ---


def test_dry_run_create_returns_panel(tmp_path: Path) -> None:
    """dry_run_create returns a Panel with expected content."""
    panel = dry_run_create(
        "proj",
        tmp_path / "out",
        tmp_path / "tmpl",
        {"key": "value"},
        "next steps",
        _console=None,
    )
    assert panel.title == "Dry Run"
    assert panel.border_style == "blue"


def test_dry_run_update_with_template_path_none(tmp_path: Path) -> None:
    """dry_run_update with template_path None returns Panel (uses 'from answers file' branch)."""
    panel = dry_run_update(
        tmp_path / "proj",
        tmp_path / "answers.yml",
        None,
        None,
        {},
        "steps",
        _console=None,
    )
    assert panel.title == "Dry Run"
    assert panel.border_style == "blue"


def test_dry_run_update_with_vcs_ref(tmp_path: Path) -> None:
    """dry_run_update with vcs_ref returns Panel (covers vcs_line branch)."""
    panel = dry_run_update(
        tmp_path / "proj",
        tmp_path / "a.yml",
        tmp_path / "t",
        "v1.0",
        {},
        "steps",
        _console=None,
    )
    assert panel.title == "Dry Run"
    assert panel.border_style == "blue"


def test_dry_run_command_add_returns_panel(tmp_path: Path) -> None:
    """dry_run_command_add returns a Panel with command name and paths."""
    panel = dry_run_command_add(
        "mycmd",
        tmp_path / "cmd.py",
        tmp_path / "test_cmd.py",
        "context",
        _console=None,
    )
    assert panel.title == "Dry Run"
    assert "mycmd" in str(panel.renderable)


# --- success ---


def test_format_next_steps_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_next_steps with unicode support uses bullet."""
    monkeypatch.setattr(success_messages, "supports_unicode_markdown", lambda c: True)
    out = format_next_steps(["a", "b"], console=Console())
    assert "•" in out
    assert "a" in out
    assert "b" in out


def test_format_next_steps_no_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
    """format_next_steps without unicode support uses numbered lines."""
    monkeypatch.setattr(success_messages, "supports_unicode_markdown", lambda c: False)
    out = format_next_steps(["a", "b"], console=Console())
    assert "1." in out or "2." in out
    assert "a" in out
    assert "b" in out


def test_command_created_with_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
    """command_created with unicode support adds prefix."""
    monkeypatch.setattr(success_messages, "supports_unicode_markdown", lambda c: True)
    panel = command_created("cmd", "body", console=Console())
    assert panel.title == "Success"
    assert "✓" in str(panel.renderable) or "body" in str(panel.renderable)


def test_command_created_without_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
    """command_created without unicode uses plain body."""
    monkeypatch.setattr(success_messages, "supports_unicode_markdown", lambda c: False)
    panel = command_created("cmd", "body text", console=Console())
    assert panel.title == "Success"
    assert "body text" in str(panel.renderable)


def test_project_created_returns_panel(tmp_path: Path) -> None:
    """project_created returns a green Panel."""
    panel = project_created("p", tmp_path / "out", {}, "steps", console=Console())
    assert panel.title == "Success"
    assert panel.border_style == "green"


def test_project_updated_returns_panel(tmp_path: Path) -> None:
    """project_updated returns a green Panel."""
    panel = project_updated(tmp_path / "out", {}, "steps", console=Console())
    assert panel.title == "Success"
    assert panel.border_style == "green"


# --- error_text (message string helpers) ---


def test_answers_file_not_found() -> None:
    """answers_file_not_found includes path and 'not found'."""
    msg = answers_file_not_found("/path/to/answers.yml")
    assert "not found" in msg.lower()
    assert "/path/to/answers.yml" in msg


def test_schema_not_found() -> None:
    """schema_not_found mentions schema/copier."""
    msg = schema_not_found()
    assert "schema" in msg.lower()
    assert "copier" in msg.lower()


def test_schema_not_found_skipping_validation() -> None:
    """schema_not_found_skipping_validation mentions skipping."""
    msg = schema_not_found_skipping_validation()
    assert "skipping" in msg.lower()


def test_project_dir_not_found(tmp_path: Path) -> None:
    """project_dir_not_found includes path."""
    msg = project_dir_not_found(tmp_path / "proj")
    assert "not exist" in msg.lower() or "not found" in msg.lower()
    assert "proj" in msg


def test_file_exists_use_force(tmp_path: Path) -> None:
    """file_exists_use_force includes path and --force."""
    msg = file_exists_use_force(tmp_path / "file.yml")
    assert "already exists" in msg.lower() or "exists" in msg.lower()
    assert "force" in msg.lower()


def test_unknown_format() -> None:
    """unknown_format includes format and allowed options."""
    msg = unknown_format("xml")
    assert "xml" in msg
    assert "table" in msg or "json" in msg


def test_invalid_yaml() -> None:
    """invalid_yaml includes the error detail."""
    msg = invalid_yaml("parse error at line 1")
    assert "yaml" in msg.lower()
    assert "parse error" in msg.lower()
