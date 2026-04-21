"""Tests for repository inspection."""

from pathlib import Path

import yaml

from repoman.inspection import inspect_repository


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


def _write_answers(repo: Path, payload: dict[str, object]) -> Path:
    answers_file = repo / ".copier-answers.yml"
    answers_file.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return answers_file


def test_inspect_repository_non_managed_repo(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    report = inspect_repository(repo)

    assert report.managed is False
    assert report.status == "warning"
    assert report.update_readiness.ready is False
    assert "Copier answers file not found" in report.update_readiness.blockers[0]
    assert report.fatal is False


def test_inspect_repository_valid_managed_repo(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_answers(
        repo,
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
            "docs_only": False,
            "fastapi_enabled": True,
            "dataset_enabled": False,
            "python_notebooks": True,
            "python_package_command_line_name": "my-app",
        },
    )

    report = inspect_repository(repo)

    assert report.managed is True
    assert report.status == "ok"
    assert report.update_readiness.ready is True
    assert report.template.src_path == "https://example.com/template.git"
    assert report.template.commit == "deadbeef"
    assert report.features.fastapi_enabled is True
    assert report.features.python_notebooks is True
    assert report.features.cli_enabled is True


def test_inspect_repository_missing_commit_blocks_update(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_answers(
        repo,
        {
            "_src_path": "https://example.com/template.git",
            "python_package_command_line_name": "my-app",
        },
    )

    report = inspect_repository(repo)

    assert report.status == "warning"
    assert report.update_readiness.ready is False
    assert "`_src_path` is set but `_commit` is missing." in report.update_readiness.blockers


def test_inspect_repository_blank_src_path_warns(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_answers(
        repo,
        {
            "_src_path": "   ",
            "_commit": "deadbeef",
        },
    )

    report = inspect_repository(repo)

    assert report.status == "warning"
    assert report.update_readiness.ready is True
    assert "`_commit` is set but `_src_path` is missing." in report.update_readiness.warnings


def test_inspect_repository_invalid_yaml_is_fatal(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    answers_file = repo / ".copier-answers.yml"
    answers_file.write_text("_src_path: [", encoding="utf-8")

    report = inspect_repository(repo)

    assert report.status == "error"
    assert report.fatal is True
    assert report.update_readiness.ready is False
    assert "Invalid YAML in answers file" in report.update_readiness.blockers[0]


def test_inspect_repository_manifest_parse_failure(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_answers(
        repo,
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
        },
    )
    manifest = repo / ".repoman" / "extensions.yml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("version: 1\nextensions: {}\n", encoding="utf-8")

    report = inspect_repository(repo)

    assert report.status == "error"
    assert report.fatal is True
    assert report.update_readiness.ready is False
    assert "Extension manifest is invalid" in report.update_readiness.blockers[0]


def test_inspect_repository_extension_summary_extraction(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    _write_answers(
        repo,
        {
            "_src_path": "https://example.com/template.git",
            "_commit": "deadbeef",
        },
    )
    extension_answers = repo / ".repoman" / "extensions" / "command" / "foo.answers.yml"
    extension_answers.parent.mkdir(parents=True)
    extension_answers.write_text("_src_path: x\n", encoding="utf-8")
    manifest = repo / ".repoman" / "extensions.yml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "extensions": [
                    {
                        "id": "command:foo",
                        "type": "command",
                        "name": "foo",
                        "status": "active",
                        "answers_file": ".repoman/extensions/command/foo.answers.yml",
                        "template_id": "command",
                        "created_with_repoman_version": "test",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    report = inspect_repository(repo)

    assert report.extensions.exists is True
    assert report.extensions.version == 1
    assert len(report.extensions.active) == 1
    assert report.extensions.active[0].id == "command:foo"
    assert report.update_readiness.ready is True
