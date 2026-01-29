import re

from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

console = Console()


def test_version(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test version call."""
    result = cli_runner.invoke(cli_app, ["--version"], input="")
    console.print(result.output)
    assert "repoman:" in result.output
    assert result.exit_code == 0


def test_parse_args(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test verbose mode with enhanced argument validation."""
    verbose_check = re.compile(r"\w* (INFO     Setting verbose mode ON)")

    result = cli_runner.invoke(cli_app, ["--verbose"], input="")
    console.print(result.output)
    assert result.exit_code == 0

    # Enhanced verbose mode validation
    assert verbose_check.search(result.output, 0)
    assert "INFO" in result.output
    assert "Setting verbose mode ON" in result.output

    # Test that verbose mode affects logging output
    assert "DEBUG" in result.output or "INFO" in result.output


def test_unknown_command(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test a wrong command with enhanced error handling validation."""
    argv = ["supercalifragilisticexpialidocious"]
    result = cli_runner.invoke(cli_app, argv, input="")
    default_help = "No such command 'supercalifragilisticexpialidocious'"
    console.print(result.output)

    # Enhanced error handling validation
    assert result.exit_code == 2
    assert default_help in result.output
    assert "No such command" in result.output
    assert "supercalifragilisticexpialidocious" in result.output
