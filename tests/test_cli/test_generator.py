"""Tests for generator command group."""

# ruff: noqa: D103

from pathlib import Path
from unittest.mock import patch

import yaml
from typer import Typer
from typer.testing import CliRunner

from repoman.copier.extension_lifecycle import ExtensionLifecycleError


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

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "generator" in result.output.lower()


def test_generator_add_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["generator", "add", "--help"], input="")

    assert result.exit_code == 0
    assert "COMMAND_NAME" in result.output or "command_name" in result.output
    assert "--project-dir" in result.output
    assert "--kind" in result.output


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


def test_generator_add_rejects_unknown_kind(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    result = cli_runner.invoke(
        cli_app,
        [
            "generator",
            "add",
            "--project-dir",
            str(project_dir),
            "--kind",
            "unknown",
            "foo",
        ],
        input="",
    )
    assert result.exit_code == 1


def test_generator_add_graphrag_requires_singleton_name(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    result = cli_runner.invoke(
        cli_app,
        [
            "generator",
            "add",
            "--project-dir",
            str(project_dir),
            "--kind",
            "graphrag",
            "foo",
        ],
        input="",
    )
    assert result.exit_code == 1


def test_generator_add_graphrag_dry_run_dispatch(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    project_answers = yaml.safe_load((project_dir / ".copier-answers.yml").read_text())
    project_answers["rag_enabled"] = True
    (project_dir / ".copier-answers.yml").write_text(yaml.safe_dump(project_answers, sort_keys=False))
    expected_command = project_dir / "src" / "test_package" / "cli" / "commands" / "graphrag" / "__init__.py"
    expected_test = project_dir / "tests" / "test_cli" / "test_graphrag.py"

    with patch("repoman.cli.commands.generator.add.create_graphrag_extension") as mock_create:
        mock_create.return_value = (
            object(),
            {"answers_file": str(project_dir / ".repoman" / "extensions" / "graphrag" / "graphrag.answers.yml")},
            expected_command,
            expected_test,
        )
        result = cli_runner.invoke(
            cli_app,
            [
                "generator",
                "add",
                "--project-dir",
                str(project_dir),
                "--kind",
                "graphrag",
                "--dry-run",
                "graphrag",
            ],
            input="",
        )

    assert result.exit_code == 0
    mock_create.assert_called_once()


def test_generator_add_graphrag_success(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    project_answers = yaml.safe_load((project_dir / ".copier-answers.yml").read_text())
    project_answers["rag_enabled"] = True
    (project_dir / ".copier-answers.yml").write_text(yaml.safe_dump(project_answers, sort_keys=False))
    expected_command = project_dir / "src" / "test_package" / "cli" / "commands" / "graphrag" / "__init__.py"
    expected_test = project_dir / "tests" / "test_cli" / "test_graphrag.py"

    with patch("repoman.cli.commands.generator.add.create_graphrag_extension") as mock_create:
        mock_create.return_value = (
            object(),
            {"answers_file": str(project_dir / ".repoman" / "extensions" / "graphrag" / "graphrag.answers.yml")},
            expected_command,
            expected_test,
        )
        result = cli_runner.invoke(
            cli_app,
            [
                "generator",
                "add",
                "--project-dir",
                str(project_dir),
                "--kind",
                "graphrag",
                "graphrag",
            ],
            input="",
        )

    assert result.exit_code == 0


def test_generator_add_graphrag_fails_when_rag_disabled(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    project_dir = _create_project(tmp_path)
    result = cli_runner.invoke(
        cli_app,
        [
            "generator",
            "add",
            "--project-dir",
            str(project_dir),
            "--kind",
            "graphrag",
            "graphrag",
        ],
        input="",
    )
    assert result.exit_code == 1
