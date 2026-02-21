"""Loading answers from YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


def load_answers(path: Path | None = None) -> dict[str, Any]:
    """Load answers from a YAML file.

    Args:
        path: Path to the answers file (e.g. .copier-answers.yml).

    Returns:
        Dictionary of answers (empty dict if file is empty).

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if path is None or not path.exists():
        raise FileNotFoundError(f"Answers file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
