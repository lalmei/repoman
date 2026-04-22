"""Tests for generator command group."""

# ruff: noqa: D103

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from typer import Typer
from typer.testing import CliRunner

from repoman.cli.commands.generator.add import detect_project_structure, validate_command_name
from repoman.copier.extension_lifecycle import ExtensionLifecycleError
from tests.conftest import strip_ansi_codes


def _create_project(tmp_path: Path, package_name: str = "test_package") -> Path:
    project_dir = tmp_path
    (project_dir / "src" / package_name / "cli" / "commands").mkdir(parents=True)
    (project_dir / "tests" / "test_cli").mkdir(parents=True)
    (project_dir / ".copier-answers.yml").write_text(
        yaml.safe_dump(
            {
                "python_package_import_name": package_name,
                "python_package_command_line_name": "test",
            },
            sort_keys=False,
        )
    )
    return project_dir


def test_generator_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["generator", "--help"], input="")
    plain = strip_ansi_codes(result.output)

    assert result.exit_code == 0
    assert "Usage:" in plain
    assert "generator" in plain.lower()


def test_generator_add_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["generator", "add", "--help"], input="")
    plain = strip_ansi_codes(result.output)

    assert result.exit_code == 0
    assert "COMMAND_NAME" in plain or "command_name" in plain
    assert "--project-dir" in plain


def test_generator_add_invalid_name(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(project_dir), "invalid-name"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_missing_answers_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    (tmp_path / "src" / "test_package" / "cli" / "commands").mkdir(parents=True)
    (tmp_path / "tests" / "test_cli").mkdir(parents=True)

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(tmp_path), "testcommand"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_existing_files_without_force(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    command_file = project_dir / "src" / "test_package" / "cli" / "commands" / "foo" / "__init__.py"
    command_file.parent.mkdir(parents=True, exist_ok=True)
    command_file.write_text("# existing")

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(project_dir), "foo"],
        input="",
    )

    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("command_name", "match"),
    [
        ("   ", "empty or whitespace"),
        ("../evil", "path traversal"),
        ("bad/name", "invalid character"),
        ("CON", "reserved system name"),
    ],
)
def test_validate_command_name_rejects_invalid_patterns(command_name: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        validate_command_name(command_name)


def test_detect_project_structure_requires_commands_dir(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    with pytest.raises(ValueError, match="Could not find CLI commands directory"):
        detect_project_structure(project_dir, "pkg")


def test_generator_add_missing_project_dir(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(missing), "foo"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_invalid_answers_yaml(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    (project_dir / ".copier-answers.yml").write_text("python_package_import_name: [\n", encoding="utf-8")

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(project_dir), "foo"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_missing_python_package_import_name(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path
) -> None:
    project_dir = _create_project(tmp_path)
    (project_dir / ".copier-answers.yml").write_text(
        yaml.safe_dump({"python_package_command_line_name": "test"}, sort_keys=False),
        encoding="utf-8",
    )

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(project_dir), "foo"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_existing_test_file_without_force(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    test_file = project_dir / "tests" / "test_cli" / "test_foo.py"
    test_file.write_text("# existing\n", encoding="utf-8")

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "--project-dir", str(project_dir), "foo"],
        input="",
    )

    assert result.exit_code == 1


def test_generator_add_dry_run_uses_lifecycle_engine(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    expected_command = project_dir / "src" / "test_package" / "cli" / "commands" / "foo" / "__init__.py"
    expected_test = project_dir / "tests" / "test_cli" / "test_foo.py"

    with patch("repoman.cli.commands.generator.add.create_command_extension") as mock_create:
        mock_create.return_value = (
            object(),
            {
                "answers_file": str(project_dir / ".repoman" / "extensions" / "command" / "foo.answers.yml"),
            },
            expected_command,
            expected_test,
        )

        result = cli_runner.invoke(
            cli_app,
            ["generator", "add", "--project-dir", str(project_dir), "--dry-run", "foo"],
            input="",
        )

    assert result.exit_code == 0
    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs["dry_run"] is True


def test_generator_add_success_path(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    expected_command = project_dir / "src" / "test_package" / "cli" / "commands" / "foo" / "__init__.py"
    expected_test = project_dir / "tests" / "test_cli" / "test_foo.py"

    with patch("repoman.cli.commands.generator.add.create_command_extension") as mock_create:
        mock_create.return_value = (
            object(),
            {"answers_file": str(project_dir / ".repoman" / "extensions" / "command" / "foo.answers.yml")},
            expected_command,
            expected_test,
        )

        result = cli_runner.invoke(
            cli_app,
            ["generator", "add", "--project-dir", str(project_dir), "foo"],
            input="",
        )

    assert result.exit_code == 0


def test_generator_add_handles_lifecycle_error(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)

    with patch("repoman.cli.commands.generator.add.create_command_extension") as mock_create:
        mock_create.side_effect = ExtensionLifecycleError("boom")

        result = cli_runner.invoke(
            cli_app,
            ["generator", "add", "--project-dir", str(project_dir), "foo"],
            input="",
        )

    assert result.exit_code == 1
