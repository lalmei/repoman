"""Pure compliance analysis engine."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from repoman.compliance.config import load_compliance_config
from repoman.compliance.detectors import detector_applies, enrich_result_with_override, evaluate_detector
from repoman.compliance.models import (
    ComplianceConfigError,
    ComplianceReport,
    ControlProfile,
    ControlResult,
    FailOn,
    GateResult,
    SectionSummary,
    TIER_ORDER,
    Tier,
    utc_now_iso,
)
from repoman.compliance.profiles import BUILTIN_PROFILES


def analyze_compliance(
    repo_path: Path,
    *,
    profile_ids: list[str] | None = None,
    compliance_file: Path | None = None,
    requested_tier: Tier | None = None,
    fail_on: FailOn = "tier",
    strict: bool = False,
) -> list[ComplianceReport]:
    """Analyze a repository against one or more built-in compliance profiles."""
    repo_path = repo_path.resolve()
    if not repo_path.exists() or not repo_path.is_dir():
        raise ComplianceConfigError(f"Path does not exist or is not a directory: {repo_path}")
    if not (repo_path / ".git").exists():
        raise ComplianceConfigError(f"Not a git repository: {repo_path}")

    config_path = compliance_file or (repo_path / "compliance.yml")
    config = load_compliance_config(config_path if config_path.exists() else None)
    selected_ids = profile_ids or list(BUILTIN_PROFILES)
    _validate_config_ids(config, selected_ids)

    reports: list[ComplianceReport] = []
    for profile_id in selected_ids:
        if profile_id not in BUILTIN_PROFILES:
            raise ComplianceConfigError(f"Unknown profile '{profile_id}'")
        profile = BUILTIN_PROFILES[profile_id]
        profile_settings = config.profiles.get(profile_id)
        if profile_settings is not None and not profile_settings.enabled:
            continue
        tier_target = requested_tier or (profile_settings.tier_target if profile_settings else None)
        reports.append(
            _analyze_profile(
                repo_path=repo_path,
                profile=profile,
                config=config,
                requested_tier=tier_target,
                fail_on=fail_on,
                strict=strict,
            )
        )
    return reports


def _analyze_profile(
    *,
    repo_path: Path,
    profile: ControlProfile,
    config,
    requested_tier: Tier | None,
    fail_on: FailOn,
    strict: bool,
) -> ComplianceReport:
    profile_settings = config.profiles.get(profile.profile_id)
    include = set(profile_settings.include if profile_settings else [])
    exclude = set(profile_settings.exclude if profile_settings else [])

    control_results: list[ControlResult] = []
    for control in profile.controls:
        if include and control.control_id not in include:
            continue
        if control.control_id in exclude:
            continue
        control_results.append(_evaluate_control(repo_path, control, config.controls.get(control.control_id)))

    counts = {"met": 0, "unmet": 0, "unknown": 0, "waived": 0}
    sections_by_name: dict[str, SectionSummary] = {}
    for result in control_results:
        counts[result.status] += 1
        section = sections_by_name.setdefault(result.section, SectionSummary(name=result.section))
        setattr(section, result.status, getattr(section, result.status) + 1)

    strict_for_tiers = strict or requested_tier is not None
    achieved_tier = _compute_achieved_tier(control_results, strict=strict_for_tiers)
    next_tier = _next_tier(achieved_tier)
    blocking_controls = _blocking_controls(control_results, requested_tier or next_tier, strict=strict_for_tiers)
    advisory_controls = [
        result.control_id
        for result in control_results
        if result.status in {"unknown", "unmet"} and result.control_id not in blocking_controls
    ]

    for result in control_results:
        section = sections_by_name[result.section]
        if result.control_id in blocking_controls:
            section.blocking_controls.append(result.control_id)
        if result.status == "unknown":
            section.unknown_controls.append(result.control_id)

    gate = _build_gate_result(
        control_results=control_results,
        achieved_tier=achieved_tier,
        requested_tier=requested_tier,
        fail_on=fail_on,
        strict=strict,
    )
    return ComplianceReport(
        repo_path=str(repo_path),
        profile_id=profile.profile_id,
        profile_title=profile.title,
        description=profile.description,
        disclaimer=profile.disclaimer,
        generated_at=utc_now_iso(),
        achieved_tier=achieved_tier,
        next_tier=next_tier,
        requested_tier=requested_tier,
        blocking_controls=blocking_controls,
        advisory_controls=advisory_controls,
        summary_counts=counts,
        sections=list(sections_by_name.values()),
        controls=control_results,
        gate=gate,
    )


def _validate_config_ids(config, selected_ids: list[str]) -> None:
    """Fail fast on unknown profile ids or control ids declared in compliance.yml."""
    known_profile_ids = set(BUILTIN_PROFILES)
    for profile_id in config.profiles:
        if profile_id not in known_profile_ids:
            raise ComplianceConfigError(f"Unknown profile id '{profile_id}'")

    known_control_ids = {
        control.control_id
        for profile in BUILTIN_PROFILES.values()
        for control in profile.controls
    }
    for control_id in config.controls:
        if control_id not in known_control_ids:
            raise ComplianceConfigError(f"Unknown control id '{control_id}'")

    for profile_id in selected_ids:
        profile_settings = config.profiles.get(profile_id)
        if profile_settings is None:
            continue
        profile_control_ids = {control.control_id for control in BUILTIN_PROFILES[profile_id].controls}
        invalid_ids = set(profile_settings.include) | set(profile_settings.exclude)
        invalid_ids = {control_id for control_id in invalid_ids if control_id not in profile_control_ids}
        if invalid_ids:
            invalid = ", ".join(sorted(invalid_ids))
            raise ComplianceConfigError(f"Unknown control ids for profile '{profile_id}': {invalid}")


def _evaluate_control(repo_path: Path, control, override) -> ControlResult:
    if control.applies_when and not detector_applies(repo_path, control.applies_when):
        result = ControlResult(
            control_id=control.control_id,
            section=control.section,
            title=control.title,
            description=control.description,
            tier=control.tier,
            status="unknown",
            detection_kind=control.detection.kind,
            evidence=["Applicability conditions were not met by repository contents."],
            required_evidence=control.required_evidence,
        )
    else:
        status, evidence = evaluate_detector(repo_path, control.detection)
        result = ControlResult(
            control_id=control.control_id,
            section=control.section,
            title=control.title,
            description=control.description,
            tier=control.tier,
            status=status,
            detection_kind=control.detection.kind,
            evidence=evidence,
            required_evidence=control.required_evidence,
        )

    if override is None:
        return result

    enrich_result_with_override(result, override.evidence)
    result.owner = override.owner
    result.last_reviewed = override.last_reviewed
    result.notes = override.notes
    if override.justification:
        result.justification = override.justification

    if override.status is None:
        return result

    if override.status == "waived":
        if not override.justification:
            raise ComplianceConfigError(f"control '{control.control_id}' waiver requires a justification")
        result.status = "waived"
        return result

    if control.detection.kind == "manual_only":
        result.status = override.status
        return result

    if result.status == "unmet" and override.status == "met":
        raise ComplianceConfigError(
            f"control '{control.control_id}' cannot be overridden from unmet to met; use evidence or a waiver"
        )
    if override.status in {"unmet", "unknown"}:
        result.status = override.status
    return result


def _compute_achieved_tier(control_results: list[ControlResult], *, strict: bool) -> Tier | None:
    achieved: Tier | None = None
    for tier in TIER_ORDER:
        if _tier_satisfied(control_results, tier, strict=strict):
            achieved = tier
            continue
        break
    return achieved


def _tier_satisfied(control_results: list[ControlResult], tier: Tier, *, strict: bool) -> bool:
    included_tiers = TIER_ORDER[: TIER_ORDER.index(tier) + 1]
    for result in control_results:
        if result.tier not in included_tiers:
            continue
        if result.status == "unmet":
            return False
        if strict and result.status == "unknown":
            return False
    return True


def _next_tier(tier: Tier | None) -> Tier | None:
    if tier is None:
        return "bronze"
    index = TIER_ORDER.index(tier)
    if index + 1 >= len(TIER_ORDER):
        return None
    return TIER_ORDER[index + 1]


def _blocking_controls(control_results: list[ControlResult], target_tier: Tier | None, *, strict: bool) -> list[str]:
    if target_tier is None:
        return []
    included_tiers = set(TIER_ORDER[: TIER_ORDER.index(target_tier) + 1])
    blockers: list[str] = []
    for result in control_results:
        if result.tier not in included_tiers:
            continue
        if result.status == "unmet" or (strict and result.status == "unknown"):
            blockers.append(result.control_id)
    return blockers


def _build_gate_result(
    *,
    control_results: list[ControlResult],
    achieved_tier: Tier | None,
    requested_tier: Tier | None,
    fail_on: FailOn,
    strict: bool,
) -> GateResult:
    reasons: list[str] = []
    passed = True

    unmet_controls = [result.control_id for result in control_results if result.status == "unmet"]
    unknown_controls = [result.control_id for result in control_results if result.status == "unknown"]

    if fail_on == "unmet" and unmet_controls:
        passed = False
        reasons.append(f"Unmet controls: {', '.join(unmet_controls)}")
    if fail_on == "unknown" and unknown_controls:
        passed = False
        reasons.append(f"Unknown controls: {', '.join(unknown_controls)}")

    if fail_on == "tier" or requested_tier is not None:
        target = requested_tier or "bronze"
        blockers = _blocking_controls(control_results, target, strict=requested_tier is not None or strict)
        if blockers:
            passed = False
            reasons.append(f"Target tier {target} blocked by: {', '.join(blockers)}")

    if strict and not requested_tier and unknown_controls:
        passed = False
        reasons.append(f"Strict mode failed due to unknown controls: {', '.join(unknown_controls)}")

    if passed and requested_tier is not None and achieved_tier is not None:
        if TIER_ORDER.index(achieved_tier) < TIER_ORDER.index(requested_tier):
            passed = False
            reasons.append(f"Achieved tier {achieved_tier} is below requested tier {requested_tier}")

    if passed and not reasons:
        reasons.append("Requested gate passed.")

    return GateResult(
        passed=passed,
        fail_on=fail_on,
        strict=strict,
        requested_tier=requested_tier,
        reasons=reasons,
    )


def manual_controls_for_profiles(profile_ids: list[str] | None = None) -> dict[str, list]:
    """Return manual-only controls grouped by profile."""
    selected = profile_ids or list(BUILTIN_PROFILES)
    grouped: dict[str, list] = defaultdict(list)
    for profile_id in selected:
        profile = BUILTIN_PROFILES[profile_id]
        grouped[profile_id] = [control for control in profile.controls if control.detection.kind == "manual_only"]
    return dict(grouped)
