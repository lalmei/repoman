"""Tests for extensions command group."""

# ruff: noqa: D103

from pathlib import Path
from unittest.mock import patch

import yaml
from typer import Typer
from typer.testing import CliRunner

from repoman.copier.extension_lifecycle import ExtensionLifecycleError


def test_extensions_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["extensions", "--help"], input="")
    assert result.exit_code == 0
    assert "sync" in result.output.lower()


def test_extensions_sync_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["extensions", "sync", "--help"], input="")
    assert result.exit_code == 0
    assert "--type" in result.output


def test_extensions_sync_missing_project(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    result = cli_runner.invoke(
        cli_app,
        ["extensions", "sync", str(tmp_path / "missing")],
        input="",
    )
    assert result.exit_code == 1


def test_extensions_sync_dry_run(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / ".copier-answers.yml").write_text(yaml.safe_dump({"project_name": "x"}))

    with patch("repoman.cli.commands.extensions.sync.sync_extensions") as mock_sync:
        mock_sync.return_value.synced = []
        mock_sync.return_value.dry_run_options = []

        result = cli_runner.invoke(
            cli_app,
            ["extensions", "sync", "--dry-run", str(project_dir)],
            input="",
        )

    assert result.exit_code == 0


def test_extensions_sync_error(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with patch("repoman.cli.commands.extensions.sync.sync_extensions") as mock_sync:
        mock_sync.side_effect = ExtensionLifecycleError("boom")

        result = cli_runner.invoke(
            cli_app,
            ["extensions", "sync", str(project_dir)],
            input="",
        )

    assert result.exit_code == 1


def test_extensions_sync_with_command_type_filter(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    with patch("repoman.cli.commands.extensions.sync.sync_extensions") as mock_sync:
        mock_sync.return_value.synced = []
        mock_sync.return_value.dry_run_options = []
        result = cli_runner.invoke(
            cli_app,
            ["extensions", "sync", "--type", "command", str(project_dir)],
            input="",
        )

    assert result.exit_code == 0
    assert mock_sync.call_args.kwargs["extension_type"] == "command"
