"""Tests for the repoman_test sync helper script."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml


def _load_module() -> Any:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "sync_repoman_test.py"
    spec = importlib.util.spec_from_file_location("sync_repoman_test", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_normalize_copier_answers_removes_only_volatile_keys(tmp_path: Path) -> None:
    """Normalization drops volatile Copier metadata but preserves managed extension data."""
    module = _load_module()
    answers_path = tmp_path / ".copier-answers.yml"
    answers_path.write_text(
        yaml.safe_dump(
            {
                "_commit": "abc123",
                "_src_path": "/example/workspace",
                "_vcs_ref": "mainline",
                "_repoman_extensions": {"instances": []},
                "project_name": "repoman-test",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    module.normalize_copier_answers(answers_path)

    result = yaml.safe_load(answers_path.read_text(encoding="utf-8"))
    assert result == {
        "_repoman_extensions": {"instances": []},
        "project_name": "repoman-test",
    }


def test_replace_repo_contents_preserves_git_directory(tmp_path: Path) -> None:
    """Repo replacement keeps `.git` intact while replacing other files."""
    module = _load_module()
    staged_repo = tmp_path / "staged"
    target_repo = tmp_path / "target"
    staged_repo.mkdir()
    target_repo.mkdir()
    (target_repo / ".git").mkdir()
    (target_repo / "obsolete.txt").write_text("old", encoding="utf-8")
    (staged_repo / "fresh.txt").write_text("new", encoding="utf-8")

    module.replace_repo_contents(staged_repo, target_repo)

    assert (target_repo / ".git").is_dir()
    assert not (target_repo / "obsolete.txt").exists()
    assert (target_repo / "fresh.txt").read_text(encoding="utf-8") == "new"


def test_bootstrap_repo_renames_generated_project_into_staging_location(tmp_path: Path) -> None:
    """Bootstrap normalizes the staged directory name after `repoman create`."""
    module = _load_module()
    temp_root = tmp_path / "temp"
    temp_root.mkdir()
    generated_repo = temp_root / "repoman-test"
    generated_repo.mkdir()

    calls: list[tuple[list[str], Path]] = []

    def fake_run_command(args: list[str], cwd: Path) -> None:
        calls.append((args, cwd))

    module.run_command = fake_run_command

    staged_repo = module.bootstrap_repo(
        repoman_repo=tmp_path,
        answers_file=tmp_path / "answers.yml",
        project_name="repoman-test",
        temp_root=temp_root,
    )

    assert len(calls) == 1
    assert staged_repo == temp_root / module.STAGED_REPO_DIRNAME
    assert staged_repo.is_dir()
    assert not generated_repo.exists()
