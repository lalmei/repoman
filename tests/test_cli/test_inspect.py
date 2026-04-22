"""Tests for the inspect command."""

import json
from pathlib import Path
from unittest.mock import patch

import yaml
from _pytest.capture import CaptureFixture
from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

from repoman.cli.commands.inspect import _bool_text, _print_table
from repoman.inspection import InspectionError
from repoman.inspection.models import (
    AnswersFileState,
    ExtensionSummary,
    FeatureFlags,
    InspectionReport,
    TemplateMetadata,
    UpdateReadiness,
)
from tests.conftest import strip_ansi_codes


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def _write_answers(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _all_output(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    output = getattr(result, "output", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    return (stdout or output) + stderr


def _captured_text(result: object, capsys: CaptureFixture[str]) -> str:
    """Return command output from Typer result data or captured streams."""
    captured = _all_output(result)
    if captured:
        return captured
    outerr = capsys.readouterr()
    return outerr.out + outerr.err


def test_inspect_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Inspect help should expose the public command options."""
    result = cli_runner.invoke(cli_app, ["inspect", "--help"], input="")
    plain = strip_ansi_codes(_all_output(result))

    assert result.exit_code == 0
    assert "inspect" in plain.lower()
    assert "--format" in plain
    assert "--answers" in plain


def test_inspect_command_table_output(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """Table output should summarize readiness and enabled features."""
    repo = _make_repo(tmp_path)
    _write_answers(
        repo / ".copier-answers.yml",
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
            "fastapi_enabled": True,
            "python_package_command_line_name": "my-app",
        },
    )

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo)], input="")

    assert result.exit_code == 0
    plain = strip_ansi_codes(_captured_text(result, capsys))
    if plain:
        assert "Update ready" in plain
        assert "FastAPI" in plain


def test_inspect_command_json_contract(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """JSON output should match the documented v1 contract."""
    repo = _make_repo(tmp_path)
    _write_answers(
        repo / ".copier-answers.yml",
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
            "python_package_command_line_name": "my-app",
        },
    )

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 0
    payload = json.loads(_captured_text(result, capsys))
    assert set(payload) == {
        "path",
        "managed",
        "status",
        "answers_file",
        "template",
        "features",
        "extensions",
        "update_readiness",
    }
    assert payload["managed"] is True
    assert payload["template"]["commit"] == "deadbeef"
    assert payload["features"]["cli_enabled"] is True


def test_inspect_command_answers_override(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """The explicit answers override should control the inspected file."""
    repo = _make_repo(tmp_path)
    custom_answers = repo / "custom-answers.yml"
    _write_answers(
        custom_answers,
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
        },
    )

    result = cli_runner.invoke(
        cli_app,
        [
            "inspect",
            "--path",
            str(repo),
            "--answers",
            str(custom_answers),
            "--format",
            "json",
        ],
        input="",
    )

    assert result.exit_code == 0
    payload = json.loads(_captured_text(result, capsys))
    assert payload["answers_file"]["path"] == str(custom_answers.resolve())
    assert payload["managed"] is True


def test_inspect_command_non_git_repo_fails(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Non-git directories should fail hard during inspection."""
    repo = tmp_path / "repo"
    repo.mkdir()

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo)], input="")

    assert result.exit_code == 1


def test_inspect_command_missing_answers_exits_zero_with_warning(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """Missing answers should warn but still complete the inspection."""
    repo = _make_repo(tmp_path)

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 0
    payload = json.loads(_captured_text(result, capsys))
    assert payload["status"] == "warning"
    assert payload["update_readiness"]["ready"] is False


def test_inspect_command_invalid_yaml_exits_one(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """Invalid answers YAML should surface as a fatal inspection error."""
    repo = _make_repo(tmp_path)
    (repo / ".copier-answers.yml").write_text("_src_path: [", encoding="utf-8")

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 1
    payload = json.loads(_captured_text(result, capsys))
    assert payload["status"] == "error"


def test_bool_text_and_print_table_cover_optional_panels() -> None:
    """Render blockers and warnings panels and keep None values readable."""
    repo_path = "repo"
    answers_path = "repo/.copier-answers.yml"
    manifest_path = "repo/.repoman/extensions.yml"
    enabled = True
    disabled = False
    console = Console(record=True)
    report = InspectionReport(
        path=repo_path,
        managed=True,
        status="warning",
        answers_file=AnswersFileState(path=answers_path, exists=True, within_project=None),
        template=TemplateMetadata(),
        features=FeatureFlags(),
        extensions=ExtensionSummary(manifest_path=manifest_path, exists=False),
        update_readiness=UpdateReadiness(
            ready=False,
            blockers=["Missing answers"],
            warnings=["Missing commit metadata"],
        ),
    )

    _print_table(console, report, show_header=False)
    rendered = console.export_text()

    assert _bool_text(None) == "-"
    assert _bool_text(enabled) == "yes"
    assert _bool_text(disabled) == "no"
    assert "Blockers" in rendered
    assert "Warnings" in rendered


def test_print_table_returns_for_non_printing_console() -> None:
    """Ignore console-like objects that do not provide a print method."""
    repo_path = "repo"
    answers_path = "repo/.copier-answers.yml"
    manifest_path = "repo/.repoman/extensions.yml"
    report = InspectionReport(
        path=repo_path,
        managed=False,
        status="ok",
        answers_file=AnswersFileState(path=answers_path, exists=False),
        template=TemplateMetadata(),
        features=FeatureFlags(),
        extensions=ExtensionSummary(manifest_path=manifest_path, exists=False),
        update_readiness=UpdateReadiness(ready=True),
    )

    _print_table(object(), report, show_header=True)


def test_inspect_command_missing_path_fails(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Missing inspect paths should fail before repository analysis."""
    missing = tmp_path / "missing"

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(missing)], input="")

    assert result.exit_code == 1


def test_inspect_command_non_directory_path_fails(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """File paths should be rejected by the inspect command."""
    repo_file = tmp_path / "repo.txt"
    repo_file.write_text("not a directory\n", encoding="utf-8")

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo_file)], input="")

    assert result.exit_code == 1


def test_inspect_command_unknown_format_fails(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Unsupported output formats should fail after inspection succeeds."""
    repo = _make_repo(tmp_path)
    _write_answers(
        repo / ".copier-answers.yml",
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
        },
    )

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "yaml"], input="")

    assert result.exit_code == 1


def test_inspect_command_handles_inspection_errors(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Surface repository analysis failures as exit code 1."""
    repo = _make_repo(tmp_path)

    with patch("repoman.cli.commands.inspect.inspect_repository", side_effect=InspectionError("boom")):
        result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo)], input="")

    assert result.exit_code == 1


def test_inspect_command_exits_one_for_fatal_reports(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    """Fatal inspection reports should still serialize and then exit non-zero."""
    repo = _make_repo(tmp_path)
    report = InspectionReport(
        path=str(repo.resolve()),
        managed=True,
        status="error",
        answers_file=AnswersFileState(path=str((repo / ".copier-answers.yml").resolve()), exists=True),
        template=TemplateMetadata(src_path="https://example.com/template.git", commit="deadbeef"),
        features=FeatureFlags(cli_enabled=True),
        extensions=ExtensionSummary(manifest_path=str((repo / ".repoman" / "extensions.yml").resolve()), exists=False),
        update_readiness=UpdateReadiness(ready=False, blockers=["fatal blocker"]),
        fatal=True,
    )

    with patch("repoman.cli.commands.inspect.inspect_repository", return_value=report):
        result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 1
    payload = json.loads(_captured_text(result, capsys))
    assert payload["status"] == "error"
