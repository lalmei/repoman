"""Loading and validating compliance.yml."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from repoman.compliance.models import (
    ComplianceConfig,
    ComplianceConfigError,
    ControlOverride,
    ProfileSettings,
    TIER_ORDER,
)

VALID_STATUSES = {"met", "unmet", "unknown", "waived"}


def load_compliance_config(path: Path | None) -> ComplianceConfig:
    """Load compliance.yml if it exists; otherwise return defaults."""
    if path is None or not path.exists():
        return ComplianceConfig()

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ComplianceConfigError(f"Invalid YAML in {path}: {e}") from e

    if not isinstance(raw, dict):
        raise ComplianceConfigError("compliance.yml must contain a mapping at the top level")

    version = raw.get("version", 1)
    if not isinstance(version, int):
        raise ComplianceConfigError("compliance.yml field 'version' must be an integer")

    profiles = _parse_profiles(raw.get("profiles", {}))
    controls = _parse_controls(raw.get("controls", {}))
    defaults = raw.get("defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise ComplianceConfigError("compliance.yml field 'defaults' must be a mapping")

    return ComplianceConfig(
        version=version,
        profiles=profiles,
        controls=controls,
        defaults=defaults,
    )


def _parse_profiles(raw: Any) -> dict[str, ProfileSettings]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ComplianceConfigError("compliance.yml field 'profiles' must be a mapping")

    profiles: dict[str, ProfileSettings] = {}
    for profile_id, value in raw.items():
        if not isinstance(value, dict):
            raise ComplianceConfigError(f"profile '{profile_id}' must be a mapping")
        tier_target = value.get("tier_target")
        if tier_target is not None and tier_target not in TIER_ORDER:
            raise ComplianceConfigError(f"profile '{profile_id}' has invalid tier_target '{tier_target}'")
        profiles[str(profile_id)] = ProfileSettings(
            enabled=bool(value.get("enabled", True)),
            tier_target=tier_target,
            include=_ensure_str_list(value.get("include", []), f"profile '{profile_id}' include"),
            exclude=_ensure_str_list(value.get("exclude", []), f"profile '{profile_id}' exclude"),
        )
    return profiles


def _parse_controls(raw: Any) -> dict[str, ControlOverride]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ComplianceConfigError("compliance.yml field 'controls' must be a mapping")

    controls: dict[str, ControlOverride] = {}
    for control_id, value in raw.items():
        if not isinstance(value, dict):
            raise ComplianceConfigError(f"control '{control_id}' must be a mapping")
        status = value.get("status")
        if status is not None and status not in VALID_STATUSES:
            raise ComplianceConfigError(f"control '{control_id}' has invalid status '{status}'")
        justification = value.get("justification")
        if status == "waived" and not justification:
            raise ComplianceConfigError(f"control '{control_id}' waivers require a justification")
        controls[str(control_id)] = ControlOverride(
            status=status,
            justification=justification,
            owner=value.get("owner"),
            evidence=_ensure_str_list(value.get("evidence", []), f"control '{control_id}' evidence"),
            last_reviewed=value.get("last_reviewed"),
            notes=value.get("notes"),
        )
    return controls


def _ensure_str_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ComplianceConfigError(f"{field_name} must be a list of strings")
    return list(value)
