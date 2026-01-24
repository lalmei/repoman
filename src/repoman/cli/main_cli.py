"""Repoman CLI Application Main Entry Point
------------------------
This module defines the main Typer-based CLI application for repoman. It serves as the entry point
for various subcommands related to building and managing repositories

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

import importlib
import logging
from pathlib import Path
from typing import Optional

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.text import Text

from repoman._version import debug_info, version_info
from repoman.config import Config
from repoman.utils.logging import get_logger_console
from repoman.utils.theme.theme import set_theme

cli_app = typer.Typer(
    add_completion=True, invoke_without_command=True, no_args_is_help=True
)


def _register_commands() -> None:
    """Dynamically discover and register CLI commands from modules in the cli directory.
    
    Scans all Python modules in the cli directory (excluding __init__.py and main_cli.py)
    and registers any functions that have a `.command` attribute.
    """
    logger, _ = get_logger_console()
    
    # Get the cli directory path
    cli_dir = Path(__file__).parent
    
    # Find all Python files in the cli directory
    command_modules = [
        f.stem
        for f in cli_dir.glob("*.py")
        if f.stem not in ("__init__", "main_cli")
    ]
    
    registered_commands = set()
    
    # Import and register commands from each module
    for module_name in command_modules:
        try:
            # Dynamically import the module
            module = importlib.import_module(f"repoman.cli.{module_name}")
            
            # Scan for functions with a .command attribute
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                
                # Check if it's a function and has a .command attribute
                if callable(attr) and hasattr(attr, "command"):
                    command_name = attr.command
                    
                    # Check for duplicate command names
                    if command_name in registered_commands:
                        logger.warning(
                            f"Duplicate command name '{command_name}' found in "
                            f"module '{module_name}'. Skipping registration."
                        )
                        continue
                    
                    # Register the command
                    cli_app.command(name=command_name)(attr)
                    registered_commands.add(command_name)
                    logger.debug(
                        f"Registered command '{command_name}' from module '{module_name}'"
                    )
        
        except ImportError as e:
            logger.warning(
                f"Failed to import module '{module_name}': {e}. Skipping."
            )
        except Exception as e:
            logger.warning(
                f"Error processing module '{module_name}': {e}. Skipping."
            )


# Register all commands dynamically
_register_commands()


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
        raise typer.Exit()


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
        raise typer.Exit()


@cli_app.callback(invoke_without_command=True, no_args_is_help=True)
def main(
    ctx: typer.Context,
    dry_run: Optional[bool] = typer.Option(
        False, "--dry-run", help="Show changes but do not execute them"
    ),
    verbose: Optional[bool] = typer.Option(
        False, "--verbose", "-v", help="verbose mode"
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="check model version",
        callback=_version_callback,
        is_eager=True,
    ),
    debug_info: Optional[bool] = typer.Option(
        None,
        "--debug-info",
        help="Print debug information",
        callback=_debug_info_callback,
        is_eager=True,
    ),
    theme: Optional[str] = typer.Option(
        "dark", "--theme", help="Set the theme, 'light' or 'dark' "
    ),
) -> None:
    """Welcome to repoman CLI App

    \f

    Parameters
    ----------
    ctx : typer.Context
        typer context that lives throughout model command
    verbose : Optional[bool]
        set logging to DEBUG , by default typer.Option(False, "--verbose", help="verbose mode")
        it is also saved in the ctx obj so it can be referred for other noisy output
    version : Optional[bool]
        outputs version information, by default typer.Option(None, "--version",
        help="check model version", callback=_version_callback)

    """
    logger, console = get_logger_console()

    try:
        ctx.config = Config()
        if verbose:
            logger.setLevel(logging.DEBUG)
            logger.info(Text("Setting verbose mode ON", style="orange"))
        else:
            logger.setLevel(logging.INFO)

        logger.debug(ctx.config.model_dump())
        logger.debug(Text("Configuration set", style="yellow"))
    except ValidationError as e:
        logger.error("Unable to load configuration: ")
        logger.error(
            f"Obtained the following validating Errors loading configuration: {e}\n"
        )
        ctx.config = None

    ctx.obj = {
        "verbose": verbose,
        "dry_run": dry_run,
        "theme": theme,
        "config": ctx.config,
    }
