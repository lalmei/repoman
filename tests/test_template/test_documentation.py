"""Build generated documentation with each project's own ProperDocs dependencies."""

import shutil
import subprocess
from pathlib import Path

import pytest
from copier import run_copy

from tests.ci_runner import run_make_command


@pytest.mark.parametrize(
    ("template", "answers"),
    [
        pytest.param("python", {"repository_provider": "github"}, id="python-github"),
        pytest.param("python", {"repository_provider": "gitlab"}, id="python-gitlab"),
        pytest.param("python", {"repository_provider": "azure"}, id="python-azure"),
        pytest.param(
            "python",
            {"fastapi_enabled": True, "dataset_enabled": True, "python_notebooks": True},
            id="python-full",
        ),
        pytest.param("python", {"docs_only": True}, id="docs-only"),
        pytest.param("python", {"insiders": True}, id="python-insiders"),
        pytest.param("python", {"docs_only": True, "insiders": True}, id="docs-only-insiders"),
        pytest.param("cpp", {"repository_provider": "github"}, id="cpp-github"),
        pytest.param("cpp", {"repository_provider": "gitlab"}, id="cpp-gitlab"),
    ],
)
def test_generated_documentation_builds(tmp_path: Path, template: str, answers: dict[str, str | bool]) -> None:
    """Fresh projects must build strictly without coverage data or lost config files."""
    source = Path(__file__).resolve().parents[2] / "src" / "repoman"
    if template == "cpp":
        source /= "cpp_template"
    project = tmp_path / "docs-smoke"
    data = {
        "project_name": "docs-smoke",
        "project_description": "Documentation build verification",
        "author_fullname": "Test User",
        "author_email": "test@example.com",
        "author_username": "testuser",
        "repository_namespace": "testuser",
        "copyright_license": "MIT",
        "fastapi_enabled": False,
        "dataset_enabled": False,
        "python_notebooks": False,
        "latex_paper": False,
        "document_review": False,
        **answers,
    }
    run_copy(str(source), str(project), data=data, defaults=True, unsafe=True, skip_tasks=True, quiet=True)
    config = project / "config" / "properdocs.yml"
    original_config = config.read_text()
    assert not (project / "config" / "mkdocs.yml").exists()

    uv = shutil.which("uv")
    assert uv is not None
    # Isolate the docs dependencies without installing optional ML/CI tooling.
    sync = subprocess.run(  # noqa: S603 - Executable is resolved above; arguments are fixed test inputs.
        [uv, "sync", "--no-default-groups", "--group", "docs"],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert sync.returncode == 0, sync.stdout + sync.stderr
    env = {"UV_NO_SYNC": "1", "DEPLOY": "false", "MATERIAL_INSIDERS": "false", "PYTHONPATH": str(project / "src")}
    result = run_make_command(project, "docs-check", env=env, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    homepage = (project / "site" / "index.html").read_text()
    assert "<html" in homepage
    assert "ProperDocs" in homepage
    assert '{% extends "base.html" %}' not in homepage
    assert config.read_text() == original_config
    assert not (project / "config" / "index.html").exists()

    if answers.get("insiders"):
        for page in ("index.html", "installation/index.html", "changelog/index.html"):
            assert (project / "site" / "insiders" / page).is_file()
    if template == "python" and not answers.get("docs_only"):
        report = project / "htmlcov" / "index.html"
        assert "Coverage report unavailable" in report.read_text()
        assert "Coverage report unavailable" in (project / "site" / "coverage" / "covindex.html").read_text()
        report.write_text("<html><body>Existing coverage report</body></html>")
        result = run_make_command(project, "ensure-docs-coverage-report", env=env, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        assert report.read_text() == "<html><body>Existing coverage report</body></html>"
    elif answers.get("docs_only"):
        assert not (project / "htmlcov").exists()
