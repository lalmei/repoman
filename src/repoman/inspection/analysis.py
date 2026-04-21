"""Pure repository inspection logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import yaml

from repoman.config import load_answers
from repoman.copier import ExtensionLifecycleError, load_manifest
from repoman.copier.extension_lifecycle import MANIFEST_RELATIVE_PATH
from repoman.inspection.models import (
    AnswersFileState,
    ExtensionState,
    ExtensionSummary,
    FeatureFlags,
    InspectionReport,
    InspectionStatus,
    TemplateMetadata,
    UpdateReadiness,
)

if TYPE_CHECKING:
    from pathlib import Path


class InspectionError(RuntimeError):
    """Raised when the repository cannot be inspected at all."""


def inspect_repository(
    repo_path: Path,
    *,
    answers_file: Path | None = None,
    skip_extensions: bool = False,
) -> InspectionReport:
    """Inspect a git repository for repoman lifecycle readiness."""
    repo_path = repo_path.resolve()
    if not repo_path.exists():
        raise InspectionError(f"Path does not exist: {repo_path}")
    if not repo_path.is_dir():
        raise InspectionError(f"Path is not a directory: {repo_path}")
    if not (repo_path / ".git").exists():
        raise InspectionError(f"Not a git repository (no .git directory): {repo_path}")

    answers_path = (answers_file.resolve() if answers_file is not None else repo_path / ".copier-answers.yml").resolve()
    answers_state = AnswersFileState(
        path=str(answers_path),
        exists=answers_path.exists(),
        within_project=_is_within_project(answers_path, repo_path),
    )

    blockers: list[str] = []
    warnings: list[str] = []
    fatal = False
    managed = answers_state.exists
    template = TemplateMetadata()
    features = FeatureFlags()

    if not answers_state.exists:
        blockers.append(f"Copier answers file not found: {answers_path}")
    else:
        try:
            answers = load_answers(answers_path)
        except yaml.YAMLError as exc:
            fatal = True
            blockers.append(f"Invalid YAML in answers file {answers_path}: {exc}")
        else:
            template = TemplateMetadata(
                src_path=_clean_optional_str(answers.get("_src_path")),
                commit=_clean_optional_str(answers.get("_commit")),
                vcs_ref=_clean_optional_str(answers.get("_vcs_ref")),
            )
            features = FeatureFlags(
                docs_only=_as_bool(answers.get("docs_only")),
                fastapi_enabled=_as_bool(answers.get("fastapi_enabled")),
                dataset_enabled=_as_bool(answers.get("dataset_enabled")),
                python_notebooks=_as_bool(answers.get("python_notebooks")),
                cli_enabled=bool(_clean_optional_str(answers.get("python_package_command_line_name"))),
            )
            if answers_state.within_project is False:
                blockers.append(
                    f"Answers file must be inside the project directory for Copier update (got {answers_path})."
                )
            if template.src_path and not template.commit:
                blockers.append("`_src_path` is set but `_commit` is missing.")
            if template.commit and not template.src_path:
                warnings.append("`_commit` is set but `_src_path` is missing.")

    extensions, extension_fatal = _inspect_extensions(repo_path, skip_extensions=skip_extensions)
    fatal = fatal or extension_fatal
    warnings.extend(extensions.warnings)
    if extension_fatal:
        blockers.extend(extensions.warnings)
    if not skip_extensions:
        for extension in extensions.active:
            expected_answers = repo_path / extension.answers_file
            if not expected_answers.exists():
                blockers.append(f"Missing extension answers file for {extension.id}: {expected_answers}")

    readiness = UpdateReadiness(
        ready=not blockers,
        blockers=blockers,
        warnings=warnings,
    )

    return InspectionReport(
        path=str(repo_path),
        managed=managed,
        status=_status_for(readiness, fatal=fatal),
        answers_file=answers_state,
        template=template,
        features=features,
        extensions=extensions,
        update_readiness=readiness,
        fatal=fatal,
    )


def _inspect_extensions(repo_path: Path, *, skip_extensions: bool) -> tuple[ExtensionSummary, bool]:
    """Load extension summary and collect extension-related warnings."""
    manifest_path = (repo_path / MANIFEST_RELATIVE_PATH).resolve()
    summary = ExtensionSummary(
        manifest_path=str(manifest_path),
        exists=manifest_path.exists(),
        version=None,
        active=[],
        warnings=[],
    )
    if not manifest_path.exists():
        return summary, False

    try:
        manifest = load_manifest(repo_path)
    except ExtensionLifecycleError as exc:
        summary.warnings.append(f"Extension manifest is invalid: {exc}")
        return summary, not skip_extensions

    summary.version = manifest.version
    summary.active = [
        ExtensionState(
            id=extension.id,
            type=extension.type,
            name=extension.name,
            status=extension.status,
            answers_file=extension.answers_file,
            template_id=extension.template_id,
        )
        for extension in manifest.extensions
        if extension.status == "active"
    ]
    return summary, False


def _clean_optional_str(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _as_bool(value: Any) -> bool:
    return bool(value)


def _is_within_project(path: Path, repo_path: Path) -> bool | None:
    try:
        path.relative_to(repo_path)
    except ValueError:
        return False
    return True


def _status_for(readiness: UpdateReadiness, *, fatal: bool) -> InspectionStatus:
    if fatal:
        return "error"
    if readiness.blockers or readiness.warnings:
        return "warning"
    return "ok"
