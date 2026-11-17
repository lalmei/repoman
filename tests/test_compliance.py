"""Unit tests for repoman.compliance."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from repoman.compliance import (
    BUILTIN_PROFILES,
    ComplianceConfigError,
    analyze_compliance,
)
from repoman.compliance.analysis import (
    _build_gate_result,
    _evaluate_control,
    _next_tier,
    controls_for_profiles,
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
    ProviderEvidence,
    SectionSummary,
)
from repoman.compliance.providers import collect_provider_evidence
from repoman.compliance.report import (
    build_starter_config,
    reports_to_evidence_html,
    reports_to_evidence_markdown,
    reports_to_markdown,
    write_reports,
)


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
        DetectorSpec(
            "yaml_path_exists",
            {"path": ".github/workflows/ci.yml", "yaml_path": ["jobs", "test"]},
        ),
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


def test_detector_github_actions_permissions_declared_passes_for_top_level_and_jobs(
    tmp_path: Path,
) -> None:
    """Accept workflows with top-level permissions or all job-level permissions."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "top.yml").write_text(
        "permissions:\n  contents: read\njobs:\n  test:\n    runs-on: ubuntu-latest\n",
        encoding="utf-8",
    )
    (workflows / "jobs.yml").write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    permissions:",
                "      contents: read",
                "    runs-on: ubuntu-latest",
                "  lint:",
                "    permissions:",
                "      contents: read",
                "    runs-on: ubuntu-latest",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("github_actions_permissions_declared"))

    assert status == "met"
    assert any("top-level permissions" in item for item in evidence)
    assert any("every job" in item for item in evidence)


def test_detector_github_actions_permissions_declared_fails_for_missing_permissions(
    tmp_path: Path,
) -> None:
    """Reject workflows where neither the workflow nor every job declares permissions."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  test:\n    runs-on: ubuntu-latest\n  lint:\n    permissions:\n      contents: read\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("github_actions_permissions_declared"))

    assert status == "unmet"
    assert evidence == ["Missing permissions in .github/workflows/ci.yml jobs: test"]


def test_detector_github_actions_permissions_declared_fails_for_invalid_yaml(
    tmp_path: Path,
) -> None:
    """Reject invalid workflow YAML instead of silently skipping it."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "broken.yml").write_text("jobs: [", encoding="utf-8")

    status, evidence = evaluate_detector(repo, DetectorSpec("github_actions_permissions_declared"))

    assert status == "unmet"
    assert evidence == ["Invalid YAML in .github/workflows/broken.yml"]


def test_detector_github_actions_uses_pinned_accepts_sha_and_local_actions(
    tmp_path: Path,
) -> None:
    """Accept external actions pinned to full SHAs and local action paths."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    pinned_sha = "1234567890abcdef1234567890abcdef12345678"
    (workflows / "ci.yml").write_text(
        "\n".join(
            [
                "jobs:",
                "  test:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                f"      - uses: actions/checkout@{pinned_sha}",
                "      - uses: ./github/actions/local-test",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("github_actions_uses_pinned"))

    assert status == "met"
    assert "1 external, 1 local" in evidence[0]


def test_detector_github_actions_uses_pinned_rejects_mutable_refs(
    tmp_path: Path,
) -> None:
    """Reject external actions pinned to tags or branches instead of full SHAs."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v4\n      - uses: owner/action@main\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("github_actions_uses_pinned"))

    assert status == "unmet"
    assert "Unpinned action in .github/workflows/ci.yml: actions/checkout@v4" in evidence
    assert "Unpinned action in .github/workflows/ci.yml: owner/action@main" in evidence


def test_github_actions_detectors_are_not_applicable_for_gitlab_ci(
    tmp_path: Path,
) -> None:
    """Avoid failing GitLab-only repositories for GitHub Actions-only controls."""
    repo = _make_repo(tmp_path)
    (repo / ".gitlab-ci.yml").write_text("test:\n  script: make test\n", encoding="utf-8")

    permissions_status, permissions_evidence = evaluate_detector(
        repo, DetectorSpec("github_actions_permissions_declared")
    )
    pinning_status, pinning_evidence = evaluate_detector(repo, DetectorSpec("github_actions_uses_pinned"))

    assert permissions_status == "not_applicable"
    assert pinning_status == "not_applicable"
    assert "GitLab CI detected" in permissions_evidence[0]
    assert "GitLab CI detected" in pinning_evidence[0]


def test_detector_ci_tool_usage_inspects_workflow_contents(
    tmp_path: Path,
) -> None:
    """Find security tools in generic CI filenames and ignore filename-only hints."""
    repo = _make_repo(tmp_path)
    workflows = repo / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "security.yml").write_text(
        "jobs:\n  scan:\n    steps:\n      - uses: github/codeql-action/init@v3\n",
        encoding="utf-8",
    )
    (workflows / "codeql.yml").write_text(
        "jobs:\n  placeholder:\n    steps:\n      - run: echo nothing\n",
        encoding="utf-8",
    )

    (workflows / "labels.yml").write_text(
        "name: CodeQL\njobs:\n  codeql:\n    name: CodeQL\n    steps:\n      - name: CodeQL\n        run: echo codeql\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("ci_tool_usage", {"tools": ["codeql"]}))

    assert status == "met"
    assert evidence == ["Found codeql in .github/workflows/security.yml"]


def test_detector_ci_tool_usage_supports_gitlab_ci(tmp_path: Path) -> None:
    """Find GitLab CI security templates and jobs."""
    repo = _make_repo(tmp_path)
    (repo / ".gitlab-ci.yml").write_text(
        "include:\n  - template: Security/SAST.gitlab-ci.yml\n",
        encoding="utf-8",
    )

    status, evidence = evaluate_detector(repo, DetectorSpec("ci_tool_usage", {"tools": ["sast"]}))

    assert status == "met"
    assert evidence == ["Found sast in .gitlab-ci.yml"]


@pytest.mark.parametrize(
    ("script", "expected"),
    [
        ("pip install pip-audit", "unmet"),
        ("uv run pip-audit", "met"),
        ("uv run --no-sync pip-audit", "met"),
        ("uv run --group security pip-audit", "met"),
        ("uv run --group=security -- pip-audit", "met"),
        ("python -m pip_audit", "met"),
        ("pip install pip-audit && pip-audit", "met"),
        ('echo "&&" pip-audit', "unmet"),
        ("echo example # comment; pip-audit", "unmet"),
    ],
)
def test_scanner_check_requires_invocation(tmp_path: Path, script: str, expected: str) -> None:
    """Recognize scanner commands while ignoring installation-only steps."""
    repo = _make_repo(tmp_path)
    (repo / ".gitlab-ci.yml").write_text(f"audit:\n  script:\n    - {script}\n", encoding="utf-8")
    assert evaluate_detector(repo, DetectorSpec("ci_tool_usage", {"tools": ["pip-audit"]}))[0] == expected


@pytest.mark.parametrize(
    ("control_id", "template"),
    [
        ("dependency-scanning", "Jobs/Dependency-Scanning.v2.gitlab-ci.yml"),
        ("secret-scanning", "Jobs/Secret-Detection.gitlab-ci.yml"),
    ],
)
def test_soc2_scanner_checks_accept_official_gitlab_templates(tmp_path: Path, control_id: str, template: str) -> None:
    """Recognize GitLab's default scanner template names in the built-in controls."""
    repo = _make_repo(tmp_path)
    (repo / ".gitlab-ci.yml").write_text(f"include:\n  - template: {template}\n", encoding="utf-8")
    controls = controls_for_profiles(["soc2-software"])["soc2-software"]
    control = next(control for control in controls if control.control_id == f"soc2.repo.{control_id}")
    assert evaluate_detector(repo, control.detection)[0] == "met"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, "met"),
        ({"required_pull_request_reviews": {}}, "unmet"),
        ({"required_status_checks": {"contexts": []}}, "unmet"),
        ({"enforce_admins": {"enabled": False}}, "unmet"),
        (
            {
                "required_pull_request_reviews": {
                    "required_approving_review_count": 1,
                    "bypass_pull_request_allowances": {"users": [{"login": "maintainer"}]},
                }
            },
            "unmet",
        ),
        ({"enforce_admins": None}, "unknown"),
    ],
)
def test_detector_github_branch_protection(tmp_path: Path, overrides: dict[str, object], expected: str) -> None:
    """Require reviews, status checks, and direct-push restrictions together."""
    provider = ProviderEvidence(
        provider="github",
        available=True,
        facts={
            "repo": {"default_branch": "main"},
            "branch_protection": {
                "required_pull_request_reviews": {"required_approving_review_count": 1},
                "required_status_checks": {"contexts": ["ci"]},
                "allow_force_pushes": {"enabled": False},
                "enforce_admins": {"enabled": True},
            }
            | overrides,
        },
    )

    status, evidence = evaluate_detector(_make_repo(tmp_path), DetectorSpec("provider_branch_protection"), provider)

    assert status == expected
    assert "GitHub default branch main" in evidence[0]


@pytest.mark.parametrize("provider_name", ["github", "gitlab"])
def test_detector_branch_protection_endpoint_unavailable(tmp_path: Path, provider_name: str) -> None:
    """Treat a failed protection lookup as unknown even when metadata was readable."""
    provider = ProviderEvidence(provider=provider_name, available=True, facts={"repo": {"default_branch": "main"}})
    status, _ = evaluate_detector(_make_repo(tmp_path), DetectorSpec("provider_branch_protection"), provider)
    assert status == "unknown"


@pytest.mark.parametrize(
    ("push_level", "pipeline", "eligible", "expected"),
    [
        (0, True, 2, "met"),
        (40, True, 2, "unmet"),
        (0, False, 2, "unmet"),
        (0, True, None, "unknown"),
        (0, True, 0, "unknown"),
        (0, True, 1, "unknown"),
    ],
)
def test_detector_gitlab_branch_protection(
    tmp_path: Path, push_level: int, pipeline: bool, eligible: int | None, expected: str
) -> None:
    """Check matched push restrictions along with merge and approval settings."""
    provider = ProviderEvidence(
        provider="gitlab",
        available=True,
        facts={
            "repo": {
                "default_branch": "release/main",
                "only_allow_merge_if_pipeline_succeeds": pipeline,
                "allow_merge_on_skipped_pipeline": False,
            },
            "protected_branches": [
                {"name": "release/*", "allow_force_push": False, "push_access_levels": [{"access_level": push_level}]},
            ],
            "approval_overrides_disabled": True,
            "committers_excluded_from_approval": False,
            "approval_rules": [
                {
                    "rule_type": "regular",
                    "approvals_required": 1,
                    "protected_branch_names": ["release/*"],
                    "eligible_approver_count": eligible,
                },
            ],
        },
    )
    status, _ = evaluate_detector(_make_repo(tmp_path), DetectorSpec("provider_branch_protection"), provider)
    assert status == expected


@pytest.mark.parametrize(
    ("origin", "canonical"),
    [
        (
            "https://alice:git-secret@github.com/acme/demo.git?token=query-secret#fragment-secret",
            "https://github.com/acme/demo",
        ),
        ("https://alice:git-secret@example.com/acme/demo.git?token=query-secret#fragment-secret", None),
        ("ssh://git@gitlab.com/group/subgroup/demo.git", "https://gitlab.com/group/subgroup/demo"),
    ],
)
def test_provider_evidence_sanitizes_origin(
    monkeypatch: pytest.MonkeyPatch, origin: str, canonical: str | None
) -> None:
    """Keep credentials, query values, and fragments out of report evidence."""
    monkeypatch.setattr("repoman.compliance.providers._git_origin_url", lambda *_: origin)
    monkeypatch.setattr("repoman.compliance.providers.shutil.which", lambda _: None)
    evidence = collect_provider_evidence(".")
    assert evidence.remote_url == canonical
    assert all(secret not in repr(evidence) for secret in ("git-secret", "query-secret", "fragment-secret"))


def test_collect_provider_evidence_reads_github_with_gh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Collect GitHub provider facts through mocked gh calls."""
    repo = _make_repo(tmp_path)

    def fake_which(command: str) -> str | None:
        return f"/bin/{command}" if command == "gh" else None

    def fake_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if command[:4] == ["git", "config", "--get", "remote.origin.url"]:
            return SimpleNamespace(returncode=0, stdout="https://github.com/acme/demo.git\n")
        assert command[:4] == ["gh", "api", "--hostname", "github.com"]
        api_path = command[4]
        if api_path == "orgs/acme/audit-log":
            assert command[5:] == ["--method", "GET", "-f", "phrase=repo:acme/demo", "-f", "per_page=1"]
        payloads = {
            "repos/acme/demo": '{"default_branch":"main","private":false,"archived":false,"visibility":"public"}',
            "repos/acme/demo/branches/main/protection": '{"required_pull_request_reviews":{},"allow_force_pushes":{"enabled":false}}',
            "repos/acme/demo/collaborators?per_page=100": json.dumps([{"login": f"user-{i}"} for i in range(100)]),
            "repos/acme/demo/keys?per_page=100": "[]",
            "repos/acme/demo/actions/permissions": '{"enabled":true}',
            "orgs/acme/audit-log": "[]",
        }
        return SimpleNamespace(returncode=0, stdout=payloads[api_path])

    monkeypatch.setattr("repoman.compliance.providers.shutil.which", fake_which)
    monkeypatch.setattr("repoman.compliance.providers.subprocess.run", fake_run)

    evidence = collect_provider_evidence(str(repo))

    assert evidence.provider == "github"
    assert evidence.repository == "acme/demo"
    assert evidence.available is True
    assert evidence.facts["collaborators"] == {"count": 100, "partial": True}
    assert evidence.facts["audit_log_available"] is True


def test_collect_provider_evidence_reads_gitlab_with_glab(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Collect GitLab provider facts through mocked glab calls."""
    repo = _make_repo(tmp_path)

    def fake_which(command: str) -> str | None:
        return f"/bin/{command}" if command == "glab" else None

    def fake_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        if command[:4] == ["git", "config", "--get", "remote.origin.url"]:
            return SimpleNamespace(returncode=0, stdout="git@gitlab.com:acme/demo.git\n")
        assert command[:4] == ["glab", "api", "--hostname", "gitlab.com"]
        api_path = command[4]
        payloads = {
            "projects/acme%2Fdemo": '{"default_branch":"main","visibility":"private","archived":false}',
            "projects/acme%2Fdemo/protected_branches?per_page=100": '[{"name":"main","allow_force_push":false}]',
            "projects/acme%2Fdemo/approvals": '{"disable_overriding_approvers_per_merge_request":true}',
            "projects/acme%2Fdemo/approval_rules?per_page=100": '[{"rule_type":"regular","approvals_required":1,"protected_branches":[{"name":"main"}],"eligible_approvers":[{"id":1,"state":"active"},{"id":2,"state":"active"}]}]',
            "projects/acme%2Fdemo/members/all?per_page=100": '[{"username":"owner"}]',
            "projects/acme%2Fdemo/deploy_keys?per_page=100": "[]",
            "projects/acme%2Fdemo/audit_events": "[]",
        }
        return SimpleNamespace(returncode=0, stdout=payloads[api_path])

    monkeypatch.setattr("repoman.compliance.providers.shutil.which", fake_which)
    monkeypatch.setattr("repoman.compliance.providers.subprocess.run", fake_run)

    evidence = collect_provider_evidence(str(repo))

    assert evidence.provider == "gitlab"
    assert evidence.repository == "acme/demo"
    assert evidence.available is True
    assert evidence.facts["members"] == {"count": 1}
    assert evidence.facts["approval_overrides_disabled"] is True
    rule = evidence.facts["approval_rules"][0]
    assert rule["protected_branch_names"] == ["main"]
    assert rule["eligible_approver_count"] == 2
    assert "eligible_approvers" not in rule


def test_collect_provider_evidence_warns_when_provider_cli_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Leave provider facts unavailable when the provider CLI is missing."""
    repo = _make_repo(tmp_path)

    def fake_run(command: list[str], **_kwargs: object) -> SimpleNamespace:
        assert command[:4] == ["git", "config", "--get", "remote.origin.url"]
        return SimpleNamespace(returncode=0, stdout="https://github.com/acme/demo.git\n")

    monkeypatch.setattr("repoman.compliance.providers.shutil.which", lambda _command: None)
    monkeypatch.setattr("repoman.compliance.providers.subprocess.run", fake_run)

    evidence = collect_provider_evidence(str(repo))

    assert evidence.provider == "github"
    assert evidence.available is False
    assert "gh" in evidence.warnings[0]


def test_detector_text_match_regex_and_manual_only(tmp_path: Path) -> None:
    """Support regex text matching and manual-only detector prompts."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("Contact security@example.com for disclosure.\n", encoding="utf-8")

    regex_status, regex_evidence = evaluate_detector(
        repo,
        DetectorSpec(
            "text_match",
            {"path": "README.md", "pattern": r"security@\w+\.com", "regex": True},
        ),
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
        DetectorSpec(
            "yaml_path_exists",
            {"path": ".github/workflows/ci.yml", "yaml_path": ["jobs"]},
        ),
    )
    rule_status, rule_evidence = evaluate_detector(
        repo,
        DetectorSpec(
            "github_actions_rule",
            {"workflow_glob": ".github/workflows/*.yml", "yaml_path": ["jobs", "test"]},
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


def test_load_compliance_config_rejects_invalid_defaults_mapping(
    tmp_path: Path,
) -> None:
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


def test_load_compliance_config_accepts_null_sections_and_null_string_lists(
    tmp_path: Path,
) -> None:
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


def test_load_compliance_config_parses_report_metadata_and_not_applicable(
    tmp_path: Path,
) -> None:
    """Parse evidence-report metadata and not-applicable control statuses."""
    config = tmp_path / "compliance.yml"
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "report:",
                "  organization: Acme",
                "  system_name: Payments",
                "  audit_period_start: '2026-01-01'",
                "  audit_period_end: '2026-06-30'",
                "controls:",
                "  soc2.repo.actions-pinning:",
                "    status: not_applicable",
                "    justification: GitLab-only repository",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = load_compliance_config(config)

    assert parsed.report.organization == "Acme"
    assert parsed.report.system_name == "Payments"
    assert parsed.controls["soc2.repo.actions-pinning"].status == "not_applicable"


@pytest.mark.parametrize(
    ("content", "match"),
    [
        ("profiles: []\n", "field 'profiles' must be a mapping"),
        (
            "profiles:\n  oss-best-practices:\n    tier_target: platinum\n",
            "invalid tier_target",
        ),
        (
            "profiles:\n  oss-best-practices:\n    include: [ok, 3]\n",
            "include must be a list of strings",
        ),
        ("controls: []\n", "field 'controls' must be a mapping"),
        (
            "controls:\n  oss.docs.readme: []\n",
            "control 'oss.docs.readme' must be a mapping",
        ),
        ("controls:\n  oss.docs.readme:\n    status: maybe\n", "invalid status"),
        (
            "controls:\n  oss.docs.readme:\n    evidence: [ok, 3]\n",
            "evidence must be a list of strings",
        ),
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


def test_detected_control_can_be_manually_completed_with_evidence(
    tmp_path: Path,
) -> None:
    """Allow detector-backed controls to be completed manually with evidence."""
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

    report = analyze_compliance(repo, profile_ids=["oss-best-practices"])[0]
    control = next(item for item in report.controls if item.control_id == "oss.docs.contributing")

    assert control.status == "met"
    assert "Manual note" in control.evidence


def test_detected_control_requires_evidence_for_manual_completion(
    tmp_path: Path,
) -> None:
    """Reject detector-backed met overrides that do not provide evidence."""
    repo = _make_repo(tmp_path)
    (repo / "README.md").write_text("# Project\n", encoding="utf-8")
    (repo / "compliance.yml").write_text(
        "\n".join(
            [
                "version: 1",
                "controls:",
                "  oss.docs.contributing:",
                "    status: met",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ComplianceConfigError, match="requires evidence"):
        analyze_compliance(repo, profile_ids=["oss-best-practices"])


def test_analyze_compliance_rejects_invalid_paths_and_unknown_selected_profile(
    tmp_path: Path,
) -> None:
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


def test_analyze_compliance_skips_disabled_profiles_and_respects_include_exclude(
    tmp_path: Path,
) -> None:
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
def test_analyze_compliance_rejects_invalid_profile_configuration(tmp_path: Path, content: str, match: str) -> None:
    """Fail fast on bad profile ids and invalid include/exclude control ids."""
    repo = _make_repo(tmp_path)
    (repo / "compliance.yml").write_text(content, encoding="utf-8")

    with pytest.raises(ComplianceConfigError, match=match):
        analyze_compliance(repo, profile_ids=["oss-best-practices"])


def test_evaluate_control_handles_applicability_and_override_metadata(
    tmp_path: Path,
) -> None:
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


def test_evaluate_control_handles_waivers_manual_controls_and_status_downgrades(
    tmp_path: Path,
) -> None:
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

    with pytest.raises(ComplianceConfigError, match="requires a justification"):
        _evaluate_control(repo, manual_control, ControlOverride(status="waived"))

    with pytest.raises(ComplianceConfigError, match="requires a justification"):
        _evaluate_control(repo, manual_control, ControlOverride(status="not_applicable"))


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


def test_controls_for_profiles_returns_all_controls() -> None:
    """Group every control for starter evidence templates."""
    grouped = controls_for_profiles(["soc2-software"])

    control_ids = {control.control_id for control in grouped["soc2-software"]}
    assert "soc2.repo.branch-protection" in control_ids
    assert "soc2.repo.actions-pinning" in control_ids


def test_soc2_profile_includes_manual_evidence_heavy_requirements() -> None:
    """Keep SOC 2 readiness broad enough to cover manual evidence requirements."""
    controls_by_id = {control.control_id: control for control in BUILTIN_PROFILES["soc2-software"].controls}
    expected_manual_controls = {
        "soc2.governance.control-owner",
        "soc2.data.classification",
        "soc2.access.mfa",
        "soc2.access.least-privilege",
        "soc2.cicd.secrets-rotation",
        "soc2.change.approval-records",
        "soc2.dependencies.vuln-monitoring",
        "soc2.data.encryption",
        "soc2.data.retention",
        "soc2.availability.backup-restore",
        "soc2.third-party.service-inventory",
        "soc2.logging.retention",
        "soc2.monitoring.alerts",
        "soc2.governance.risk-assessment",
        "soc2.access.periodic-review",
        "soc2.incident.tabletop",
        "soc2.security.review",
        "soc2.availability.disaster-recovery",
        "soc2.evidence.audit-trail",
        "soc2.privacy.requests",
    }

    assert expected_manual_controls <= set(controls_by_id)
    assert all(controls_by_id[control_id].detection.kind == "manual_only" for control_id in expected_manual_controls)
    assert controls_by_id["soc2.access.mfa"].tier == "silver"
    assert controls_by_id["soc2.incident.tabletop"].tier == "gold"


def test_soc2_profile_includes_repo_specific_requirements() -> None:
    """Cover software-repository governance and supply-chain controls."""
    controls_by_id = {control.control_id: control for control in BUILTIN_PROFILES["soc2-software"].controls}
    expected_manual_controls = {
        "soc2.repo.access-review",
        "soc2.repo.ci-evidence-retention",
        "soc2.repo.vuln-disclosure-log",
        "soc2.repo.emergency-change",
        "soc2.repo.release-signing",
        "soc2.repo.release-provenance",
        "soc2.repo.audit-log-retention",
    }
    expected_detector_kinds = {
        "soc2.repo.branch-protection": "provider_branch_protection",
        "soc2.repo.codeowners": "glob_exists",
        "soc2.repo.pr-template": "glob_exists",
        "soc2.repo.security-policy": "glob_exists",
        "soc2.repo.dependency-scanning": "ci_tool_usage",
        "soc2.repo.static-analysis": "ci_tool_usage",
        "soc2.repo.secret-scanning": "ci_tool_usage",
        "soc2.repo.workflow-permissions": "github_actions_permissions_declared",
        "soc2.repo.actions-pinning": "github_actions_uses_pinned",
        "soc2.repo.sbom": "ci_tool_usage",
    }

    assert expected_manual_controls | set(expected_detector_kinds) <= set(controls_by_id)
    assert all(controls_by_id[control_id].detection.kind == "manual_only" for control_id in expected_manual_controls)
    for control_id, detection_kind in expected_detector_kinds.items():
        assert controls_by_id[control_id].detection.kind == detection_kind
    assert controls_by_id["soc2.repo.branch-protection"].tier == "silver"
    assert controls_by_id["soc2.repo.actions-pinning"].tier == "gold"
    assert all(control.criteria_refs for control in controls_by_id.values())


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


def test_report_rendering_handles_optional_sections_and_invalid_output(
    tmp_path: Path,
) -> None:
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
        summary_counts={
            "met": 1,
            "waived": 0,
            "not_applicable": 0,
            "unknown": 0,
            "unmet": 0,
        },
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
                criteria_refs=("CC5.1",),
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
    evidence_markdown = reports_to_evidence_markdown([report])
    evidence_html = reports_to_evidence_html([report])
    for evidence_format in (evidence_markdown, evidence_html):
        assert f"Requested tier: `{report.requested_tier or 'n/a'}`" in evidence_format
        assert f"Achieved tier: `{report.achieved_tier or 'none'}`" in evidence_format
        assert f"Gate passed: `{report.gate.passed}`" in evidence_format
    starter = build_starter_config(["oss-best-practices"], {})

    assert "- None" in markdown
    assert "Justification: Manually reviewed" in markdown
    assert "SOC 2 Repository Audit Evidence Report" in evidence_markdown
    assert "CC5.1" in evidence_markdown
    assert "controls:\n  {}\n" in starter

    with pytest.raises(ValueError, match="Unsupported output format"):
        write_reports([report], "text", tmp_path / "report.txt")


def test_readme_does_not_satisfy_architecture_or_rollback_controls(
    tmp_path: Path,
) -> None:
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

    assert {report.profile_id for report in reports} == {
        "soc2-software",
        "oss-best-practices",
    }
    assert all(report.gate.passed for report in reports)
