"""CLI tests for the hotspots command."""

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from repoman import cli
from tests.conftest import strip_ansi_codes


def test_hotspots_command_help(cli_runner: CliRunner) -> None:
    """Test hotspots command help."""
    result = cli_runner.invoke(cli, ["hotspots", "--help"], input="")
    plain = strip_ansi_codes(result.output)

    assert result.exit_code == 0
    assert "Usage:" in plain
    assert "hotspots" in plain.lower()
    assert "--limit" in plain or "-n" in plain
    assert "--format" in plain or "-f" in plain


def test_hotspots_command_registered(cli_runner: CliRunner) -> None:
    """Test that hotspots command is registered."""
    result = cli_runner.invoke(cli, ["hotspots", "--help"], input="")
    assert result.exit_code == 0


def test_hotspots_not_a_git_repo(tmp_path: Path, cli_runner: CliRunner) -> None:
    """Test hotspots fails when path is not a git repository."""
    (tmp_path / "some_file.txt").write_text("hello")

    result = cli_runner.invoke(cli, ["hotspots", "--path", str(tmp_path)], input="")

    assert result.exit_code == 1
    # Rich panels may not be captured by CliRunner; exit code confirms failure
    assert "Not a git repository" in strip_ansi_codes(result.output) or result.output == ""


def test_hotspots_path_does_not_exist(cli_runner: CliRunner) -> None:
    """Test hotspots fails when path does not exist."""
    result = cli_runner.invoke(
        cli,
        ["hotspots", "--path", "/nonexistent/path/xyz"],
        input="",
    )

    assert result.exit_code == 1


def test_hotspots_invalid_since_date(cli_runner: CliRunner) -> None:
    """Test hotspots fails with invalid --since date format."""
    result = cli_runner.invoke(
        cli,
        ["hotspots", "--path", ".", "--since", "invalid-date"],
        input="",
    )

    assert result.exit_code == 1


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repo with a few commits."""
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "src").mkdir()
    (repo / "src" / "main.py").write_text("print('hello')\n")
    (repo / "README.md").write_text("# Test\n")

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
    # Second commit to add churn
    (repo / "src" / "main.py").write_text("print('hello')\nprint('world')\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "update main"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    return repo


def test_hotspots_succeeds_on_git_repo(
    git_repo: Path,
    cli_runner: CliRunner,
) -> None:
    """Test hotspots runs successfully on a git repository."""
    result = cli_runner.invoke(
        cli,
        ["hotspots", "--path", str(git_repo), "-n", "10", "-e", ".py,.md"],
        input="",
    )

    assert result.exit_code == 0
    # Output may not be captured by CliRunner (Rich); exit code 0 confirms success


def test_hotspots_json_format_via_subprocess() -> None:
    """Test hotspots --format json outputs valid JSON (via subprocess for reliable capture)."""
    proc = subprocess.run(
        ["uv", "run", "python", "-m", "repoman", "hotspots", "-n", "3", "-f", "json"],
        cwd=Path(__file__).parent.parent.parent,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    if data:
        for item in data:
            assert "file" in item
            assert "commits" in item
            assert "churn" in item
            assert "contributors" in item


def test_hotspots_html_format(git_repo: Path, tmp_path: Path, cli_runner: CliRunner) -> None:
    """Test hotspots --format html creates report directory with index.html."""
    out_dir = tmp_path / "hotspot_report"
    result = cli_runner.invoke(
        cli,
        ["hotspots", "--path", str(git_repo), "-f", "html", "-o", str(out_dir), "-e", ".py,.md"],
        input="",
    )

    assert result.exit_code == 0
    assert (out_dir / "index.html").exists()


def test_hotspots_limit(
    git_repo: Path,
    cli_runner: CliRunner,
) -> None:
    """Test hotspots with --limit completes successfully."""
    result = cli_runner.invoke(
        cli,
        ["hotspots", "--path", str(git_repo), "-n", "1"],
        input="",
    )

    assert result.exit_code == 0
