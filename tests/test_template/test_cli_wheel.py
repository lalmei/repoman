"""Smoke test the console script installed from a generated wheel."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from copier import run_copy

from repoman.copier import build_copier_options, build_preset_data


def _run(command: list[str], cwd: Path) -> str:
    """Run a command without importing packages from the caller's Python path."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    result = subprocess.run(  # noqa: S603 - Commands use known executables and test paths
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, f"{command}\n{result.stdout}\n{result.stderr}"
    return result.stdout.strip()


def test_generated_cli_wheel_version(tmp_path: Path) -> None:
    """Install the wheel in a fresh environment and compare CLI and metadata versions."""
    project_name = "wheel-smoke"
    distribution_name = "example-wheel-dist"
    import_name = "example_wheel_package"
    template = Path(__file__).resolve().parents[2] / "src" / "repoman"
    answers = build_preset_data("cli", project_name)
    answers.update(
        python_package_distribution_name=distribution_name,
        python_package_import_name=import_name,
    )
    options = build_copier_options(project_name, tmp_path, template, answers, trusted=True)
    run_copy(**options, quiet=True, skip_tasks=True)

    uv = shutil.which("uv")
    assert uv is not None, "uv is required to build and install generated wheels"
    wheel_dir = tmp_path / "wheels"
    _run([uv, "build", "--wheel", "--python", sys.executable, "--out-dir", str(wheel_dir)], tmp_path / project_name)
    (wheel,) = wheel_dir.glob("*.whl")

    venv = tmp_path / "installed"
    _run([uv, "venv", "--python", sys.executable, str(venv)], tmp_path)
    scripts = venv / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    python = str(scripts / f"python{suffix}")
    _run([uv, "pip", "install", "--python", python, str(wheel)], tmp_path)

    wheel_version = _run(
        [
            python,
            "-I",
            "-c",
            "import sys; from importlib.metadata import version; print(version(sys.argv[1]))",
            distribution_name,
        ],
        tmp_path,
    )
    reported_version = _run([str(scripts / f"{project_name}{suffix}"), "--version"], tmp_path)
    assert reported_version == f"{import_name}: {wheel_version}"
