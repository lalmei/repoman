#!/usr/bin/env python3
"""Update the instantiated template coverage percentage in docs/development/testing.md.

Run from the project root:
    uv run python scripts/update_instantiated_template_coverage.py

Or use the Makefile target:
    make update-instantiated-template-coverage
"""

from pathlib import Path
import re
import sys
import tempfile

# Project root is parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOC_PATH = PROJECT_ROOT / "docs" / "development" / "testing.md"
MARKER_PATTERN = re.compile(
    r"^(- \*\*📊 Instantiated template coverage\*\*: )"
    r"(\d+(?:\.\d+)?)(% \(update with.*?\)) "
    r"(<!-- instantiated-template-coverage: )(\d+(?:\.\d+)?)(% -->)$",
    re.MULTILINE,
)


def main() -> int:
    sys.path.insert(0, str(PROJECT_ROOT))

    from tests.ci_runner import parse_coverage_percent, run_make_command
    from tests.template_testing import cleanup_project_artifacts, instantiate_template

    answers_file = PROJECT_ROOT / "tests" / "fixtures" / "default_copier_answers.yml"
    if not answers_file.exists():
        print("error: default answers file not found:", answers_file, file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="repoman-coverage-") as tmp_dir:
        tmp_path = Path(tmp_dir)
        project_dir = instantiate_template(
            output_dir=tmp_path,
            project_name="test-project",
            answers_file=answers_file,
            force=True,
        )
        try:
            for cmd in ("setup", "format", "fix"):
                result = run_make_command(project_dir, cmd)
                if result.returncode != 0:
                    print(f"error: make {cmd} failed", file=sys.stderr)
                    return 1
            result = run_make_command(project_dir, "test-coverage-report")
            if result.returncode != 0:
                print("error: make test-coverage-report failed", file=sys.stderr)
                return 1
        finally:
            cleanup_project_artifacts(project_dir)

    pct = parse_coverage_percent(result.stdout)
    if pct is None:
        print("error: could not parse coverage from output", file=sys.stderr)
        return 1

    text = DOC_PATH.read_text()
    new_value = f"{pct:.2f}"

    def replacer(match: re.Match[str]) -> str:
        prefix, _old1, middle, comment_prefix, _old2, comment_suffix = match.groups()
        return f"{prefix}{new_value}{middle} {comment_prefix}{new_value}{comment_suffix}"

    new_text = MARKER_PATTERN.sub(replacer, text)
    if new_text == text:
        print("error: could not find instantiated-template-coverage line in", DOC_PATH, file=sys.stderr)
        return 1

    DOC_PATH.write_text(new_text)
    print(f"Updated instantiated template coverage to {new_value}% in {DOC_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
