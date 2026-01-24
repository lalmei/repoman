"""Repoman CLI Application Module
----------------

This module initializes the CLI for the `repoman` package using the Typer library.
It serves as the entry point for various command-line interface (CLI) commands
related to building and managing repositories.

Each command is defined in its respective module and registered via Typer to allow
for a modular and extendable CLI application.

Once installed, the `pyproject.toml` defines the entry point as

``` py  title="pyproject.toml"
[project.scripts]
repoman = "repoman:app"
```

since in the `src/repoman/__init__.py` we have the following import

```python title="repoman/__init__.py"
from repoman.cli.cli import app
```

Once installed this allows you to run the CLI directly from the command line using:
```bash
repoman [COMMAND] [OPTIONS]
```
or

```bash
uv run python -m repoman.cli [COMMAND] [OPTIONS]
```

This module is designed to be run as a script, and it will automatically
load the appropriate subcommands based on the environment and configuration.
It also provides a help message when no command is specified.


Example:
    python -m repoman.cli create my-project

Dependencies:
    - Typer: A modern library for building CLI applications, based on Click.
    - Pydantic: For data validation and settings management.
    - Rich: For rich text and beautiful formatting in the terminal.
    - Pydantic-settings: For settings management with Pydantic.

Each subcommand is defined in its own module and registered here.

Subcommands can define a default behavior through the use of a @app.callback() function. This callback is invoked when the subcommand is used without specifying a sub-subcommand.

For example, in the create command, the @app.callback() handles project creation. This enables users to run repoman create my-project directly, with optional flags like --template, --output, etc.

If we want to add sub-subcommands (such as list), we define them using the @app.command() decorator. In this case, the callback is still invoked before the sub-subcommand is executed unless invoke_without_command=True is used, allowing for flexible pre-processing or shared setup logic.

Warning:
    There may be a better pattern for this ;)

Commands:
    -
"""

from repoman.cli.main_cli import cli_app as cli

__all__: list[str] = ["cli"]
