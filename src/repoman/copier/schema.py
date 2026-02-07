"""Loading prompt schema from copier.yml."""

from __future__ import annotations

from pathlib import Path

import yaml

# Repoman package root (where copier.yml lives when template_path is None)
_REPOMAN_ROOT = Path(__file__).resolve().parent.parent


def load_prompt_schema(template_path: Path | None = None) -> dict:
    """Load prompt schema from a copier.yml (keys and type info).

    Args:
        template_path: Directory containing copier.yml. If None, use repoman package root.

    Returns:
        Dict mapping prompt key -> schema entry (type, help, default, when, etc.).
        Only includes top-level keys that are not copier meta (do not start with _).
    """
    root = template_path if template_path is not None else _REPOMAN_ROOT
    copier_path = root / "copier.yml"
    if not copier_path.exists():
        return {}
    with open(copier_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: v for k, v in data.items() if isinstance(v, dict) and not k.startswith("_")}
