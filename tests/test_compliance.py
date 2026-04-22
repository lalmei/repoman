"""Unit tests for repoman.compliance."""

from pathlib import Path

import pytest

from repoman.compliance import BUILTIN_PROFILES, ComplianceConfigError, analyze_compliance
from repoman.compliance.analysis import (
    _build_gate_result,
    _evaluate_control,
    _next_tier,
    manual_controls_for_profiles,
)
from repoman.compliance.config import load_compliance_config
from repoman.compliance.detectors import evaluate_detector
from repoman.compliance.models import (
    ComplianceReport,
    ControlDefinition,
    ControlOverride,
    ControlResult,
    DetectorSpec,
    GateResult,
    SectionSummary,
)
from repoman.compliance.report import build_starter_config, reports_to_markdown, write_reports


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_detector_file_exists(tmp_path: Path) -> None:
    """Mark the file detector as met when the file exists."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")

    status, evidence = evaluate_detector(repo, DetectorSpec("file_exists", {"path": "README.md"}))

    assert status == "met"
    assert "README.md" in evidence[0]


def test_detector_yaml_path_exists(tmp_path: Path) -> None:
    """Mark the YAML-path detector as met when the path exists."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")

    status, _evidence = evaluate_detector(
        repo,
        DetectorSpec("yaml_path_exists", {"path": ".github/workflows/ci.yml", "yaml_path": ["jobs", "test"]}),
    )

    assert status == "met"


def test_detector_github_actions_rule(tmp_path: Path) -> None:
    """Match GitHub Actions rules when the configured YAML path exists."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  build:\n    steps:\n      - run: make test\n", encoding="utf-8")

    status, evidence = evaluate_detector(
        repo,
        DetectorSpec("github_actions_rule", {"yaml_path": ["jobs", "build", "steps"]}),
    )

    assert status == "met"
    assert "ci.yml" in evidence[0]


def test_detector_text_match_regex_and_manual_only(tmp_path: Path) -> None:
    """Support regex text matching and manual-only detector prompts."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("Contact security@example.com for disclosure.\n", encoding="utf-8")

    regex_status, regex_evidence = evaluate_detector(
        repo,
        DetectorSpec("text_match", {"path": "README.md", "pattern": r"security@\w+\.com", "regex": True}),
    )
    manual_status, manual_evidence = evaluate_detector(
        repo,
        DetectorSpec("manual_only", {"prompt": "Manual evidence required"}),
    )

    assert regex_status == "met"
    assert "Matched regex" in regex_evidence[0]
    assert manual_status == "unknown"
    assert manual_evidence == ["Manual evidence required"]


def test_detector_yaml_invalid_and_missing_workflow_rule(tmp_path: Path) -> None:
    """Treat invalid YAML and missing workflow rules as unmet."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs: [", encoding="utf-8")
    (workflows / "build.yml").write_text("jobs:\n  build:\n    runs-on: ubuntu-latest\n", encoding="utf-8")

    yaml_status, yaml_evidence = evaluate_detector(
        repo,
        DetectorSpec("yaml_path_exists", {"path": ".github/workflows/ci.yml", "yaml_path": ["jobs"]}),
    )
    rule_status, rule_evidence = evaluate_detector(
        repo,
        DetectorSpec(
            "github_actions_rule", {"workflow_glob": ".github/workflows/*.yml", "yaml_path": ["jobs", "test"]}
        ),
    )

    assert yaml_status == "unmet"
    assert "Invalid YAML" in yaml_evidence[0]
    assert rule_status == "unmet"
    assert "Did not find workflow rule" in rule_evidence[0]


def test_detector_missing_make_target_and_pyproject_path(tmp_path: Path) -> None:
    """Report missing Makefiles and pyproject files as unmet."""
    repo = _make_repo(tmp_path)

    make_status, make_evidence = evaluate_detector(repo, DetectorSpec("make_target_exists", {"target": "test"}))
    pyproject_status, pyproject_evidence = evaluate_detector(
        repo,
        DetectorSpec("pyproject_field_exists", {"field_path": ["project", "dependencies"]}),
    )

    assert make_status == "unmet"
    assert "Missing Makefile" in make_evidence[0]
    assert pyproject_status == "unmet"
    assert "Missing pyproject.toml" in pyproject_evidence[0]


def test_detector_pyproject_field_exists(tmp_path: Path) -> None:
    """Mark the pyproject detector as met when the field path exists."""
    repo = _make_repo(tmp_path)
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\ndependencies=['typer']\n", encoding="utf-8")

    status, _evidence = evaluate_detector(
        repo,
        DetectorSpec("pyproject_field_exists", {"field_path": ["project", "dependencies"]}),
    )

    assert status == "met"


def test_load_compliance_config_requires_waiver_justification(tmp_path: Path) -> None:
    """Reject waived controls that do not include a justification."""
    config = tmp_path / "compliance.yml"
    config.write_text("controls:\n  test.control:\n    status: waived\n", encoding="utf-8")

    with pytest.raises(ComplianceConfigError):
        load_compliance_config(config)


def test_load_compliance_config_rejects_invalid_defaults_mapping(tmp_path: Path) -> None:
    """Reject defaults blocks that are not mappings."""
    config = tmp_path / "compliance.yml"
    config.write_text("defaults: []\n", encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match="defaults"):
        load_compliance_config(config)


def test_load_compliance_config_rejects_invalid_profile_shape(tmp_path: Path) -> None:
    """Reject profile entries that are not mappings."""
    config = tmp_path / "compliance.yml"
    config.write_text("profiles:\n  bad: []\n", encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match="profile 'bad' must be a mapping"):
        load_compliance_config(config)


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ("profiles: [\n", "Invalid YAML"),
        ("[1]\n", "must contain a mapping"),
        ("version: nope\n", "field 'version' must be an integer"),
    ],
)
def test_load_compliance_config_rejects_invalid_yaml_top_level_and_version(
    tmp_path: Path, content: str, match: str
) -> None:
    """Reject malformed YAML, non-mapping payloads, and non-integer versions."""
    config = tmp_path / "compliance.yml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match=match):
        load_compliance_config(config)


def test_load_compliance_config_accepts_null_sections_and_null_string_lists(tmp_path: Path) -> None:
    """Treat null sections and null list-like fields as empty values."""
    config = tmp_path / "compliance.yml"
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "profiles:",
                "controls:",
                "defaults:",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = load_compliance_config(config)

    assert parsed.profiles == {}
    assert parsed.controls == {}
    assert parsed.defaults == {}

    config.write_text(
        "\n".join(
            [
                "profiles:",
                "  oss-best-practices:",
                "    include:",
                "    exclude:",
                "controls:",
                "  oss.docs.readme:",
                "    evidence:",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = load_compliance_config(config)

    assert parsed.profiles["oss-best-practices"].include == []
    assert parsed.profiles["oss-best-practices"].exclude == []
    assert parsed.controls["oss.docs.readme"].evidence == []


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ("profiles: []\n", "field 'profiles' must be a mapping"),
        ("profiles:\n  oss-best-practices:\n    tier_target: platinum\n", "invalid tier_target"),
        ("profiles:\n  oss-best-practices:\n    include: [ok, 3]\n", "include must be a list of strings"),
        ("controls: []\n", "field 'controls' must be a mapping"),
        ("controls:\n  oss.docs.readme: []\n", "control 'oss.docs.readme' must be a mapping"),
        ("controls:\n  oss.docs.readme:\n    status: maybe\n", "invalid status"),
        ("controls:\n  oss.docs.readme:\n    evidence: [ok, 3]\n", "evidence must be a list of strings"),
    ],
)
def test_load_compliance_config_rejects_invalid_profile_and_control_fields(
    tmp_path: Path, content: str, match: str
) -> None:
    """Reject invalid compliance profile and control field shapes."""
    config = tmp_path / "compliance.yml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match=match):
        load_compliance_config(config)


def test_analyze_compliance_computes_bronze_and_manual_unknowns(tmp_path: Path) -> None:
    """Compute bronze tier and retain unknown manual controls."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "CONTRIBUTING.md").write_text("Use a pull request.\n", encoding="utf-8")
    (repo / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (repo / "Makefile").write_text("test:\n\tpytest\n", encoding="utf-8")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci\njobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")

    reports = analyze_compliance(repo, profile_ids=["oss-best-practices"])

    assert len(reports) == 1
    report = reports[0]
    assert report.profile_id == "oss-best-practices"
    assert report.achieved_tier == "bronze"
    assert report.next_tier == "silver"
    assert report.summary_counts["unknown"] >= 1


def test_unknown_blocks_requested_tier(tmp_path: Path) -> None:
    """Block the requested tier when strict tier evaluation sees unknown controls."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "CONTRIBUTING.md").write_text("pull request\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\ndependencies=['a']\n", encoding="utf-8")
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  soc2.environments.separation:",
                "    status: met",
                "    evidence:",
                "      - Documented in internal architecture docs",
                "  soc2.cicd.secrets-manager:",
                "    status: unknown",
                "    evidence:",
                "      - Pending platform review",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = analyze_compliance(
        repo,
        profile_ids=["soc2-software"],
        requested_tier="silver",
        fail_on="tier",
    )[0]

    assert report.achieved_tier == "bronze"
    assert report.gate.passed is False
    assert any("silver" in reason for reason in report.gate.reasons)


def test_invalid_override_cannot_force_unmet_to_met(tmp_path: Path) -> None:
    """Reject overrides that force an unmet detected control to met."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  oss.docs.contributing:",
                "    status: met",
                "    evidence:",
                "      - Manual note",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ComplianceConfigError):
        analyze_compliance(repo, profile_ids=["oss-best-practices"])


def test_analyze_compliance_rejects_invalid_paths_and_unknown_selected_profile(tmp_path: Path) -> None:
    """Reject missing paths, non-git directories, and unknown selected profiles."""
    missing = tmp_path / "missing"
    non_git = tmp_path / "non_git"
    non_git.mkdir()
    repo = _make_repo(tmp_path)

    with pytest.raises(ComplianceConfigError, match="Path does not exist or is not a directory"):
        analyze_compliance(missing)

    with pytest.raises(ComplianceConfigError, match="Not a git repository"):
        analyze_compliance(non_git)

    with pytest.raises(ComplianceConfigError, match="Unknown profile 'missing-profile'"):
        analyze_compliance(repo, profile_ids=["missing-profile"])


def test_analyze_compliance_skips_disabled_profiles_and_respects_include_exclude(tmp_path: Path) -> None:
    """Skip disabled profiles and only evaluate included controls that are not excluded."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "CONTRIBUTING.md").write_text("pull request\n", encoding="utf-8")

    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "profiles:",
                "  oss-best-practices:",
                "    enabled: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    assert analyze_compliance(repo, profile_ids=["oss-best-practices"]) == []

    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "profiles:",
                "  oss-best-practices:",
                "    include:",
                "      - oss.docs.readme",
                "      - oss.docs.contributing",
                "    exclude:",
                "      - oss.docs.contributing",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    report = analyze_compliance(repo, profile_ids=["oss-best-practices"])[0]

    assert [control.control_id for control in report.controls] == ["oss.docs.readme"]


@pytest.mark.parametrize(
    ("content", "match"),
    [
        (
            "\n".join(
                [
                    "profiles:",
                    "  made-up-profile:",
                    "    enabled: true",
                ]
            )
            + "\n",
            "Unknown profile id 'made-up-profile'",
        ),
        (
            "\n".join(
                [
                    "profiles:",
                    "  oss-best-practices:",
                    "    include:",
                    "      - not.a.real.control",
                ]
            )
            + "\n",
            "Unknown control ids for profile 'oss-best-practices'",
        ),
    ],
)
def test_analyze_compliance_rejects_invalid_profile_configuration(
    tmp_path: Path, content: str, match: str
) -> None:
    """Fail fast on bad profile ids and invalid include/exclude control ids."""
    repo = _make_repo(tmp_path)
    (repo / "compliance.yml").write_text(content, encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match=match):
        analyze_compliance(repo, profile_ids=["oss-best-practices"])


def test_evaluate_control_handles_applicability_and_override_metadata(tmp_path: Path) -> None:
    """Preserve metadata-only overrides and mark non-applicable controls unknown."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")

    gated_control = ControlDefinition(
        control_id="custom.docs.architecture",
        section="docs",
        title="Architecture docs",
        description="Architecture docs exist",
        tier="bronze",
        detection=DetectorSpec("file_exists", {"path": "docs/architecture.md"}),
        required_evidence="docs/architecture.md",
        applies_when=(DetectorSpec("file_exists", {"path": "pyproject.toml"}),),
    )
    gated_result = _evaluate_control(repo, gated_control, None)

    assert gated_result.status == "unknown"
    assert gated_result.required_evidence == "docs/architecture.md"
    assert gated_result.evidence == ["Applicability conditions were not met by repository contents."]

    readme_control = ControlDefinition(
        control_id="custom.docs.readme",
        section="docs",
        title="README exists",
        description="README exists",
        tier="bronze",
        detection=DetectorSpec("file_exists", {"path": "README.md"}),
    )
    result = _evaluate_control(
        repo,
        readme_control,
        ControlOverride(
            status=None,
            justification="Reviewed by maintainer",
            owner="docs",
            evidence=["Found README.md", "Linked from project homepage"],
            last_reviewed="2026-04-20",
            notes="Looks good",
        ),
    )

    assert result.status == "met"
    assert result.justification == "Reviewed by maintainer"
    assert result.owner == "docs"
    assert result.last_reviewed == "2026-04-20"
    assert result.notes == "Looks good"
    assert result.evidence == ["Found README.md", "Linked from project homepage"]


def test_evaluate_control_handles_waivers_manual_controls_and_status_downgrades(tmp_path: Path) -> None:
    """Support manual overrides and reject unjustified waivers."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")

    readme_control = ControlDefinition(
        control_id="custom.docs.readme",
        section="docs",
        title="README exists",
        description="README exists",
        tier="bronze",
        detection=DetectorSpec("file_exists", {"path": "README.md"}),
    )
    downgraded = _evaluate_control(repo, readme_control, ControlOverride(status="unknown"))
    assert downgraded.status == "unknown"

    manual_control = ControlDefinition(
        control_id="custom.manual.review",
        section="ops",
        title="Manual review",
        description="Manual review completed",
        tier="silver",
        detection=DetectorSpec("manual_only", {"prompt": "Manual review required"}),
    )
    manual_result = _evaluate_control(repo, manual_control, ControlOverride(status="met"))
    assert manual_result.status == "met"

    with pytest.raises(ComplianceConfigError, match="waiver requires a justification"):
        _evaluate_control(repo, manual_control, ControlOverride(status="waived"))


def test_gate_helpers_cover_unmet_unknown_strict_and_requested_tier_outcomes() -> None:
    """Exercise remaining gate result branches and helper outputs."""
    unmet_result = ControlResult(
        control_id="custom.unmet",
        section="ops",
        title="Unmet control",
        description="Unmet",
        tier="bronze",
        status="unmet",
        detection_kind="file_exists",
    )
    unknown_result = ControlResult(
        control_id="custom.unknown",
        section="ops",
        title="Unknown control",
        description="Unknown",
        tier="bronze",
        status="unknown",
        detection_kind="manual_only",
    )

    unmet_gate = _build_gate_result(
        control_results=[unmet_result],
        achieved_tier=None,
        requested_tier=None,
        fail_on="unmet",
        strict=False,
    )
    unknown_gate = _build_gate_result(
        control_results=[unknown_result],
        achieved_tier=None,
        requested_tier=None,
        fail_on="unknown",
        strict=False,
    )
    strict_gate = _build_gate_result(
        control_results=[unknown_result],
        achieved_tier=None,
        requested_tier=None,
        fail_on="unmet",
        strict=True,
    )
    requested_gate = _build_gate_result(
        control_results=[],
        achieved_tier="bronze",
        requested_tier="gold",
        fail_on="tier",
        strict=False,
    )

    assert unmet_gate.passed is False
    assert unmet_gate.reasons == ["Unmet controls: custom.unmet"]
    assert unknown_gate.passed is False
    assert unknown_gate.reasons == ["Unknown controls: custom.unknown"]
    assert strict_gate.passed is False
    assert strict_gate.reasons == ["Strict mode failed due to unknown controls: custom.unknown"]
    assert requested_gate.passed is False
    assert requested_gate.reasons == ["Achieved tier bronze is below requested tier gold"]
    assert _next_tier("gold") is None


def test_manual_controls_for_profiles_returns_only_manual_controls() -> None:
    """Group only manual-only controls for the requested profiles."""
    grouped = manual_controls_for_profiles(["oss-best-practices"])

    assert list(grouped) == ["oss-best-practices"]
    assert grouped["oss-best-practices"]
    assert all(control.detection.kind == "manual_only" for control in grouped["oss-best-practices"])


def test_manual_control_can_be_met_via_compliance_file(tmp_path: Path) -> None:
    """Allow manual-only controls to be satisfied from compliance.yml evidence."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "CONTRIBUTING.md").write_text("pull request\n", encoding="utf-8")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  build:\n    steps:\n      - run: make test\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\ndependencies=['a']\n", encoding="utf-8")
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  soc2.environments.separation:",
                "    status: met",
                "    evidence:",
                "      - Separate production account",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = analyze_compliance(repo, profile_ids=["soc2-software"])[0]
    control = next(item for item in report.controls if item.control_id == "soc2.environments.separation")
    assert control.status == "met"
    assert "Separate production account" in control.evidence


def test_builtin_profiles_exposed() -> None:
    """Expose the built-in profile registry."""
    assert "soc2-software" in BUILTIN_PROFILES
    assert "oss-best-practices" in BUILTIN_PROFILES


def test_unknown_control_id_in_compliance_file_fails_clearly(tmp_path: Path) -> None:
    """Fail fast when compliance.yml references an unknown control id."""
    repo = _make_repo(tmp_path)
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  sco2.environments.separation:",
                "    status: met",
                "    evidence:",
                "      - typo should fail",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ComplianceConfigError, match="Unknown control id"):
        analyze_compliance(repo, profile_ids=["soc2-software"])


def test_requested_tier_uses_strict_rules_for_achieved_tier(tmp_path: Path) -> None:
    """Treat unknown controls as blockers when a tier target is requested."""
    repo = _make_repo(tmp_path)
    (repo / "CONTRIBUTING.md").write_text("pull request\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("jobs:\n  test:\n    runs-on: ubuntu-latest\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\ndependencies=['a']\n", encoding="utf-8")
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  soc2.environments.separation:",
                "    status: unknown",
                "    evidence:",
                "      - Pending environment review",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = analyze_compliance(
        repo,
        profile_ids=["soc2-software"],
        requested_tier="bronze",
        fail_on="tier",
    )[0]

    assert report.achieved_tier is None
    assert "soc2.environments.separation" in report.blocking_controls


def test_report_rendering_handles_optional_sections_and_invalid_output(tmp_path: Path) -> None:
    """Render optional report sections and reject unsupported output formats."""
    report = ComplianceReport(
        repo_path="/example/repo",
        profile_id="oss-best-practices",
        profile_title="OSS Best Practices",
        description="Repository hygiene checks",
        disclaimer="Best-practices guidance only.",
        generated_at="2026-04-19T00:00:00+00:00",
        achieved_tier="bronze",
        next_tier="silver",
        requested_tier=None,
        blocking_controls=[],
        advisory_controls=[],
        summary_counts={"met": 1, "waived": 0, "unknown": 0, "unmet": 0},
        sections=[SectionSummary(name="basics", met=1)],
        controls=[
            ControlResult(
                control_id="oss.docs.readme",
                section="basics",
                title="README exists",
                description="Repository has a README.",
                tier="bronze",
                status="met",
                detection_kind="file_exists",
                evidence=["Found README.md"],
                justification="Manually reviewed",
            )
        ],
        gate=GateResult(
            passed=True,
            fail_on="tier",
            strict=False,
            requested_tier=None,
            reasons=["Requested gate passed."],
        ),
    )

    markdown = reports_to_markdown([report])
    starter = build_starter_config(["oss-best-practices"], {})

    assert "- None" in markdown
    assert "Justification: Manually reviewed" in markdown
    assert "controls:\n  {}\n" in starter

    with pytest.raises(ValueError, match="Unsupported output format"):
        write_reports([report], "text", tmp_path / "report.txt")


def test_readme_does_not_satisfy_architecture_or_rollback_controls(tmp_path: Path) -> None:
    """Keep README-only repositories from satisfying architecture or rollback controls."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")

    report = analyze_compliance(repo, profile_ids=["soc2-software"])[0]

    statuses = {control.control_id: control.status for control in report.controls}
    assert statuses["soc2.architecture.docs"] == "unmet"
    assert statuses["soc2.operations.rollback"] == "unmet"


def test_repo_self_compliance_baseline_passes() -> None:
    """Verify the repository's own compliance baseline passes."""
    repo = Path(__file__).resolve().parents[1]

    reports = analyze_compliance(
        repo,
        profile_ids=["soc2-software", "oss-best-practices"],
        compliance_file=repo / "compliance.yml",
    )

    assert {report.profile_id for report in reports} == {"soc2-software", "oss-best-practices"}
    assert all(report.gate.passed for report in reports)
