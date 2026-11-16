"""Credential-free tests for the generated document review CLI."""

import importlib
import json
from pathlib import Path
from types import ModuleType

import pytest
from typer import Typer
from typer.testing import CliRunner


@pytest.fixture(scope="module")
def pilot(tmp_path_factory: pytest.TempPathFactory, cli_app: Typer) -> tuple[Path, ModuleType]:
    """Generate and import the pilot through the normal scaffold path."""
    tmp_path = tmp_path_factory.mktemp("document-review")
    result = CliRunner().invoke(
        cli_app, ["create", "cli", "cli", "review-pilot", "--document-review", "-o", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    project = tmp_path / "review-pilot"
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.syspath_prepend(str(project / "src"))
        module = importlib.import_module("review_pilot.cli.main_cli")
    return project, module


def test_pilot_is_opt_in(tmp_path: Path, cli_app: Typer) -> None:
    """Standard CLI scaffolds omit the example and command."""
    result = CliRunner().invoke(cli_app, ["create", "cli", "cli", "plain-cli", "-o", str(tmp_path)])
    assert result.exit_code == 0, result.output
    project = tmp_path / "plain-cli"
    assert not (project / "document-review-example").exists()
    assert not (project / "src/plain_cli/cli/commands/document_review").exists()


def test_fixture_comparison(pilot: tuple[Path, ModuleType]) -> None:
    """Score both final outputs on the same source against a known qualifier."""
    project, cli = pilot
    example = project / "document-review-example"
    result = CliRunner().invoke(
        cli.cli_app,
        [
            "document_review",
            "summarize-document",
            str(example / "cohort.md"),
            "--mode",
            "compare",
            "--fixture",
            str(example / "fixture.json"),
        ],
    )
    assert result.exit_code == 0, result.output
    comparison = json.loads(result.stdout)
    for mode, calls, required, forbidden in (
        ("baseline", 2, False, True),
        ("reviewed", 4, True, False),
    ):
        row = comparison[mode]
        text = " ".join(claim["text"] for claim in row["summary"]["claims"])
        assert ("opt-in cohort only" in text) is required
        assert ("all users" in text) is forbidden
        assert row["calls"] == calls
    assert comparison["reviewed"]["status"] == "pass"


@pytest.mark.parametrize(
    ("variant", "status", "calls"),
    [
        ("pass", "pass", 2),
        ("unresolved", "unresolved", 4),
        ("bad citation", None, 1),
        ("malformed", None, 1),
        ("bad finding", None, 2),
        ("oversized", None, 0),
    ],
)
def test_workflow_boundaries(pilot: tuple[Path, ModuleType], variant: str, status: str | None, calls: int) -> None:
    """Check validation, clean passes, and the maximum revision budget."""
    project, _ = pilot
    workflow = importlib.import_module("review_pilot.cli.commands.document_review.workflow")
    example = project / "document-review-example"
    responses = json.loads((example / "fixture.json").read_text())
    source = (example / "cohort.md").read_text()
    if variant == "pass":
        responses["review"] = [responses["review"][1]]
    elif variant == "unresolved":
        responses["review"][1] = responses["review"][0]
    elif variant == "bad citation":
        responses["draft"][0]["claims"][0]["citation"]["end"] = 99
    elif variant == "bad finding":
        responses["review"][0]["findings"][0]["claim_index"] = 99
    elif variant == "oversized":
        source = "x" * (workflow.MAX_SOURCE_BYTES + 1)

    seen = []

    def respond(operation: str, prompt: str, _schema: object) -> str:
        seen.append(operation)
        assert "2: Processing time fell 20% for the opt-in cohort only." in prompt
        return "invalid JSON" if variant == "malformed" else json.dumps(responses[operation].pop(0))

    if status is None:
        with pytest.raises(ValueError, match=r"Citation|Invalid JSON|nonexistent claim|Source must contain"):
            workflow.summarize(source, respond, reviewed=True)
    else:
        result = workflow.summarize(source, respond, reviewed=True)
        assert result.status == status
        assert result.calls == calls
    assert len(seen) == calls
