"""Utilities for instantiating templates in tests.

See docs/development/testing.md#test-utilities-reference for full reference.
"""

import contextlib
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import yaml
from copier import run_copy
from copier.errors import CopierError

from repoman.utils.logging import get_logger_console

logger, console = get_logger_console(__name__)


def _slugify(value: str, separator: str = "-") -> str:
    """Slugify a string (convert to URL-friendly format).

    Args:
        value: String to slugify
        separator: Separator character (default: "-")

    Returns:
        Slugified string
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", separator, value).strip("-_")


def _run_ruff_format(project_dir: Path) -> None:
    """Run ruff format on src/ and tests/ in project_dir if ruff is available."""
    ruff_config = project_dir / "config" / "ruff.toml"
    if not ruff_config.exists():
        return
    uv_path = shutil.which("uv")
    if not uv_path:
        return
    with contextlib.suppress(FileNotFoundError, subprocess.TimeoutExpired):
        subprocess.run(  # noqa: S603
            [uv_path, "run", "ruff", "format", "src/", "tests/", f"--config={ruff_config}"],
            cwd=project_dir,
            capture_output=True,
            check=False,
            timeout=120,
        )


def instantiate_template(
    output_dir: Path,
    template_path: Path | None = None,
    project_name: str = "test-project",
    copier_data: dict | None = None,
    answers_file: Path | None = None,
    *,
    force: bool = True,
) -> Path:
    """Instantiate a template in the specified directory.

    Args:
        output_dir: Directory where the template should be instantiated
        template_path: Path to the template. If None, uses the main template
        project_name: Name of the project to create
        copier_data: Additional copier data to pass. Merged with defaults and answers file
        answers_file: Path to a .copier-answers.yml file. If provided, loads answers from file
        force: Whether to overwrite existing files

    Returns:
        Path to the instantiated project directory

    Raises:
        CopierError: If template instantiation fails
        ValueError: If template_path doesn't exist
        FileNotFoundError: If answers_file is provided but doesn't exist
    """
    # Resolve template path (default to main template directory)
    if template_path is None:
        current_file = Path(__file__)
        template_path = current_file.parent.parent / "src" / "repoman" / "main_template"
        logger.info(f"Using main template at {template_path}")

    template_path = Path(template_path).resolve()
    if not template_path.exists():
        raise ValueError(f"Template path does not exist: {template_path}")

    # Prepare output directory
    project_dir = Path(output_dir) / project_name
    project_dir = project_dir.resolve()

    # Load answers from file if provided
    answers_data = {}
    if answers_file is not None:
        answers_file_path = Path(answers_file).resolve()
        if not answers_file_path.exists():
            raise FileNotFoundError(f"Answers file not found: {answers_file_path}")
        logger.info(f"Loading answers from {answers_file_path}")
        with open(answers_file_path) as f:
            answers_data = yaml.safe_load(f) or {}
        # Always override project_name with function parameter (function parameter takes precedence)
        answers_data["project_name"] = project_name

    # Compute derived package names (matching copier.yml defaults)
    python_package_distribution_name = _slugify(project_name, separator="-")
    python_package_import_name = _slugify(project_name, separator="_")
    python_package_command_line_name = _slugify(project_name, separator="-")

    # Prepare default copier data
    default_data = {
        "project_name": project_name,
        "python_package_distribution_name": python_package_distribution_name,
        "python_package_import_name": python_package_import_name,
        "python_package_command_line_name": python_package_command_line_name,
        "repository_provider": "github",
        "repository_namespace": "testuser",
        "repository_name": python_package_distribution_name,
        "ci": "github",
        "author_username": "testuser",
        "author_fullname": "Test User",
        "author_email": "test@example.com",
        "project_description": f"Test project {project_name}",
        "copyright_license": "MIT",
        "copyright_holder": "Test User",
        "copyright_holder_email": "test@example.com",
        "copyright_date": "2025",
        "insiders": False,
        "public_release": False,
        "python_notebooks": False,
    }

    # Merge answers file data first (if provided), then provided copier_data (highest priority)
    if answers_data:
        default_data.update(answers_data)
    if copier_data:
        default_data.update(copier_data)

    # Prepare copier options
    copier_options: dict[str, str | dict | bool] = {
        "src_path": str(template_path),
        "dst_path": str(project_dir),
        "overwrite": force,
        "quiet": True,
        "data": default_data,
        "unsafe": True,  # Template uses _jinja_extensions; _tasks (e.g. git init) run when using package root (repoman create)
    }

    # Add answers_file to copier options if provided
    # For run_copy, answers_file specifies where Copier will SAVE the answers file
    # (we've already loaded the data and passed it via the 'data' parameter)
    # Copier requires answers_file to be relative to dst_path (project_dir)
    if answers_file is not None:
        # For initial creation, we just tell Copier to save answers in the standard location
        # The actual data comes from the 'data' parameter we already set
        copier_options["answers_file"] = ".copier-answers.yml"

    try:
        logger.info(f"Instantiating template from {template_path} to {project_dir}")
        run_copy(**copier_options)
        logger.info(f"Template instantiated successfully at {project_dir}")
        console.print(f"[green]✓[/green] Template instantiated at {project_dir}")
        # Format generated Python so instantiated project passes make format-check
        _run_ruff_format(project_dir)
    except CopierError as e:
        error_msg = f"Failed to instantiate template: {e}"
        logger.exception(error_msg)
        console.print(f"[red]✗[/red] {error_msg}")
        raise
    else:
        return project_dir


def cleanup_project_artifacts(project_dir: Path) -> None:
    """Remove all build artifacts, caches, and generated files from a project directory.

    This function removes:
    - Virtual environments (.venv/)
    - Build directories (dist/, build/, *.egg-info/)
    - Cache directories (__pycache__/, .pytest_cache/, .mypy_cache/, .ipynb_checkpoints/)
    - Documentation artifacts (site/)

    Args:
        project_dir: Path to the project directory to clean up
    """
    project_dir = Path(project_dir).resolve()

    if not project_dir.exists():
        logger.warning(f"Project directory does not exist: {project_dir}")
        return

    logger.info(f"Cleaning up artifacts in {project_dir}")

    # Virtual environments
    venv_dir = project_dir / ".venv"
    if venv_dir.exists():
        logger.debug(f"Removing virtual environment: {venv_dir}")
        shutil.rmtree(venv_dir, ignore_errors=True)

    # Build artifacts
    build_dirs = ["dist", "build", "site"]
    for dir_name in build_dirs:
        build_dir = project_dir / dir_name
        if build_dir.exists():
            logger.debug(f"Removing build directory: {build_dir}")
            shutil.rmtree(build_dir, ignore_errors=True)

    # Find and remove *.egg-info directories
    for egg_info in project_dir.glob("*.egg-info"):
        if egg_info.is_dir():
            logger.debug(f"Removing egg-info directory: {egg_info}")
            shutil.rmtree(egg_info, ignore_errors=True)

    # Cache directories - need recursive search
    cache_patterns = [
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ipynb_checkpoints",
    ]

    for pattern in cache_patterns:
        for cache_dir in project_dir.rglob(pattern):
            if cache_dir.is_dir():
                logger.debug(f"Removing cache directory: {cache_dir}")
                shutil.rmtree(cache_dir, ignore_errors=True)

    logger.info(f"Cleanup completed for {project_dir}")
