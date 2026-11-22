"""Exercise the opt-in research scaffold through project creation and wheel installation."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer import Typer
from typer.testing import CliRunner


def test_plain_cli_omits_pipeline(tmp_path: Path, cli_runner: CliRunner, cli_app: Typer) -> None:
    """Ordinary CLI projects omit the example, command and corresponding test."""
    result = cli_runner.invoke(cli_app, ["create", "cli", "cli", "plain-cli", "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output
    project = tmp_path / "plain-cli"
    assert not (project / "research-pipeline-example").exists()
    assert not (project / "src/plain_cli/research_pipeline.py").exists()
    assert not (project / "src/plain_cli/cli/commands/run").exists()
    assert not (project / "tests/test_research_pipeline.py").exists()


def test_pipeline_from_installed_wheel(
    tmp_path: Path, cli_runner: CliRunner, cli_app: Typer, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Build the opt-in project, run its installed command, and exercise its generated tests."""
    result = cli_runner.invoke(
        cli_app, ["create", "cli", "cli", "pipeline-demo", "--research-pipeline", "-o", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    project = tmp_path / "pipeline-demo"
    example = project / "research-pipeline-example"
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.delenv("PYTHONHOME", raising=False)
    uv = shutil.which("uv")
    assert uv is not None

    def run(args: list[str], cwd: Path) -> str:
        completed = subprocess.run(  # noqa: S603 - Arguments are test-owned executables and paths.
            [uv, *args], cwd=cwd, capture_output=True, text=True, check=False, timeout=120
        )
        assert completed.returncode == 0, f"{completed.stdout}\n{completed.stderr}"
        return completed.stdout.strip()

    wheel_dir = tmp_path / "wheels"
    run(["build", "--wheel", "--python", sys.executable, "--out-dir", str(wheel_dir)], project)
    (wheel,) = wheel_dir.glob("*.whl")
    installed = [
        "run",
        "--isolated",
        "--no-project",
        "--python",
        sys.executable,
        "--with",
        str(wheel),
        "--with",
        "pytest",
    ]
    attempt = Path(run([*installed, "pipeline-demo", "run", "-c", str(example / "run.json")], tmp_path))
    assert attempt.parent == example / "runs"
    assert json.loads((attempt / "summary.json").read_text()) == {"lines": 3, "words": 6}

    # The generated test config adds src/ to sys.path. Exercise the installed wheel here.
    config = tmp_path / "pytest.ini"
    config.write_text("[pytest]\n")
    run(
        [
            *installed,
            "python",
            "-I",
            "-m",
            "pytest",
            "-c",
            str(config),
            "--import-mode=importlib",
            str(project / "tests/test_research_pipeline.py"),
        ],
        tmp_path,
    )
