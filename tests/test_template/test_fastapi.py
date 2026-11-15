"""Startup smoke tests for generated FastAPI projects."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from copier import run_copy

from repoman.copier import build_copier_options, build_preset_data


@pytest.mark.parametrize("include_health_endpoints", [True, False], ids=["health-enabled", "health-disabled"])
def test_generated_fastapi_starts(tmp_path: Path, *, include_health_endpoints: bool) -> None:
    """Run the generated FastAPI tests for each health endpoint setting."""
    project_name = "test-project"
    template = Path(__file__).resolve().parents[2] / "src" / "repoman"
    answers = build_preset_data("fastapi", project_name)
    answers.update(
        include_health_endpoints=include_health_endpoints,
        fastapi_api_prefix="/generated",
    )
    options = build_copier_options(project_name, tmp_path, template, answers, trusted=True)
    run_copy(**options, quiet=True, skip_tasks=True)

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
            "tests/test_app",
        ],
        cwd=tmp_path / project_name,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
