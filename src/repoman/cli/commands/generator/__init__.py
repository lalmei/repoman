"""Generator command for adding new CLI commands to repoman-generated projects."""

from typer import Typer

from repoman.cli.commands.generator.add import app as add_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="""Generate new CLI commands or feature extensions for a repoman-generated project.

Examples:

    repoman generator add fetch-data --project-dir ./my-app
    repoman generator add my-rag --kind graphrag -d ./my-app
    repoman generator add my-cmd --dry-run
""",
)


app.add_typer(add_app)
