"""Detectors for repository-visible compliance signals."""

from __future__ import annotations

import re
import shlex
import tomllib
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from repoman.compliance.models import (
        ControlResult,
        DetectorSpec,
        ProviderEvidence,
        Status,
    )


def evaluate_detector(
    repo_path: Path,
    detection: DetectorSpec,
    provider_evidence: ProviderEvidence | None = None,
) -> tuple[Status, list[str]]:
    """Evaluate a detector and return (status, evidence)."""
    if detection.kind == "provider_branch_protection":
        return _provider_branch_protection(provider_evidence)

    handlers = {
        "file_exists": _file_exists,
        "glob_exists": _glob_exists,
        "yaml_path_exists": _yaml_path_exists,
        "text_match": _text_match,
        "github_actions_rule": _github_actions_rule,
        "github_actions_permissions_declared": _github_actions_permissions_declared,
        "github_actions_uses_pinned": _github_actions_uses_pinned,
        "ci_tool_usage": _ci_tool_usage,
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
        return "met", [f"Found {path.relative_to(repo_path).as_posix()}"]
    return "unmet", [f"Missing {path.relative_to(repo_path).as_posix()}"]


def _glob_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    patterns = params.get("patterns") or [params["pattern"]]
    matches: list[str] = []
    for pattern in patterns:
        matches.extend(path.relative_to(repo_path).as_posix() for path in repo_path.glob(str(pattern)))
    if matches:
        unique = sorted(set(matches))
        return "met", [f"Matched {path}" for path in unique]
    return "unmet", [f"No files matched {', '.join(str(p) for p in patterns)}"]


def _yaml_path_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params["path"])
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path).as_posix()}"]

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return "unmet", [f"Invalid YAML in {path.relative_to(repo_path).as_posix()}"]

    yaml_path = params.get("yaml_path", [])
    current: Any = data
    for key in yaml_path:
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        return "unmet", [f"Missing YAML path {'.'.join(yaml_path)} in {path.relative_to(repo_path).as_posix()}"]
    return "met", [f"Found YAML path {'.'.join(yaml_path)} in {path.relative_to(repo_path).as_posix()}"]


def _text_match(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params["path"])
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path).as_posix()}"]

    content = path.read_text(encoding="utf-8", errors="replace")
    pattern = str(params["pattern"])
    if params.get("regex", False):
        if re.search(pattern, content, flags=re.MULTILINE):
            return "met", [f"Matched regex in {path.relative_to(repo_path).as_posix()}: {pattern}"]
    elif pattern in content:
        return "met", [f"Found text in {path.relative_to(repo_path).as_posix()}: {pattern}"]
    return "unmet", [f"Did not find expected text in {path.relative_to(repo_path).as_posix()}"]


def _github_actions_rule(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    yaml_path = list(params.get("yaml_path", []))

    workflow_glob, matches = _workflow_matches(repo_path, params)
    if not matches:
        if _has_gitlab_ci(repo_path):
            return "not_applicable", ["GitHub Actions workflows not present; GitLab CI detected."]
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
            found_in.append(path.relative_to(repo_path).as_posix())

    if found_in:
        return "met", [f"Found workflow rule in {path}" for path in sorted(found_in)]
    return "unmet", [f"Did not find workflow rule {'.'.join(yaml_path)}"]


def _github_actions_permissions_declared(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    workflow_glob, matches = _workflow_matches(repo_path, params)
    if not matches:
        if _has_gitlab_ci(repo_path):
            return "not_applicable", ["GitHub Actions workflows not present; GitLab CI detected."]
        return "unmet", [f"No workflow files matched {workflow_glob}"]

    failures: list[str] = []
    passing: list[str] = []
    for path in matches:
        relative = path.relative_to(repo_path).as_posix()
        data = _load_workflow(path, relative, failures)
        if data is None:
            continue
        if "permissions" in data:
            passing.append(f"{relative} declares top-level permissions")
            continue
        jobs = data.get("jobs")
        if not isinstance(jobs, dict) or not jobs:
            failures.append(f"Missing jobs mapping in {relative}")
            continue
        missing_jobs = sorted(
            job_name for job_name, job in jobs.items() if not isinstance(job, dict) or "permissions" not in job
        )
        if missing_jobs:
            failures.append(f"Missing permissions in {relative} jobs: {', '.join(str(job) for job in missing_jobs)}")
        else:
            passing.append(f"{relative} declares permissions for every job")

    if failures:
        return "unmet", failures
    return "met", passing


def _github_actions_uses_pinned(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    workflow_glob, matches = _workflow_matches(repo_path, params)
    if not matches:
        if _has_gitlab_ci(repo_path):
            return "not_applicable", ["GitHub Actions workflows not present; GitLab CI detected."]
        return "unmet", [f"No workflow files matched {workflow_glob}"]

    failures: list[str] = []
    pinned_count = 0
    local_count = 0
    for path in matches:
        relative = path.relative_to(repo_path).as_posix()
        data = _load_workflow(path, relative, failures)
        if data is None:
            continue
        for action_ref in _action_uses(data):
            if action_ref.startswith("./"):
                local_count += 1
                continue
            if re.search(r"@[0-9a-fA-F]{40}$", action_ref):
                pinned_count += 1
                continue
            failures.append(f"Unpinned action in {relative}: {action_ref}")

    if failures:
        return "unmet", failures
    return "met", [
        f"All external workflow actions are pinned to full commit SHAs ({pinned_count} external, {local_count} local)."
    ]


def _ci_tool_usage(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    tools = [str(tool).lower() for tool in params.get("tools", [])]
    workflow_globs = list(
        params.get(
            "workflow_globs",
            [
                ".github/workflows/*.y*ml",
                ".gitlab-ci.yml",
                ".gitlab/**/*.y*ml",
            ],
        )
    )
    matches = sorted({path for pattern in workflow_globs for path in repo_path.glob(str(pattern)) if path.is_file()})
    artifacts = sorted(
        {
            path
            for pattern in params.get("artifact_globs", [])
            for path in repo_path.glob(str(pattern))
            if path.is_file()
        }
    )
    invalid: list[str] = []
    found = [f"Found configured evidence in {path.relative_to(repo_path).as_posix()}" for path in artifacts]
    for path in matches:
        relative = path.relative_to(repo_path).as_posix()
        data = _load_workflow(path, relative, invalid)
        if data is None:
            continue
        searchable = "\n".join(_workflow_tool_references(data)).lower()
        for tool in tools:
            if re.search(rf"(?<![\w-]){re.escape(tool)}(?:-action)?(?![\w-])", searchable):
                found.append(f"Found {tool} in {relative}")

    if found:
        return "met", sorted(set(found))
    evidence = [f"Did not find CI tool usage for: {', '.join(tools)}"]
    evidence.extend(invalid)
    return "unmet", evidence


def _make_target_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params.get("path", "Makefile"))
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path).as_posix()}"]

    target = str(params["target"])
    pattern = re.compile(rf"^{re.escape(target)}\s*:", flags=re.MULTILINE)
    content = path.read_text(encoding="utf-8", errors="replace")
    if pattern.search(content):
        return "met", [f"Found make target {target} in {path.relative_to(repo_path).as_posix()}"]
    return "unmet", [f"Missing make target {target} in {path.relative_to(repo_path).as_posix()}"]


def _pyproject_field_exists(repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    path = repo_path / str(params.get("path", "pyproject.toml"))
    if not path.exists():
        return "unmet", [f"Missing {path.relative_to(repo_path).as_posix()}"]

    with open(path, "rb") as f:
        data = tomllib.load(f)

    fields = list(params.get("field_path", []))
    current: Any = data
    for field in fields:
        if isinstance(current, dict) and field in current:
            current = current[field]
            continue
        return "unmet", [f"Missing TOML path {'.'.join(fields)} in {path.relative_to(repo_path).as_posix()}"]
    return "met", [f"Found TOML path {'.'.join(fields)} in {path.relative_to(repo_path).as_posix()}"]


def _manual_only(_repo_path: Path, params: dict[str, Any]) -> tuple[Status, list[str]]:
    prompt = str(params.get("prompt", "Manual evidence required in compliance.yml"))
    return "unknown", [prompt]


def _provider_branch_protection(
    provider_evidence: ProviderEvidence | None,
) -> tuple[Status, list[str]]:
    if provider_evidence is None:
        return "unknown", ["Provider evidence was not collected."]
    if provider_evidence.provider not in {"github", "gitlab"}:
        return "unknown", ["Branch protection provider evidence is unavailable."]
    if not provider_evidence.available:
        return "unknown", provider_evidence.warnings or ["Provider evidence is unavailable."]

    repo = provider_evidence.facts.get("repo")
    if not isinstance(repo, dict):
        return "unknown", ["Provider repository metadata did not include default branch."]
    default_branch = str(repo.get("default_branch") or "main")

    if provider_evidence.provider == "github":
        return _github_branch_protection(provider_evidence, default_branch)
    return _gitlab_branch_protection(provider_evidence, default_branch, repo)


def _github_branch_protection(provider_evidence: ProviderEvidence, default_branch: str) -> tuple[Status, list[str]]:
    label = f"GitHub default branch {default_branch}"
    protection = provider_evidence.facts.get("branch_protection")
    if not isinstance(protection, dict):
        return "unknown", [f"{label} protection settings were unavailable."]

    reviews = protection.get("required_pull_request_reviews") or {}
    checks = protection.get("required_status_checks") or {}
    bypass = reviews.get("bypass_pull_request_allowances") or {}
    if (
        not isinstance(reviews.get("required_approving_review_count"), int)
        or reviews["required_approving_review_count"] < 1
    ):
        return "unmet", [f"{label} does not require an approving pull request review."]
    if not (checks.get("checks") or checks.get("contexts")):
        return "unmet", [f"{label} does not require status checks."]
    force_pushes = (protection.get("allow_force_pushes") or {}).get("enabled")
    enforce_admins = (protection.get("enforce_admins") or {}).get("enabled")
    if force_pushes is True or enforce_admins is False or any(bypass.get(key) for key in ("users", "teams", "apps")):
        return "unmet", [f"{label} allows a push or pull request bypass."]
    if force_pushes is not False or enforce_admins is not True:
        return "unknown", [f"{label} direct-push restrictions could not be verified."]
    return "met", [f"{label} requires reviewed pull requests and passing checks, with direct pushes restricted."]


def _gitlab_branch_protection(
    provider_evidence: ProviderEvidence, default_branch: str, repo: dict[str, Any]
) -> tuple[Status, list[str]]:
    label = f"GitLab default branch {default_branch}"
    branches = provider_evidence.facts.get("protected_branches")
    if not isinstance(branches, list):
        return "unknown", [f"{label} protection rules were unavailable or incomplete."]
    matching = [branch for branch in branches if _matches_gitlab_branch(branch, default_branch)]
    if not matching:
        return "unmet", [f"{label} is not protected."]

    push_levels = [branch.get("push_access_levels") for branch in matching]
    if any(branch.get("allow_force_push") is True for branch in matching) or any(
        _gitlab_push_allowed(entry) for levels in push_levels if isinstance(levels, list) for entry in levels
    ):
        return "unmet", [f"{label} allows a direct or force push."]
    if any(not isinstance(levels, list) for levels in push_levels) or any(
        branch.get("allow_force_push") is not False for branch in matching
    ):
        return "unknown", [f"{label} direct-push restrictions could not be verified."]

    pipeline = repo.get("only_allow_merge_if_pipeline_succeeds")
    skip_pipeline = repo.get("allow_merge_on_skipped_pipeline")
    if pipeline is False or skip_pipeline is True:
        return "unmet", [f"{label} can merge without a successful pipeline."]
    approvals = provider_evidence.facts.get("approval_rules")
    enforce_approvals = provider_evidence.facts.get("approval_overrides_disabled")
    if enforce_approvals is False:
        return "unmet", [f"{label} permits approval rule overrides."]
    if (
        pipeline is not True
        or skip_pipeline is not False
        or enforce_approvals is not True
        or not isinstance(approvals, list)
    ):
        return "unknown", [f"{label} approval requirements or pipeline settings could not be verified."]
    # GitLab can auto-approve an impossible rule. Committer exclusions are request-specific.
    if provider_evidence.facts.get("committers_excluded_from_approval") is not False:
        return "unknown", [f"{label} approval eligibility could not be verified."]
    if any(_gitlab_requires_approval(rule, default_branch) for rule in approvals):
        return "met", [
            f"{label} requires reviewed merge requests and successful pipelines, with direct pushes restricted."
        ]
    return "unknown", [f"No mandatory approval rule applicable to {label} could be verified."]


def _matches_gitlab_branch(branch: object, default_branch: str) -> bool:
    if not isinstance(branch, dict) or not isinstance(branch.get("name"), str):
        return False
    pattern = re.escape(branch["name"]).replace(r"\*", ".*")
    return re.fullmatch(pattern, default_branch) is not None


def _gitlab_push_allowed(entry: object) -> bool:
    return isinstance(entry, dict) and (
        bool(entry.get("access_level"))
        or any(entry.get(key) is not None for key in ("user_id", "group_id", "deploy_key_id"))
    )


def _gitlab_requires_approval(rule: dict[str, Any], default_branch: str) -> bool:
    required = rule.get("approvals_required")
    if rule.get("rule_type") not in {"regular", "any_approver"} or not isinstance(required, int) or required < 1:
        return False
    eligible = rule.get("eligible_approver_count")
    # Reserve one approver for the possibility that they author the merge request.
    if not isinstance(eligible, int) or eligible <= required:
        return False
    return rule.get("applies_to_all_protected_branches") is True or any(
        _matches_gitlab_branch({"name": name}, default_branch) for name in rule.get("protected_branch_names", [])
    )


def _workflow_matches(repo_path: Path, params: dict[str, Any]) -> tuple[str, list[Path]]:
    workflow_glob = str(params.get("workflow_glob", ".github/workflows/*.y*ml"))
    return workflow_glob, sorted(repo_path.glob(workflow_glob))


def _load_workflow(path: Path, relative: str, failures: list[str]) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        failures.append(f"Invalid YAML in {relative}")
        return None
    if not isinstance(data, dict):
        failures.append(f"Workflow {relative} must contain a mapping")
        return None
    return data


def _action_uses(value: Any) -> list[str]:
    uses: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "uses" and isinstance(nested, str):
                uses.append(nested)
            else:
                uses.extend(_action_uses(nested))
    elif isinstance(value, list):
        for item in value:
            uses.extend(_action_uses(item))
    return uses


def _has_gitlab_ci(repo_path: Path) -> bool:
    return (repo_path / ".gitlab-ci.yml").exists() or any(repo_path.glob(".gitlab/**/*.y*ml"))


def _workflow_tool_references(workflow: dict[str, Any]) -> list[str]:
    references: list[str] = []
    jobs = workflow.get("jobs")
    if isinstance(jobs, dict):
        for job in jobs.values():
            if not isinstance(job, dict):
                continue
            steps = job.get("steps")
            entries = [job, *steps] if isinstance(steps, list) else [job]
            for entry in entries:
                if isinstance(entry, dict):
                    uses = entry.get("uses")
                    if isinstance(uses, str):
                        references.append(uses.partition("@")[0])
                    references.extend(_command_names(entry.get("run")))
        return references

    for job in workflow.values():
        if isinstance(job, dict):
            for key in ("script", "before_script", "after_script"):
                references.extend(_command_names(job.get(key)))
    includes = workflow.get("include")
    for include in includes if isinstance(includes, list) else [includes]:
        if isinstance(include, dict):
            for key in ("template", "component"):
                if isinstance(value := include.get(key), str):
                    references.append(value.partition("@")[0])
    return references


_SHELL_OPERATORS = re.compile(r"""'[^']*'|"(?:\\.|[^"\\])*"|\\.|(?P<separator>[;&|]+)|(?P<comment>(?<![^\s;&|])\#)""")
_LAUNCHER_OPTIONS_WITH_VALUES = {
    "--extra",
    "--from",
    "--group",
    "--no-group",
    "--only-group",
    "--project",
    "--python",
    "--spec",
    "--with",
    "--with-editable",
    "--with-requirements",
    "-p",
}
_LAUNCHER_FLAGS = {
    "--all-extras",
    "--all-groups",
    "--frozen",
    "--isolated",
    "--locked",
    "--no-dev",
    "--no-project",
    "--no-sync",
    "--offline",
    "--quiet",
    "--verbose",
    "--yes",
    "-q",
    "-v",
    "-y",
}


def _command_names(value: object) -> list[str]:
    if isinstance(value, list):
        return [name for item in value for name in _command_names(item)]
    if not isinstance(value, str):
        return []

    names = []
    for line in value.splitlines():
        for segment in _shell_segments(line):
            try:
                command = shlex.split(segment)
            except ValueError:
                continue
            while command and re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", command[0]):
                command.pop(0)
            for launcher in (["uv", "run"], ["uvx"], ["pipx", "run"], ["npx"], ["python", "-m"], ["python3", "-m"]):
                if command[: len(launcher)] == launcher:
                    command = _launcher_command(command[len(launcher) :])
                    break
            if command:
                name = command[0].rsplit("/", 1)[-1].removesuffix(".exe")
                names.append(name.replace("_", "-"))
    return names


def _shell_segments(line: str) -> Iterable[str]:
    start = 0
    for match in _SHELL_OPERATORS.finditer(line):
        if match["comment"]:
            yield line[start : match.start()]
            return
        if match["separator"]:
            yield line[start : match.start()]
            start = match.end()
    yield line[start:]


def _launcher_command(arguments: list[str]) -> list[str]:
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            return arguments[index + 1 :]
        if not argument.startswith("-"):
            return arguments[index:]
        option, equals, _ = argument.partition("=")
        if option in _LAUNCHER_OPTIONS_WITH_VALUES:
            index += 1 if equals else 2
        elif argument in _LAUNCHER_FLAGS:
            index += 1
        else:
            return []
    return []
