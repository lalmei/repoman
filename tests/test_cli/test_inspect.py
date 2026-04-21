"""Tests for the inspect command."""

import json
from pathlib import Path

import yaml
from _pytest.capture import CaptureFixture
from typer import Typer
from typer.testing import CliRunner

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
    captured = _all_output(result)
    if captured:
        return captured
    outerr = capsys.readouterr()
    return outerr.out + outerr.err


def test_inspect_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    result = cli_runner.invoke(cli_app, ["inspect", "--help"], input="")

    assert result.exit_code == 0
    assert "inspect" in result.output.lower()
    assert "--format" in result.output
    assert "--answers" in result.output


def test_inspect_command_table_output(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
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
    repo = tmp_path / "repo"
    repo.mkdir()

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo)], input="")

    assert result.exit_code == 1


def test_inspect_command_missing_answers_exits_zero_with_warning(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path)

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 0
    payload = json.loads(_captured_text(result, capsys))
    assert payload["status"] == "warning"
    assert payload["update_readiness"]["ready"] is False


def test_inspect_command_invalid_yaml_exits_one(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    repo = _make_repo(tmp_path)
    (repo / ".copier-answers.yml").write_text("_src_path: [", encoding="utf-8")

    result = cli_runner.invoke(cli_app, ["inspect", "--path", str(repo), "--format", "json"], input="")

    assert result.exit_code == 1
    payload = json.loads(_captured_text(result, capsys))
    assert payload["status"] == "error"
