"""Extensions lifecycle command group."""

from typer import Typer

from repoman.cli.commands.extensions.sync import app as sync_app

app = Typer(add_completion=True, no_args_is_help=True, help="Manage project extensions")

app.add_typer(sync_app, name="sync")
