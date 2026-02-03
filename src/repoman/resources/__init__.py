"""Bundled resources for repoman (e.g. copier answers template)."""

from __future__ import annotations

from importlib.resources import files


def get_copier_answers_template() -> str:
    """Return the bundled copier answers template as a string.

    Uses importlib.resources so it works when repoman is installed as a package.
    """
    return (files("repoman") / "resources" / "copier_answers_template.yml").read_text(
        encoding="utf-8"
    )
