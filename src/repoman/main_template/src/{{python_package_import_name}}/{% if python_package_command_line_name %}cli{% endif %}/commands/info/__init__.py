"""Info command - used for testing command registration."""

import typer

app = typer.Typer(help="Show package info")


@app.callback(invoke_without_command=True)
def info() -> None:
    """Show package information."""
    pass
