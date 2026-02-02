#!/usr/bin/env python3
"""Regenerate tree blocks in documentation from eza --tree or tree.

Replaces content between <!-- TREE_START:id --> and <!-- TREE_END --> markers
in markdown files with actual directory tree output.

Run from the project root:
    uv run python scripts/gen_tree_docs.py

Or use the Makefile target:
    make docs-trees
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"

# Exclude patterns for tree commands (pipe-separated)
REPOMAN_EXCLUDES = (
    ".git|.venv|site|htmlcov|__pycache__|*.pyc|.pytest_cache|*.egg-info|.mypy_cache"
)
DOCS_EXCLUDES = "htmlcov"

# Tree IDs and their config: (path, depth, excludes, cwd)
# cwd: if set, run from this dir so the tree root shows path.name
TREE_SOURCES: dict[str, tuple[Path, int, str, Path | None]] = {
    "repoman": (PROJECT_ROOT, 4, REPOMAN_EXCLUDES, PROJECT_ROOT.parent),
    "docs": (DOCS_DIR, 4, DOCS_EXCLUDES, PROJECT_ROOT),
    # instantiated is handled specially in main()
}


def run_tree(path: Path, excludes: str, depth: int, *, cwd: Path | None = None) -> str:
    """Run eza --tree or tree and return output.

    Prefers eza, falls back to tree if eza is not available.

    Args:
        path: Directory to list
        excludes: Pipe-separated glob patterns to exclude
        depth: Maximum depth (-L for eza/tree)
        cwd: If set, run from this dir so tree root shows path.name

    Returns:
        Tree output as string

    Raises:
        FileNotFoundError: If neither eza nor tree is available
    """
    work_dir = cwd if cwd is not None else path
    tree_arg = path.name if cwd is not None else str(path)
    eza_path = shutil.which("eza")
    tree_path = shutil.which("tree")

    if eza_path:
        result = subprocess.run(
            [
                eza_path,
                "--tree",
                "--icons=never",
                f"--level={depth}",
                f"--ignore-glob={excludes}",
                tree_arg,
            ],
            capture_output=True,
            text=True,
            cwd=work_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        # If eza fails (e.g. bad glob), fall through to tree

    if tree_path:
        result = subprocess.run(
            [
                tree_path,
                "-L",
                str(depth),
                "-I",
                excludes,
                "--dirsfirst",
                tree_arg,
            ],
            capture_output=True,
            text=True,
            cwd=work_dir,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        raise RuntimeError(f"tree failed: {result.stderr}")

    raise FileNotFoundError(
        "Neither eza nor tree found. Install eza (https://github.com/eza-community/eza) "
        "or tree (e.g. brew install tree) to regenerate tree blocks."
    )


def replace_tree_blocks(content: str, tree_id: str, tree_output: str) -> str:
    """Replace content between TREE_START and TREE_END with a code block.

    Args:
        content: Full markdown content
        tree_id: The tree ID (for the start marker)
        tree_output: Generated tree output to insert

    Returns:
        Updated content
    """
    start_marker = f"<!-- TREE_START:{tree_id} -->"
    end_marker = "<!-- TREE_END -->"

    pattern = re.compile(
        re.escape(start_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )
    replacement = f"{start_marker}\n```\n{tree_output}\n```\n{end_marker}"
    return pattern.sub(replacement, content, count=1)


def get_instantiated_tree() -> str:
    """Instantiate template, run tree, cleanup, return output."""
    sys.path.insert(0, str(PROJECT_ROOT))

    from tests.template_testing import cleanup_project_artifacts, instantiate_template

    answers_file = PROJECT_ROOT / "tests" / "fixtures" / "default_copier_answers.yml"
    if not answers_file.exists():
        raise FileNotFoundError(f"Answers file not found: {answers_file}")

    with tempfile.TemporaryDirectory(prefix="repoman-tree-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        project_dir = instantiate_template(
            output_dir=tmp_path,
            project_name="my_project",
            answers_file=answers_file,
            force=True,
        )
        try:
            return run_tree(
                project_dir,
                excludes=REPOMAN_EXCLUDES,
                depth=5,
            )
        finally:
            cleanup_project_artifacts(project_dir)


def main() -> int:
    # Collect required tree IDs from docs
    tree_ids_needed: dict[str, list[Path]] = {}  # id -> list of files
    for md_file in DOCS_DIR.rglob("*.md"):
        text = md_file.read_text()
        for m in re.finditer(r"<!-- TREE_START:(\w+) -->", text):
            tid = m.group(1)
            if tid not in tree_ids_needed:
                tree_ids_needed[tid] = []
            tree_ids_needed[tid].append(md_file)

    if not tree_ids_needed:
        print("No TREE_START markers found in docs/")
        return 0

    # Generate trees
    trees: dict[str, str] = {}
    for tid in tree_ids_needed:
        if tid == "instantiated":
            try:
                trees[tid] = get_instantiated_tree()
            except Exception as e:
                print(
                    f"error: failed to generate instantiated tree: {e}", file=sys.stderr
                )
                return 1
        elif tid in TREE_SOURCES:
            path, depth, excludes, cwd = TREE_SOURCES[tid]
            if not path.exists():
                print(f"error: path for {tid} does not exist: {path}", file=sys.stderr)
                return 1
            try:
                trees[tid] = run_tree(path, excludes, depth, cwd=cwd)
            except Exception as e:
                print(f"error: failed to generate tree for {tid}: {e}", file=sys.stderr)
                return 1
        else:
            print(f"error: unknown tree ID: {tid}", file=sys.stderr)
            return 1

    # Replace in each file
    for tid, files in tree_ids_needed.items():
        output = trees[tid]
        for md_file in files:
            content = md_file.read_text()
            new_content = replace_tree_blocks(content, tid, output)
            if new_content != content:
                md_file.write_text(new_content)
                print(f"Updated {md_file.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
