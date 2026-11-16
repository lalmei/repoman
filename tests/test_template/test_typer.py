"""Smoke tests for the generated Typer CLI and command extension."""

import shutil
import subprocess
import sys
from pathlib import Path

from copier import run_copy
from typer import Typer
from typer.testing import CliRunner

from repoman.copier import build_copier_options, build_preset_data


def test_generated_typer_cli(tmp_path: Path, cli_runner: CliRunner, cli_app: Typer) -> None:
    """Render a CLI project, add a command, and run the generated tests."""
    project_name = "test-project"
    project = tmp_path / project_name
    template = Path(__file__).resolve().parents[2] / "src" / "repoman"
    answers = build_preset_data("cli", project_name)
    options = build_copier_options(project_name, tmp_path, template, answers, trusted=True)
    run_copy(**options, quiet=True, skip_tasks=True)

    added = cli_runner.invoke(cli_app, ["generator", "add", "noop", "--project-dir", str(project)])
    assert added.exit_code == 0, added.output

    uv = shutil.which("uv")
    assert uv is not None, "uv is required to test generated projects"
    result = subprocess.run(  # noqa: S603 - Fixed arguments in a generated test project
        [
            uv,
            "run",
            "--python",
            sys.executable,
            "--no-default-groups",
            "--group",
            "ci",
            "pytest",
            "-c=config/pytest.ini",
            "--no-cov",
            "tests/test_cli",
            "tests/test_version.py",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
