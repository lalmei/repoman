"""Path subcommand for config - show the repoman config file path."""

from pathlib import Path
from typing import Annotated

from typer import Option, Typer

from repoman.config import get_config_file_path

app = Typer(
    add_completion=True,
    help="Show the path where repoman loads/writes config",
)


@app.callback(invoke_without_command=True)
def path(
    config_path: Annotated[
        str | None,
        Option(
            "--config",
            "-c",
            help="Override config path (default: REPOMAN_CONFIG_PATH or OS default)",
        ),
    ] = None,
) -> None:
    """Print the path where repoman loads or writes config.

    Respects REPOMAN_CONFIG_PATH and --config. The path is printed to stdout.
    """
    custom_path = Path(config_path).resolve() if config_path else None
    file_path = get_config_file_path(custom_path=custom_path)
    print(file_path)  # noqa: T201
