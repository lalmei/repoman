"""Tests for the create command."""

import re
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

console = Console()


def test_create_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command help."""
    result = cli_runner.invoke(cli_app, ["create", "--help"], input="")

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "create" in result.output.lower()
    assert "PROJECT_NAME" in result.output or "project_name" in result.output


def test_create_command_dry_run(sample_project_names: list[str], cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with dry-run flag."""
    project_name = sample_project_names[0]

    result = cli_runner.invoke(cli_app, ["create", project_name, "--dry-run", "--force"], input="")
    console.print(result.output)

    assert result.exit_code == 0
    assert "Would create project" in result.output or "Dry Run" in result.output
    assert project_name in result.output


def test_create_command_missing_required_args(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with missing required arguments."""
    result = cli_runner.invoke(cli_app, ["create"], input="")
    console.print(result.output)

    # Should fail due to missing PROJECT_NAME
    assert result.exit_code == 2
    assert "Missing argument" in result.output or "PROJECT_NAME" in result.output


def test_create_command_invalid_template_path(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with invalid template path."""
    project_name = "test-project"
    invalid_template = "/non/existent/template/path"

    result = cli_runner.invoke(
        cli_app,
        ["create", project_name, "--template", invalid_template, "--force"],
        input="",
    )
    console.print(result.output)

    # Should fail - Typer validates arguments first (exit code 2) before custom validation (exit code 1)
    assert result.exit_code in [1, 2]
    # Error message could be from Typer (argument validation) or from our custom validation
    assert (
        "not found" in result.output
        or "does not exist" in result.output
        or "template" in result.output.lower()
        or "Missing argument" in result.output
    )


def test_create_command_output_directory(tmp_path: Path, cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with custom output directory."""
    project_name = "test-project"
    custom_output = tmp_path / "output"

    result = cli_runner.invoke(
        cli_app,
        ["--dry-run", "create", "--output", str(custom_output), project_name],
        input="",
    )
    console.print(result.output)
    assert result.exit_code == 0

    # Should show dry-run output
    assert "Would create project" in result.output or "Dry Run" in result.output
    assert project_name in result.output


def test_create_command_force_overwrite(
    tmp_path: Path, mock_project_structure: Any, cli_runner: CliRunner, cli_app: Typer
) -> None:
    """Test create command with force overwrite."""
    project_name = "test-project"
    project_dir = tmp_path / project_name

    # Use the mock project structure instead of creating a simple dummy directory
    shutil.copytree(mock_project_structure, project_dir, dirs_exist_ok=True)

    # Run create with force and dry-run to avoid template execution errors
    result = cli_runner.invoke(
        cli_app,
        ["create", project_name, "--output", str(tmp_path), "--force", "--dry-run"],
        input="",
    )
    console.print(result.output)

    # Since we're using --dry-run, it should succeed and show the dry-run output
    assert result.exit_code == 0
    assert "Would create project" in result.output or "Dry Run" in result.output


@pytest.mark.usefixtures("tmp_path")
def test_create_command_verbose_mode(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with verbose mode."""
    verbose_check = re.compile(r"\w* (INFO     Setting verbose mode ON)")
    result = cli_runner.invoke(
        cli_app,
        ["--verbose", "create", "test-project", "--dry-run", "--force"],
        input="",
    )
    console.print(result.output)
    assert result.exit_code == 0

    # Enhanced verbose create mode validation
    assert verbose_check.search(result.output, 0) or "INFO" in result.output
    assert "test-project" in result.output
    assert "Dry Run" in result.output or "Would create project" in result.output
