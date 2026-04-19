"""Detectors for repository-visible compliance signals."""

from __future__ import annotations

import re
import tomllib
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from repoman.compliance.models import ControlResult, DetectorSpec, Status


def evaluate_detector(repo_path: Path, detection: DetectorSpec) -> tuple[Status, list[str]]:
    """Evaluate a detector and return (status, evidence)."""
    handlers = {
        "file_exists": _file_exists,
        "glob_exists": _glob_exists,
        "yaml_path_exists": _yaml_path_exists,
        "text_match": _text_match,
        "github_actions_rule": _github_actions_rule,
        "make_target_exists": _make_target_exists,
        "pyproject_field_exists": _pyproject_field_exists,
        "manual_only": _manual_only,
    }
    handler = handlers[detection.kind]
    return handler(repo_path, detection.params)


def detector_applies(repo_path: Path, detectors: Iterable[DetectorSpec]) -> bool:
    """Return True when all applicability detectors succeed."""
    for detector in detectors:
        status, _evidence = evaluate_detector(repo_path, detector)
        if status != "met":
            return False
    return True


def enrich_result_with_override(result: ControlResult, extra_evidence: list[str]) -> None:
    """Append extra evidence from compliance.yml."""
    for item in extra_evidence:
        if item not in result.evidence:
            result.evidence.append(item)


def _file_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params["path"])
    if path.exists():
        return "met", [f"Found {path.relative_to(repo_path)}"]
    return "unmet", [f"Missing {path.relative_to(repo_path)}"]


def _glob_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    patterns = params.get("patterns") or [params["pattern"]]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(str(path.relative_to(repo_path)) for path in repo_path.glob(str(pattern)))
    if matches:
        unique = sorted(set(matches))
        return "met", [f"Matched {path}" for path in unique]
    return "unmet", [f"No files matched {', '.join(str(p) for p in patterns)}"]


def _yaml_path_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params["path"])
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path)}"]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return "unmet", [f"Invalid YAML in {path.relative_to(repo_path)}"]

    yaml_path = params.get("yaml_path", [])
    current: Any = data
    for key in yaml_path:
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        return "unmet", [f"Missing YAML path {'.'.join(yaml_path)} in {path.relative_to(repo_path)}"]
    return "met", [f"Found YAML path {'.'.join(yaml_path)} in {path.relative_to(repo_path)}"]


def _text_match(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params["path"])
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path)}"]

    content = path.read_text(encoding="utf-8", errors="replace")
    pattern = str(params["pattern"])
    if params.get("regex", False):
        if re.search(pattern, content, flags=re.MULTILINE):
            return "met", [f"Matched regex in {path.relative_to(repo_path)}: {pattern}"]
    elif pattern in content:
        return "met", [f"Found text in {path.relative_to(repo_path)}: {pattern}"]
    return "unmet", [f"Did not find expected text in {path.relative_to(repo_path)}"]


def _github_actions_rule(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    workflow_glob = str(params.get("workflow_glob", ".github/workflows/*.y*ml"))
    yaml_path = list(params.get("yaml_path", []))

    matches = list(repo_path.glob(workflow_glob))
    if not matches:
        return "unmet", [f"No workflow files matched {workflow_glob}"]

    found_in: list[str] = []
    for path in matches:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        current: Any = data
        missing = False
        for key in yaml_path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                missing = True
                break
        if not missing:
            found_in.append(str(path.relative_to(repo_path)))

    if found_in:
        return "met", [f"Found workflow rule in {path}" for path in sorted(found_in)]
    return "unmet", [f"Did not find workflow rule {'.'.join(yaml_path)}"]


def _make_target_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params.get("path", "Makefile"))
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path)}"]

    target = str(params["target"])
    pattern = re.compile(rf"^{re.escape(target)}\s*:", flags=re.MULTILINE)
    content = path.read_text(encoding="utf-8", errors="replace")
    if pattern.search(content):
        return "met", [f"Found make target {target} in {path.relative_to(repo_path)}"]
    return "unmet", [f"Missing make target {target} in {path.relative_to(repo_path)}"]


def _pyproject_field_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params.get("path", "pyproject.toml"))
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path)}"]

    with open(path, "rb") as f:
        data = tomllib.load(f)

    fields = list(params.get("field_path", []))
    current: Any = data
    for field in fields:
        if isinstance(current, dict) and field in current:
            current = current[field]
            continue
        return "unmet", [f"Missing TOML path {'.'.join(fields)} in {path.relative_to(repo_path)}"]
    return "met", [f"Found TOML path {'.'.join(fields)} in {path.relative_to(repo_path)}"]


def _manual_only(_repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    prompt = str(params.get("prompt", "Manual evidence required in compliance.yml"))
    return "unknown", [prompt]
