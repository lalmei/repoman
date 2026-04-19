"""Core models for repository compliance analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

Status = Literal["met", "unmet", "unknown", "waived"]
Tier = Literal["bronze", "silver", "gold"]
FailOn = Literal["unmet", "unknown", "tier"]
DetectionKind = Literal[
    "file_exists",
    "glob_exists",
    "yaml_path_exists",
    "text_match",
    "github_actions_rule",
    "make_target_exists",
    "pyproject_field_exists",
    "manual_only",
]

TIER_ORDER: tuple[Tier, ...] = ("bronze", "silver", "gold")
STATUS_ORDER: tuple[Status, ...] = ("met", "waived", "unknown", "unmet")


class ComplianceConfigError(ValueError):
    """Raised when compliance.yml is invalid."""


@dataclass(frozen=True)
class DetectorSpec:
    """Configuration for a detector used by a control."""

    kind: DetectionKind
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ControlDefinition:
    """Single control in a compliance profile."""

    control_id: str
    section: str
    title: str
    description: str
    tier: Tier
    detection: DetectorSpec
    required_evidence: str | None = None
    weight: int = 1
    applies_when: tuple[DetectorSpec, ...] = ()


@dataclass(frozen=True)
class ControlProfile:
    """Built-in profile definition."""

    profile_id: str
    title: str
    description: str
    disclaimer: str
    controls: tuple[ControlDefinition, ...]
    tiers: tuple[Tier, ...] = TIER_ORDER


@dataclass
class ControlResult:
    """Evaluation result for a single control."""

    control_id: str
    section: str
    title: str
    description: str
    tier: Tier
    status: Status
    detection_kind: DetectionKind
    evidence: list[str] = field(default_factory=list)
    justification: str | None = None
    owner: str | None = None
    last_reviewed: str | None = None
    notes: str | None = None
    required_evidence: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize result to a JSON-friendly dict."""
        return asdict(self)


@dataclass
class SectionSummary:
    """Rollup summary for a control section."""

    name: str
    met: int = 0
    unmet: int = 0
    unknown: int = 0
    waived: int = 0
    blocking_controls: list[str] = field(default_factory=list)
    unknown_controls: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize summary to a JSON-friendly dict."""
        return asdict(self)


@dataclass
class GateResult:
    """Outcome of applying exit-code oriented gating rules."""

    passed: bool
    fail_on: FailOn
    strict: bool
    requested_tier: Tier | None
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize gate result."""
        return asdict(self)


@dataclass
class ComplianceReport:
    """Full report for a single profile against a repository."""

    repo_path: str
    profile_id: str
    profile_title: str
    description: str
    disclaimer: str
    generated_at: str
    achieved_tier: Tier | None
    next_tier: Tier | None
    requested_tier: Tier | None
    blocking_controls: list[str]
    advisory_controls: list[str]
    summary_counts: dict[str, int]
    sections: list[SectionSummary]
    controls: list[ControlResult]
    gate: GateResult

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report."""
        return {
            "repo_path": self.repo_path,
            "profile_id": self.profile_id,
            "profile_title": self.profile_title,
            "description": self.description,
            "disclaimer": self.disclaimer,
            "generated_at": self.generated_at,
            "achieved_tier": self.achieved_tier,
            "next_tier": self.next_tier,
            "requested_tier": self.requested_tier,
            "blocking_controls": self.blocking_controls,
            "advisory_controls": self.advisory_controls,
            "summary_counts": dict(self.summary_counts),
            "sections": [section.to_dict() for section in self.sections],
            "controls": [control.to_dict() for control in self.controls],
            "gate": self.gate.to_dict(),
        }


@dataclass
class ControlOverride:
    """Repo-declared control override from compliance.yml."""

    status: Status | None = None
    justification: str | None = None
    owner: str | None = None
    evidence: list[str] = field(default_factory=list)
    last_reviewed: str | None = None
    notes: str | None = None


@dataclass
class ProfileSettings:
    """Per-profile settings from compliance.yml."""

    enabled: bool = True
    tier_target: Tier | None = None
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)


@dataclass
class ComplianceConfig:
    """Parsed compliance.yml content."""

    version: int = 1
    profiles: dict[str, ProfileSettings] = field(default_factory=dict)
    controls: dict[str, ControlOverride] = field(default_factory=dict)
    defaults: dict[str, Any] = field(default_factory=dict)


def utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 form."""
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
