"""CLI tests for the compliance command."""

import json
from pathlib import Path

from typer.testing import CliRunner

from repoman import cli


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "CONTRIBUTING.md").write_text("pull request\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\ndependencies=['typer']\n", encoding="utf-8")
    return repo


def test_compliance_command_help(cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["compliance", "--help"], input="")
    assert result.exit_code == 0
    assert "compliance" in result.output.lower()
    assert "check" in result.output.lower()
    assert "init" in result.output.lower()


def test_compliance_not_a_git_repo(tmp_path: Path, cli_runner: CliRunner) -> None:
    result = cli_runner.invoke(cli, ["compliance", "check", "--path", str(tmp_path)], input="")
    assert result.exit_code == 2


def test_compliance_init_writes_starter_file(tmp_path: Path, cli_runner: CliRunner) -> None:
    repo = _make_repo(tmp_path)
    target = repo / "compliance.yml"

    result = cli_runner.invoke(cli, ["compliance", "init", "--path", str(repo)], input="")

    assert result.exit_code == 0
    assert target.exists()
    assert "soc2-software" in target.read_text(encoding="utf-8")


def test_compliance_check_json_output(cli_runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    result = cli_runner.invoke(
        cli,
        ["compliance", "check", "--path", str(repo), "--profile", "oss-best-practices", "--format", "json"],
        input="",
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert payload[0]["profile_id"] == "oss-best-practices"


def test_compliance_check_markdown_output_file(cli_runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output = tmp_path / "compliance.md"

    result = cli_runner.invoke(
        cli,
        [
            "compliance",
            "check",
            "--path",
            str(repo),
            "--profile",
            "oss-best-practices",
            "--format",
            "markdown",
            "--output",
            str(output),
        ],
        input="",
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "Compliance Report" in output.read_text(encoding="utf-8")


def test_compliance_check_html_output_file(cli_runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output_dir = tmp_path / "html-report"

    result = cli_runner.invoke(
        cli,
        [
            "compliance",
            "check",
            "--path",
            str(repo),
            "--profile",
            "oss-best-practices",
            "--format",
            "html",
            "--output",
            str(output_dir),
        ],
        input="",
    )

    assert result.exit_code == 0
    assert (output_dir / "index.html").exists()


def test_compliance_check_tier_target_exit_code(cli_runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    result = cli_runner.invoke(
        cli,
        [
            "compliance",
            "check",
            "--path",
            str(repo),
            "--profile",
            "oss-best-practices",
            "--tier-target",
            "gold",
        ],
        input="",
    )

    assert result.exit_code == 1


def test_compliance_check_profile_filter(cli_runner: CliRunner, tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    output = tmp_path / "profile.json"

    result = cli_runner.invoke(
        cli,
        [
            "compliance",
            "check",
            "--path",
            str(repo),
            "--profile",
            "soc2-software",
            "--format",
            "json",
            "--output",
            str(output),
        ],
        input="",
    )

    assert result.exit_code in {0, 1}
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["profile_id"] == "soc2-software"
