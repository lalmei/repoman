"""Shared Rich console helpers for CLI output."""

import os
import sys

from rich.console import Console

from repoman.utils.ui.theme.theme import set_theme

_console_cache: list[Console | None] = [None]


def _is_running_in_pytest() -> bool:
    """Check if code is running inside pytest.

    Returns:
        True if running in pytest, False otherwise
    """
    # Check for pytest in sys.modules or environment variable
    # Also check if we're being imported during pytest collection
    return (
        "pytest" in sys.modules
        or "PYTEST_CURRENT_TEST" in os.environ
        or any("pytest" in str(arg) for arg in sys.argv if isinstance(arg, str))
    )


def get_console() -> Console:
    """Return the process-wide Rich console used by CLI rendering."""
    console = _console_cache[0]

    if console is not None:
        if _is_running_in_pytest():
            console.file = sys.stdout
        return console

    if _is_running_in_pytest():
        # Use a console that outputs plain text (no colors/formatting)
        # Write to stdout instead of stderr so CliRunner can capture it
        console = Console(
            file=sys.stdout,
            force_terminal=False,
            legacy_windows=False,
            no_color=True,
        )
    else:
        console = Console(theme=set_theme("dark"))

    _console_cache[0] = console
    return console
