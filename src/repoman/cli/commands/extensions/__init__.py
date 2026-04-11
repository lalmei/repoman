"""Extensions lifecycle command group."""

from typer import Typer

from repoman.cli.commands.extensions.sync import app as sync_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="""Manage project extensions.

Examples:

    repoman extensions sync ./my-project
    repoman extensions sync ./my-project --dry-run
    repoman extensions sync ./my-project --type command --name my_cmd
""",
)

app.add_typer(sync_app, name="sync")
