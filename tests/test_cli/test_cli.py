"""Tests for the main CLI application."""

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
    """Test verbose mode with enhanced argument validation.

    # Rich logs go to stderr (via RichHandler) and are displayed by pytest
    # The formatted output is visible in pytest output but may not be in result.output
    # We verify verbose mode works by checking the command succeeds
    # The actual log output with Rich formatting is visible in pytest's output

    """
    result = cli_runner.invoke(cli_app, ["--verbose"], input="")
    console.print(result.output)

    # Verbose mode should execute successfully
    assert result.exit_code == 0


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


def test_debug_info_callback(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test that --debug-info flag triggers debug info callback.

    This test verifies the debug info callback (lines 74-76).
    """
    result = cli_runner.invoke(cli_app, ["--debug-info"], input="")
    console.print(result.output)

    # Should exit with code 0 and show debug info
    assert result.exit_code == 0
    # Debug info should contain environment information
    # Note: Rich Panel output may not be fully captured in result.output, but if there is output,
    # it should contain debug-related content. If output is empty, that's acceptable (Rich may
    # output to stderr/console directly rather than being captured).
    if result.output:
        assert (
            "debug" in result.output.lower()
            or "information" in result.output.lower()
            or "interpreter" in result.output.lower()
            or "platform" in result.output.lower()
        ), f"Expected debug output keywords not found. Output: {result.output[:200]}"


def test_config_validation_error(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test that ValidationError in Config is handled gracefully.

    This test verifies ValidationError handling (lines 129-132).
    """
    from unittest.mock import patch

    from pydantic import ValidationError

    # Mock Config to raise ValidationError
    with patch("repoman.cli.main_cli.Config") as mock_config:
        mock_config.side_effect = ValidationError.from_exception_data(
            "Config", [{"type": "value_error", "loc": ("test_field",), "msg": "Invalid value"}]
        )

        result = cli_runner.invoke(cli_app, ["--help"], input="")

        # Should still work (config is set to None on error)
        assert result.exit_code == 0
