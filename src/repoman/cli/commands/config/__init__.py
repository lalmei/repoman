"""Config command for managing repoman/template configuration."""

from typer import Typer

from repoman.cli.commands.config.init_ import app as init_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="Manage repoman and template configuration",
)

app.add_typer(init_app, name="init")
