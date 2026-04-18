"""Unit tests for repoman.compliance."""

from pathlib import Path

import pytest

from repoman.compliance import BUILTIN_PROFILES, ComplianceConfigError, analyze_compliance
from repoman.compliance.config import load_compliance_config
from repoman.compliance.detectors import evaluate_detector
from repoman.compliance.models import DetectorSpec


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def test_detector_file_exists(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Test\n", encoding="utf-8")

    status, evidence = evaluate_detector(repo, DetectorSpec("file_exists", {"path": "README.md"}))

    assert status == "met"
    assert "README.md" in evidence[0]


def test_detector_yaml_path_exists(tmp_path: Path) -> None:
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


def test_detector_pyproject_field_exists(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "pyproject.toml").write_text("[project]\nname='demo'\ndependencies=['typer']\n", encoding="utf-8")

    status, _evidence = evaluate_detector(
        repo,
        DetectorSpec("pyproject_field_exists", {"field_path": ["project", "dependencies"]}),
    )

    assert status == "met"


def test_load_compliance_config_requires_waiver_justification(tmp_path: Path) -> None:
    config = tmp_path / "compliance.yml"
    config.write_text("controls:\n  test.control:\n    status: waived\n", encoding="utf-8")

    with pytest.raises(ComplianceConfigError):
        load_compliance_config(config)


def test_analyze_compliance_computes_bronze_and_manual_unknowns(tmp_path: Path) -> None:
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


def test_manual_control_can_be_met_via_compliance_file(tmp_path: Path) -> None:
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
    assert "soc2-software" in BUILTIN_PROFILES
    assert "oss-best-practices" in BUILTIN_PROFILES


def test_unknown_control_id_in_compliance_file_fails_clearly(tmp_path: Path) -> None:
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


def test_readme_does_not_satisfy_architecture_or_rollback_controls(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")

    report = analyze_compliance(repo, profile_ids=["soc2-software"])[0]

    statuses = {control.control_id: control.status for control in report.controls}
    assert statuses["soc2.architecture.docs"] == "unmet"
    assert statuses["soc2.operations.rollback"] == "unmet"


def test_repo_self_compliance_baseline_passes() -> None:
    repo = Path(__file__).resolve().parents[1]

    reports = analyze_compliance(
        repo,
        profile_ids=["soc2-software", "oss-best-practices"],
        compliance_file=repo / "compliance.yml",
    )

    assert {report.profile_id for report in reports} == {"soc2-software", "oss-best-practices"}
    assert all(report.gate.passed for report in reports)
