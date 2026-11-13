"""Template identity and release provenance."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_TEMPLATE = "https://github.com/lalmei/repoman.git"


def is_bundled_template(path: Path) -> bool:
    """Check whether the template comes from this installed package."""
    return path.resolve() in {PACKAGE_ROOT, PACKAGE_ROOT / "cpp_template"}


def record_release_source(answers_file: Path, template_path: Path) -> None:
    """Associate the bundled Python template with the commit that built the wheel."""
    revision_file = PACKAGE_ROOT / "resources" / "template_revision.txt"
    if template_path.resolve() != PACKAGE_ROOT or not revision_file.is_file():
        return

    revision = revision_file.read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError(f"Invalid bundled template revision: {revision}")

    answers = yaml.safe_load(answers_file.read_text(encoding="utf-8"))
    if "_commit" not in answers:
        answers["_src_path"] = UPSTREAM_TEMPLATE
        answers["_commit"] = revision
        answers_file.write_text(yaml.safe_dump(answers, sort_keys=False), encoding="utf-8")
