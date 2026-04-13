"""Config command for managing repoman/template configuration."""

from typer import Typer

from repoman.cli.commands.config.init_ import app as init_app
from repoman.cli.commands.config.list_keys import app as list_keys_app
from repoman.cli.commands.config.path_ import app as path_app
from repoman.cli.commands.config.show import app as show_app
from repoman.cli.commands.config.validate_ import app as validate_app

app = Typer(
    add_completion=True,
    no_args_is_help=True,
    help="""Manage repoman and template configuration.

Examples:

    repoman config init -o .copier-answers.yml
    repoman config show --key python_package_import_name
    repoman config validate -a .copier-answers.yml
    repoman config path
    repoman config list-keys --format json
""",
)

app.add_typer(init_app, name="init")
app.add_typer(path_app, name="path")
app.add_typer(validate_app, name="validate")
app.add_typer(show_app, name="show")
app.add_typer(list_keys_app, name="list-keys")
