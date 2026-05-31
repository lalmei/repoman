"""Presets and copier run options."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import yaml

from repoman.extensions import slugify
from repoman.resources import get_copier_answers_template

PRESETS: dict[str, dict] = {
    "cli": {
        "fastapi_enabled": False,
        "dataset_enabled": False,
    },
    "cpp": {
        "fastapi_enabled": False,
        "dataset_enabled": False,
        "python_package_command_line_name": "",
    },
    "docs_only": {
        "docs_only": True,
        "fastapi_enabled": False,
        "dataset_enabled": False,
        "python_package_command_line_name": "",
    },
    "library": {
        "fastapi_enabled": False,
        "dataset_enabled": False,
        "python_package_command_line_name": "",
    },
    "fastapi": {
        "fastapi_enabled": True,
        "dataset_enabled": False,
    },
}


def build_preset_data(preset_name: str, project_name: str) -> dict:
    """Build copier data from preset overrides and base defaults."""
    base = {} if preset_name == "cpp" else yaml.safe_load(get_copier_answers_template()) or {}
    overrides = PRESETS.get(preset_name, {}).copy()
    if "python_package_command_line_name" not in overrides:
        overrides["python_package_command_line_name"] = slugify(project_name)
    if preset_name == "cpp":
        cpp_name = slugify(project_name, "_")
        overrides.setdefault("project_description", "")
        overrides.setdefault("repository_provider", "github")
        overrides.setdefault("copyright_license", "MIT")
        overrides.setdefault("cpp_namespace", cpp_name)
        overrides.setdefault("cpp_library_name", cpp_name)
        overrides.setdefault("cpp_standard", "c++17")
        overrides.setdefault("cpp_build_cli", True)
        overrides.setdefault("cpp_build_examples", True)
        overrides.setdefault("cpp_build_tests", True)
        overrides.setdefault("cpp_build_python_bindings", True)
    return {**base, **overrides}


def build_copier_options(
    project_name: str,
    output_dir: Path,
    template_path: Path,
    data: dict | None,
) -> dict[str, Any]:
    """Build the options dict passed to copier.run_copy.

    Args:
        project_name: Name of the project (used for dst_path and for data['project_name'] if data).
        output_dir: Base output directory; destination will be output_dir / project_name.
        template_path: Source template path.
        data: Optional pre-filled answers; if provided, project_name is set and copier runs with data.

    Returns:
        Dict suitable for copier.run_copy (src_path, dst_path, and optionally data, answers_file, etc.).
    """
    output_dir_obj = output_dir / project_name
    if data is not None:
        data = dict(data)
        data["project_name"] = project_name
        return {
            "src_path": str(template_path),
            "dst_path": str(output_dir_obj),
            "data": data,
            "answers_file": ".copier-answers.yml",
            "overwrite": True,
            "defaults": True,
            "quiet": False,
            "unsafe": True,
        }
    return {
        "src_path": str(template_path),
        "dst_path": str(output_dir_obj),
    }
