"""Shared logic for create command and subcommands."""

import re
from pathlib import Path

import yaml
from copier import run_copy
from copier.errors import CopierError
from rich.progress import Progress, SpinnerColumn, TextColumn
from typer import Exit

from repoman.cli.messages import (
    dry_run_create,
    error_panel,
    format_next_steps,
    output_dir_exists_use_force,
    project_created,
    warning_panel,
)
from repoman.extensions import slugify
from repoman.resources import get_copier_answers_template
from repoman.utils.logging import get_logger_console

# ASCII control characters: ord < 32 (SPACE)
_CONTROL_CHAR_THRESHOLD = 32

PRESETS: dict[str, dict] = {
    "cli": {
        "fastapi_enabled": False,
        "rag_enabled": False,
        "dataset_enabled": False,
    },
    "docs_only": {
        "docs_only": True,
        "fastapi_enabled": False,
        "rag_enabled": False,
        "dataset_enabled": False,
        "python_package_command_line_name": "",
    },
    "library": {
        "fastapi_enabled": False,
        "rag_enabled": False,
        "dataset_enabled": False,
        "python_package_command_line_name": "",
    },
    "fastapi": {
        "fastapi_enabled": True,
        "rag_enabled": False,
        "dataset_enabled": False,
    },
    "rag": {
        "fastapi_enabled": True,
        "rag_enabled": True,
        "dataset_enabled": True,
    },
}


def validate_project_name(project_name: str) -> bool:
    """Validate project name for security and safety."""
    if not project_name or not project_name.strip():
        raise ValueError("Project name cannot be empty or whitespace only")

    path_traversal_patterns = [
        r"\.\./",
        r"\.\.\\",
        r"\.\.%2F",
        r"\.\.%5C",
        r"\.\.%2f",
        r"\.\.%5c",
        r"\.\.%252F",
        r"\.\.%255C",
        r"\.\.\u2215",
        r"\.\.\uFE68",
        r"\.\.\uFF0F",
        r"\.\.\uFF3C",
    ]
    for pattern in path_traversal_patterns:
        if re.search(pattern, project_name, re.IGNORECASE):
            raise ValueError(f"Project name contains path traversal pattern: {pattern}")

    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        if char in project_name:
            raise ValueError(f"Project name contains invalid character: {char}")

    if any(ord(char) < _CONTROL_CHAR_THRESHOLD for char in project_name):
        raise ValueError("Project name contains control characters")

    reserved = ["CON", "PRN", "AUX", "NUL"] + [f"COM{i}" for i in range(1, 10)] + [f"LPT{i}" for i in range(1, 10)]
    if project_name.upper() in reserved:
        raise ValueError(f"Project name is a reserved system name: {project_name}")

    return True


def build_preset_data(preset_name: str, project_name: str) -> dict:
    """Build copier data from preset overrides and base defaults."""
    base = yaml.safe_load(get_copier_answers_template()) or {}
    overrides = PRESETS.get(preset_name, {}).copy()
    if "python_package_command_line_name" not in overrides:
        overrides["python_package_command_line_name"] = slugify(project_name)
    return {**base, **overrides}


def run_create(
    project_name: str,
    output_dir: Path,
    template_path: Path,
    data: dict | None,
    force: bool,
    dry_run: bool,
) -> None:
    """Run the create flow: validate, build copier options, run copy or dry-run."""
    _logger, console = get_logger_console()

    try:
        validate_project_name(project_name)
    except ValueError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from None

    output_dir_obj = output_dir / project_name

    if output_dir_obj.exists() and not force:
        console.print(warning_panel(output_dir_exists_use_force(output_dir_obj), console=console))
        raise Exit(1) from None

    if data is not None:
        data["project_name"] = project_name
        copier_options = {
            "src_path": str(template_path),
            "dst_path": str(output_dir_obj),
            "data": data,
            "answers_file": ".copier-answers.yml",
            "overwrite": True,
            "defaults": True,
            "quiet": False,
            "unsafe": True,
        }
    else:
        copier_options = {
            "src_path": str(template_path),
            "dst_path": str(output_dir_obj),
        }

    next_steps = [
        f"cd {output_dir_obj}",
        "Review and customize the generated project",
        "Initialize git repository",
        "Start developing!",
    ]
    steps_text = format_next_steps(next_steps, console=console)

    if dry_run:
        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}
        console.print(
            dry_run_create(
                project_name,
                output_dir_obj,
                template_path,
                copier_options_serializable,
                steps_text,
                _console=console,
            )
        )
        return

    try:
        if data is not None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating project...", total=None)
                run_copy(**copier_options)  # type: ignore[arg-type]
                progress.update(task, description="Project created successfully!")
        else:
            console.print("Creating project...")
            run_copy(**copier_options)  # type: ignore[arg-type]

        copier_options_serializable = {k: str(v) if isinstance(v, Path) else v for k, v in copier_options.items()}
        console.print(
            project_created(
                project_name,
                output_dir_obj,
                copier_options_serializable,
                steps_text,
                console=console,
            )
        )
    except CopierError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
    except (OSError, ValueError, RuntimeError) as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e
