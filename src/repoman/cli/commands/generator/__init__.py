"""Generator command for adding new CLI commands to repoman-generated projects."""

from typer import Typer

from repoman.cli.commands.generator.add import app as add_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="Generate new CLI commands for your project",
)


app.add_typer(add_app)
