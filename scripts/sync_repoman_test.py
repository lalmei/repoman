"""Sync the managed repoman_test repository from the local repoman template."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

VOLATILE_COPIER_KEYS = {
    "_commit",
    "_src_path",
    "_vcs_ref",
}
STAGED_REPO_DIRNAME = "repoman_test"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repoman-repo", type=Path, required=True, help="Path to the repoman repository root.")
    parser.add_argument("--target-repo", type=Path, required=True, help="Path to the checked-out repoman_test repo.")
    parser.add_argument("--answers-file", type=Path, required=True, help="Canonical answers file for bootstrap runs.")
    parser.add_argument(
        "--project-name",
        required=True,
        help="Project name to pass to `repoman create` during bootstrap.",
    )
    return parser.parse_args()


def run_command(args: list[str], cwd: Path) -> None:
    """Run a command and stream its output."""
    subprocess.run(args, cwd=cwd, check=True)


def remove_path(path: Path) -> None:
    """Remove a file, symlink, or directory tree."""
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def copy_entry(source: Path, destination: Path) -> None:
    """Copy a single file or directory while preserving metadata where possible."""
    if source.is_dir() and not source.is_symlink():
        shutil.copytree(source, destination, dirs_exist_ok=True)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination, follow_symlinks=False)


def replace_repo_contents(staged_repo: Path, target_repo: Path) -> None:
    """Replace target repo contents with staged output while preserving `.git`."""
    for child in target_repo.iterdir():
        if child.name == ".git":
            continue
        remove_path(child)

    for child in staged_repo.iterdir():
        if child.name == ".git":
            continue
        copy_entry(child, target_repo / child.name)


def normalize_copier_answers(path: Path) -> None:
    """Drop volatile Copier metadata that would otherwise create noisy CI diffs."""
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in answers file, found: {type(data).__name__}")

    for key in VOLATILE_COPIER_KEYS:
        data.pop(key, None)

    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def bootstrap_repo(repoman_repo: Path, answers_file: Path, project_name: str, temp_root: Path) -> Path:
    """Create the managed smoke repo from scratch in a staging directory."""
    run_command(
        [
            "uv",
            "run",
            "python",
            "-m",
            "repoman",
            "create",
            "--project_name",
            project_name,
            "--answers",
            str(answers_file),
            "--output",
            str(temp_root),
            "--template",
            str(repoman_repo),
            "--force",
        ],
        cwd=repoman_repo,
    )
    generated_repo = temp_root / project_name
    staged_repo = temp_root / STAGED_REPO_DIRNAME
    generated_repo.rename(staged_repo)
    return staged_repo


def update_repo(repoman_repo: Path, target_repo: Path, temp_root: Path) -> Path:
    """Copy the current smoke repo into staging and apply `repoman update` there."""
    staged_repo = temp_root / STAGED_REPO_DIRNAME
    shutil.copytree(
        target_repo,
        staged_repo,
        ignore=shutil.ignore_patterns(".git"),
    )
    run_command(
        [
            "uv",
            "run",
            "python",
            "-m",
            "repoman",
            "update",
            str(staged_repo),
            "--answers",
            str(staged_repo / ".copier-answers.yml"),
            "--template",
            str(repoman_repo),
        ],
        cwd=repoman_repo,
    )
    return staged_repo


def validate_staged_repo(staged_repo: Path) -> None:
    """Run smoke validation before syncing staged output into the target repo."""
    run_command(["uv", "sync"], cwd=staged_repo)
    run_command(["make", "test"], cwd=staged_repo)


def main() -> int:
    """Execute the managed smoke-repo sync."""
    args = parse_args()
    repoman_repo = args.repoman_repo.resolve()
    target_repo = args.target_repo.resolve()
    answers_file = args.answers_file.resolve()

    if not repoman_repo.exists():
        raise FileNotFoundError(f"repoman repo not found: {repoman_repo}")
    if not target_repo.exists():
        raise FileNotFoundError(f"target repo not found: {target_repo}")
    if not answers_file.exists():
        raise FileNotFoundError(f"answers file not found: {answers_file}")

    with tempfile.TemporaryDirectory(prefix="repoman-test-sync-") as temp_dir_name:
        temp_root = Path(temp_dir_name)
        answers_path = target_repo / ".copier-answers.yml"

        if answers_path.exists():
            staged_repo = update_repo(repoman_repo, target_repo, temp_root)
        else:
            staged_repo = bootstrap_repo(repoman_repo, answers_file, args.project_name, temp_root)

        normalize_copier_answers(staged_repo / ".copier-answers.yml")
        validate_staged_repo(staged_repo)
        replace_repo_contents(staged_repo, target_repo)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}: {exc.cmd}", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc
