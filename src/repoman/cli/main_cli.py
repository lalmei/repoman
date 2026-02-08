"""Repoman CLI Application Main Entry Point.

This module defines the main Typer-based CLI application for repoman. It serves as the entry point
for various subcommands related to building and managing repositories.

Features:
- Uses `Typer` for CLI structure and command dispatch.
- Employs `pydantic-settings` for configuration management.
- Integrates with `Rich` for improved terminal output formatting and theming.
- Displays version and debug information.
- Supports subcommands like

Behavior:
- When run with no arguments, displays help.
- Common options include verbosity, dry-run simulation, theme selection, and version/debug flags.

Example usage:

    python -m repoman.cli --version
    python -m repoman.cli --debug-info

Dependencies:
- typer
- pydantic
- pydantic-settings
- rich
"""

import logging
from pathlib import Path

from pydantic import ValidationError
from rich.console import Console
from rich.text import Text
from typer import Context, Exit, Option, Typer

from repoman._version import debug_info, version_info
from repoman.cli.register_commands import _register_commands
from repoman.config import Config
from repoman.utils.logging import get_logger_console
from repoman.utils.theme.theme import set_theme

cli_app = Typer(add_completion=True, invoke_without_command=True, no_args_is_help=True)


# Register all commands dynamically
_register_commands(cli_app)


def _version_callback(value: bool) -> None:
    """Print model version information.

    Parameters
    ----------
    value: bool
        Whether to print version information
    """
    if value:
        console = Console(theme=set_theme("dark"))
        console.print(
            version_info(),
        )
        raise Exit(0)


def _debug_info_callback(value: bool) -> None:
    """Print debug information.

    Parameters
    ----------
    value: bool
        Whether to print debug information
    """
    if value:
        console = Console(theme=set_theme("dark"))
        debug_info(console)
        raise Exit(0)


@cli_app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    ctx: Context,
    dry_run: bool | None = Option(False, "--dry-run", help="Show changes but do not execute them"),
    verbose: bool | None = Option(False, "--verbose", "-v", help="verbose mode"),
    version: bool | None = Option(
        None,
        "--version",
        help="check model version",
        callback=_version_callback,
        is_eager=True,
    ),
    debug_info: bool | None = Option(
        None,
        "--debug-info",
        help="Print debug information",
        callback=_debug_info_callback,
        is_eager=True,
    ),
    theme: str | None = Option("dark", "--theme", help="Set the theme, 'light' or 'dark' "),
    config_path: str | None = Option(
        None,
        "--config",
        "-c",
        envvar="REPOMAN_CONFIG_PATH",
        help="Path to repoman config JSON",
    ),
) -> None:
    r"""Welcome to repoman CLI App."""
    logger, _console = get_logger_console()

    config: Config | None = None
    try:
        config = Config.load(custom_path=Path(config_path) if config_path else None)
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.info(Text("Setting verbose mode ON", style="orange"))
        else:
            logger.setLevel(logging.INFO)

        logger.debug(config.model_dump())
        logger.debug(Text("Configuration set", style="yellow"))
    except ValidationError:
        logger.exception("Unable to load configuration: ")
        logger.exception("Obtained the following validating Errors loading configuration")
        config = None

    ctx.obj = {
        "verbose": verbose,
        "dry_run": dry_run,
        "theme": theme,
        "config": config,
    }
