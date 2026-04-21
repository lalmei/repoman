"""Typed models for repository inspection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

InspectionStatus = Literal["ok", "warning", "error"]


@dataclass(slots=True)
class AnswersFileState:
    """State of the selected Copier answers file."""

    path: str
    exists: bool
    within_project: bool | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "exists": self.exists,
            "within_project": self.within_project,
        }


@dataclass(slots=True)
class TemplateMetadata:
    """Template metadata read from the answers file."""

    src_path: str | None = None
    commit: str | None = None
    vcs_ref: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "src_path": self.src_path,
            "commit": self.commit,
            "vcs_ref": self.vcs_ref,
        }


@dataclass(slots=True)
class FeatureFlags:
    """Feature flags derived from Copier answers."""

    docs_only: bool = False
    fastapi_enabled: bool = False
    dataset_enabled: bool = False
    python_notebooks: bool = False
    cli_enabled: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "docs_only": self.docs_only,
            "fastapi_enabled": self.fastapi_enabled,
            "dataset_enabled": self.dataset_enabled,
            "python_notebooks": self.python_notebooks,
            "cli_enabled": self.cli_enabled,
        }


@dataclass(slots=True)
class ExtensionState:
    """Summary of an active extension instance."""

    id: str
    type: str
    name: str
    status: str
    answers_file: str
    template_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "status": self.status,
            "answers_file": self.answers_file,
            "template_id": self.template_id,
        }


@dataclass(slots=True)
class ExtensionSummary:
    """Summary of extension manifest state."""

    manifest_path: str
    exists: bool
    version: int | None = None
    active: list[ExtensionState] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest_path": self.manifest_path,
            "exists": self.exists,
            "version": self.version,
            "active": [item.to_dict() for item in self.active],
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class UpdateReadiness:
    """Whether the repository is ready for Copier update."""

    ready: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "blockers": self.blockers,
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class InspectionReport:
    """Full repository inspection result."""

    path: str
    managed: bool
    status: InspectionStatus
    answers_file: AnswersFileState
    template: TemplateMetadata
    features: FeatureFlags
    extensions: ExtensionSummary
    update_readiness: UpdateReadiness
    fatal: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "managed": self.managed,
            "status": self.status,
            "answers_file": self.answers_file.to_dict(),
            "template": self.template.to_dict(),
            "features": self.features.to_dict(),
            "extensions": self.extensions.to_dict(),
            "update_readiness": self.update_readiness.to_dict(),
        }
