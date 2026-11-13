"""Extensions lifecycle command group."""

from typer import Typer

from repoman.cli.commands.extensions.sync import app as sync_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="""Manage project extensions.

Examples:

    repoman extensions sync ./my-project
    repoman extensions sync --dry-run ./my-project
    repoman extensions sync --type command --name my_cmd ./my-project
""",
)

app.add_typer(sync_app, name="sync")
