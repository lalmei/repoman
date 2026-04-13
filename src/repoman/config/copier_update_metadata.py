"""Predicates for Copier metadata in answers files (update vs copy)."""

from __future__ import annotations

from typing import Any


def missing_commit_for_copier_update(answers: dict[str, Any]) -> bool:
    """Return True if answers have a template source but no usable ``_commit``.

    Copier's update path needs ``_src_path`` and ``_commit`` in ``.copier-answers.yml``
    to resolve the previous template revision. When ``_src_path`` is set but
    ``_commit`` is missing or blank, ``Worker.run_update()`` fails.

    Args:
        answers: Loaded YAML mapping (e.g. from ``load_answers``).

    Returns:
        True when ``_src_path`` is a non-empty string and ``_commit`` is absent,
        None, or blank (after strip for strings). False when ``_src_path`` is
        missing or not a non-empty string.
    """
    src = answers.get("_src_path")
    if not isinstance(src, str) or not src.strip():
        return False
    commit = answers.get("_commit")
    if commit is None:
        return True
    if isinstance(commit, str):
        return not commit.strip()
    return False
