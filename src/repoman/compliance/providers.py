"""Read-only repository provider evidence collection."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from typing import Any
from urllib.parse import quote, urlsplit

from repoman.compliance.models import ProviderEvidence, utc_now_iso

DEFAULT_TIMEOUT_SECONDS = 10
PROVIDER_PAGE_SIZE = 100


def collect_provider_evidence(
    repo_path: str,
    *,
    enabled: bool = True,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> ProviderEvidence:
    """Collect best-effort provider evidence for a git repository."""
    evidence = ProviderEvidence(collected_at=utc_now_iso())
    if not enabled:
        evidence.warnings.append("Provider evidence collection disabled.")
        return evidence

    remote_url = _git_origin_url(repo_path, timeout_seconds)
    if remote_url is None:
        evidence.warnings.append("No origin remote URL found.")
        return evidence

    remote = _parse_remote(remote_url)
    if remote is None:
        evidence.warnings.append("Unsupported origin remote URL.")
        return evidence

    provider, repository = remote
    evidence.remote_url = f"https://{provider}.com/{repository}"
    evidence.provider = provider
    evidence.repository = repository
    if provider == "github":
        _collect_github(evidence, repository, timeout_seconds)
    elif provider == "gitlab":
        _collect_gitlab(evidence, repository, timeout_seconds)
    return evidence


def _git_origin_url(repo_path: str, timeout_seconds: int) -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],  # noqa: S607
            cwd=repo_path,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    remote = result.stdout.strip()
    return remote or None


def _parse_remote(remote_url: str) -> tuple[str, str] | None:
    ssh = re.fullmatch(r"git@(github\.com|gitlab\.com):(.+)", remote_url)
    if ssh:
        host, path = ssh.groups()
    else:
        try:
            url = urlsplit(remote_url)
            host = url.hostname
        except ValueError:
            return None
        if url.scheme not in {"https", "ssh"}:
            return None
        path = url.path.removeprefix("/")
    if host not in {"github.com", "gitlab.com"}:
        return None
    repository = path.rstrip("/").removesuffix(".git")
    namespace, _, _ = repository.rpartition("/")
    if not namespace or (host == "github.com" and "/" in namespace):
        return None
    if any(part in {".", ".."} or not re.fullmatch(r"[\w.-]+", part, re.ASCII) for part in repository.split("/")):
        return None
    return host.removesuffix(".com"), repository


def _collect_github(evidence: ProviderEvidence, repository: str, timeout_seconds: int) -> None:
    if shutil.which("gh") is None:
        evidence.warnings.append("GitHub CLI `gh` not found; provider evidence unavailable.")
        return

    api = ["gh", "api", "--hostname", "github.com"]
    repo_data = _run_json([*api, f"repos/{repository}"], timeout_seconds)
    if not isinstance(repo_data, dict):
        evidence.warnings.append("GitHub repository metadata unavailable from `gh api`.")
        return

    evidence.available = True
    default_branch = str(repo_data.get("default_branch") or "main")
    evidence.facts["repo"] = {
        "default_branch": default_branch,
        "private": repo_data.get("private"),
        "archived": repo_data.get("archived"),
        "visibility": repo_data.get("visibility"),
    }
    evidence.facts["branch_protection"] = _run_json(
        [*api, f"repos/{repository}/branches/{quote(default_branch, safe='')}/protection"],
        timeout_seconds,
    )
    evidence.facts["collaborators"] = _summarize_list(
        _run_json([*api, f"repos/{repository}/collaborators?per_page={PROVIDER_PAGE_SIZE}"], timeout_seconds)
    )
    evidence.facts["deploy_keys"] = _summarize_list(
        _run_json([*api, f"repos/{repository}/keys?per_page={PROVIDER_PAGE_SIZE}"], timeout_seconds)
    )
    evidence.facts["actions_permissions"] = _run_json(
        [*api, f"repos/{repository}/actions/permissions"],
        timeout_seconds,
    )
    owner, _ = repository.split("/", 1)
    audit_log = _run_json(
        [
            *api,
            f"orgs/{owner}/audit-log",
            "--method",
            "GET",
            "-f",
            f"phrase=repo:{repository}",
            "-f",
            "per_page=1",
        ],
        timeout_seconds,
    )
    evidence.facts["audit_log_available"] = audit_log is not None


def _collect_gitlab(evidence: ProviderEvidence, repository: str, timeout_seconds: int) -> None:
    if shutil.which("glab") is None:
        evidence.warnings.append("GitLab CLI `glab` not found; provider evidence unavailable.")
        return

    api = ["glab", "api", "--hostname", "gitlab.com"]
    project_id = quote(repository, safe="")
    project = _run_json([*api, f"projects/{project_id}"], timeout_seconds)
    if not isinstance(project, dict):
        evidence.warnings.append("GitLab project metadata unavailable from `glab api`.")
        return

    evidence.available = True
    default_branch = str(project.get("default_branch") or "main")
    evidence.facts["repo"] = {
        "default_branch": default_branch,
        "visibility": project.get("visibility"),
        "archived": project.get("archived"),
        "only_allow_merge_if_pipeline_succeeds": project.get("only_allow_merge_if_pipeline_succeeds"),
        "allow_merge_on_skipped_pipeline": project.get("allow_merge_on_skipped_pipeline"),
    }
    branches = _run_json(
        [*api, f"projects/{project_id}/protected_branches?per_page={PROVIDER_PAGE_SIZE}"],
        timeout_seconds,
    )
    # An unseen wildcard rule could allow a push. Use only a complete list for this control.
    if isinstance(branches, list) and len(branches) < PROVIDER_PAGE_SIZE:
        evidence.facts["protected_branches"] = branches
    approvals = _run_json([*api, f"projects/{project_id}/approvals"], timeout_seconds)
    evidence.facts["approval_overrides_disabled"] = (
        approvals.get("disable_overriding_approvers_per_merge_request") if isinstance(approvals, dict) else None
    )
    if isinstance(approvals, dict):
        evidence.facts["committers_excluded_from_approval"] = approvals.get(
            "merge_requests_disable_committers_approval"
        )
    rules = _run_json(
        [*api, f"projects/{project_id}/approval_rules?per_page={PROVIDER_PAGE_SIZE}"],
        timeout_seconds,
    )
    if isinstance(rules, list):
        evidence.facts["approval_rules"] = [
            {key: rule.get(key) for key in ("rule_type", "approvals_required", "applies_to_all_protected_branches")}
            | {
                "eligible_approver_count": _eligible_approver_count(rule.get("eligible_approvers")),
                "protected_branch_names": [
                    branch.get("name") for branch in rule.get("protected_branches") or [] if isinstance(branch, dict)
                ],
            }
            for rule in rules
            if isinstance(rule, dict)
        ]
    evidence.facts["members"] = _summarize_list(
        _run_json([*api, f"projects/{project_id}/members/all?per_page={PROVIDER_PAGE_SIZE}"], timeout_seconds)
    )
    evidence.facts["deploy_keys"] = _summarize_list(
        _run_json([*api, f"projects/{project_id}/deploy_keys?per_page={PROVIDER_PAGE_SIZE}"], timeout_seconds)
    )
    audit_events = _run_json(
        [*api, f"projects/{project_id}/audit_events"],
        timeout_seconds,
    )
    evidence.facts["audit_log_available"] = audit_events is not None


def _run_json(command: list[str], timeout_seconds: int) -> Any | None:
    try:
        result = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError:
        return None


def _summarize_list(value: Any | None) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    summary = {"count": len(value)}
    if len(value) >= PROVIDER_PAGE_SIZE:
        return summary | {"partial": True}
    return summary


def _eligible_approver_count(value: object) -> int | None:
    if not isinstance(value, list):
        return None
    return len(
        {
            user["id"]
            for user in value
            if isinstance(user, dict) and isinstance(user.get("id"), int) and user.get("state") == "active"
        }
    )
