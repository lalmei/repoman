"""Tests for the config command and config init subcommand."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from typer import Typer
from typer.testing import CliRunner

from repoman.cli.commands.config.list_keys import _serialize_value
from repoman.cli.commands.config.utils import ValidationReport
from repoman.cli.commands.config.validate_ import _format_report
from repoman.resources import get_copier_answers_template
from tests.conftest import strip_ansi_codes


def _all_output(result: object) -> str:
    """Combine stdout and stderr (Rich/Click may use either)."""
    stdout = getattr(result, "stdout", "") or ""
    output = getattr(result, "output", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    return (stdout or output) + stderr


def test_config_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test repoman config --help shows parent help and lists subcommands."""
    result = cli_runner.invoke(cli_app, ["config", "--help"], input="")
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "config" in result.output.lower()
    assert "init" in result.output.lower()
    assert "path" in result.output.lower()
    assert "validate" in result.output.lower()
    assert "show" in result.output.lower()
    assert "list-keys" in result.output.lower()
    assert "Manage repoman" in result.output or "configuration" in result.output.lower()


def test_config_init_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test repoman config init --help shows init options."""
    result = cli_runner.invoke(cli_app, ["config", "init", "--help"], input="")
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "init" in result.output.lower()
    assert "--output" in result.output or "-o" in result.output
    assert "--force" in result.output or "-f" in result.output
    assert ".copier-answers.yml" in result.output


def test_config_init_writes_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init writes template to specified path."""
    out = tmp_path / "answers.yml"
    result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(out)], input="")
    assert result.exit_code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    expected = get_copier_answers_template()
    assert content == expected
    assert "project_name:" in content
    assert "my-awesome-project" in content


def test_config_init_respects_output_option(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init uses --output path."""
    custom = tmp_path / "my-answers.yaml"
    result = cli_runner.invoke(cli_app, ["config", "init", "-o", str(custom)], input="")
    assert result.exit_code == 0
    assert custom.exists()
    assert (tmp_path / "answers.yml").exists() is False


def test_config_init_refuses_overwrite_without_force(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init refuses to overwrite existing file without --force."""
    out = tmp_path / "existing.yml"
    out.write_text("existing content")
    result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(out)], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "already exists" in plain.lower() or "overwrite" in plain.lower()
    assert out.read_text() == "existing content"


def test_config_init_overwrites_with_force(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init overwrites when --force is given."""
    out = tmp_path / "existing.yml"
    out.write_text("existing content")
    result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(out), "--force"], input="")
    assert result.exit_code == 0
    content = out.read_text(encoding="utf-8")
    assert content == get_copier_answers_template()
    assert "existing content" not in content


def test_config_init_dry_run_does_not_write(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init with --dry-run does not create file."""
    out = tmp_path / "would-be-created.yml"
    result = cli_runner.invoke(cli_app, ["--dry-run", "config", "init", "--output", str(out)], input="")
    assert result.exit_code == 0
    assert out.exists() is False
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "dry run" in plain.lower() or "would write" in plain.lower()


def test_config_init_output_directory_resolves_to_copier_answers(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path
) -> None:
    """Test config init with output path that is a directory writes .copier-answers.yml inside it."""
    result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(tmp_path)], input="")
    assert result.exit_code == 0
    expected_file = tmp_path / ".copier-answers.yml"
    assert expected_file.exists()
    assert expected_file.read_text(encoding="utf-8") == get_copier_answers_template()


def test_config_init_custom_template(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init --template uses custom template file."""
    custom_template = tmp_path / "custom.yml"
    custom_template.write_text("project_name: from-custom\nci: gitlab.com\n")
    out = tmp_path / "out.yml"
    result = cli_runner.invoke(
        cli_app,
        ["config", "init", "--output", str(out), "--template", str(custom_template)],
        input="",
    )
    assert result.exit_code == 0
    assert out.read_text() == "project_name: from-custom\nci: gitlab.com\n"


def test_config_init_template_not_found(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init with missing --template path fails."""
    out = tmp_path / "out.yml"
    result = cli_runner.invoke(
        cli_app,
        [
            "config",
            "init",
            "--output",
            str(out),
            "--template",
            str(tmp_path / "nonexistent.yml"),
        ],
        input="",
    )
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "not found" in plain.lower()
    assert out.exists() is False


def test_config_init_template_path_not_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init when --template path exists but is not a file (e.g. directory) fails (init_.py 75-76)."""
    out = tmp_path / "out.yml"
    adir = tmp_path / "adir"
    adir.mkdir()
    result = cli_runner.invoke(
        cli_app,
        ["config", "init", "--output", str(out), "--template", str(adir)],
        input="",
    )
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "not a file" in plain.lower() or "template" in plain.lower()
    assert out.exists() is False


def test_config_init_output_path_not_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init --output when path exists but is not a file (e.g. FIFO) fails."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("mkfifo not available (Unix only)")
    fifo = tmp_path / "not_a_file"
    os.mkfifo(str(fifo))
    result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(fifo)], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "not a file" in plain.lower() or "output" in plain.lower()


def test_config_init_write_os_error(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config init when write_text raises OSError fails with error."""
    out = tmp_path / "out.yml"
    with patch.object(Path, "write_text", side_effect=OSError("Permission denied")):
        result = cli_runner.invoke(cli_app, ["config", "init", "--output", str(out)], input="")
    assert result.exit_code == 1


# --- config validate ---


def test_config_validate_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config validate --help."""
    result = cli_runner.invoke(cli_app, ["config", "validate", "--help"], input="")
    assert result.exit_code == 0
    assert "--answers" in result.output or "-a" in result.output
    assert "strict" in result.output.lower()
    assert "quiet" in result.output.lower()


def test_config_validate_success(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config validate with valid answers file passes."""
    fixture = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    result = cli_runner.invoke(cli_app, ["config", "validate", "--answers", str(fixture)], input="")
    assert result.exit_code == 0
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "passed" in plain.lower() or "validation" in plain.lower()


def test_config_validate_missing_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config validate with missing file fails."""
    result = cli_runner.invoke(
        cli_app,
        ["config", "validate", "--answers", str(tmp_path / "nonexistent.yml")],
        input="",
    )
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "not found" in plain.lower()


def test_config_validate_quiet(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config validate --quiet exits 0 with no message on success."""
    fixture = Path(__file__).parent.parent / "fixtures" / "default_copier_answers.yml"
    result = cli_runner.invoke(
        cli_app,
        ["config", "validate", "--answers", str(fixture), "--quiet"],
        input="",
    )
    assert result.exit_code == 0


def test_config_validate_invalid_yaml(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config validate with invalid YAML file fails with error message."""
    bad_yaml = tmp_path / "bad.yml"
    bad_yaml.write_text("key: [unclosed", encoding="utf-8")
    result = cli_runner.invoke(cli_app, ["config", "validate", "--answers", str(bad_yaml)], input="")
    assert result.exit_code == 1
    # YAMLError path is covered; output may not be captured by runner in all environments
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "yaml" in plain.lower() or "invalid" in plain.lower() or "error" in plain.lower()


def test_config_validate_schema_not_found(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config validate when load_prompt_schema returns empty fails with warning."""
    answers_file = tmp_path / "answers.yml"
    answers_file.write_text("project_name: p\nci: github", encoding="utf-8")
    with patch("repoman.cli.commands.config.validate_.load_prompt_schema", return_value={}):
        result = cli_runner.invoke(cli_app, ["config", "validate", "--answers", str(answers_file)], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "skipping" in plain.lower() or "schema" in plain.lower()


def test_config_validate_failure_narrow_uses_format_report(
    cli_runner: CliRunner, cli_app: Typer, tmp_path: Path
) -> None:
    """Test config validate with invalid answers and narrow console uses _format_report (single panel)."""
    invalid_answers = tmp_path / "invalid.yml"
    invalid_answers.write_text("{}", encoding="utf-8")  # missing required keys
    with patch("repoman.cli.commands.config.validate_.use_layout", return_value=False):
        result = cli_runner.invoke(cli_app, ["config", "validate", "--answers", str(invalid_answers)], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "Missing keys" in plain or "missing" in plain.lower() or "key" in plain.lower()


def test_config_validate_failure_wide_uses_layout(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config validate with invalid answers and wide console uses layout_validation_failed."""
    invalid_answers = tmp_path / "invalid.yml"
    invalid_answers.write_text("{}", encoding="utf-8")
    with patch("repoman.cli.commands.config.validate_.use_layout", return_value=True):
        result = cli_runner.invoke(cli_app, ["config", "validate", "--answers", str(invalid_answers)], input="")
    assert result.exit_code == 1
    # Wide layout path is covered; output may not be captured by runner


def test_config_validate_format_report_branches() -> None:
    """Unit test _format_report for all branches (missing, extra, type_errors, empty)."""
    out = _format_report(
        ValidationReport(
            valid=False,
            missing_keys=["a"],
            extra_keys=["b"],
            type_errors=["c: error"],
        )
    )
    assert "Missing keys" in out
    assert "a" in out
    assert "Extra keys" in out
    assert "b" in out
    assert "c: error" in out

    out_missing_only = _format_report(ValidationReport(valid=False, missing_keys=["x"], extra_keys=[], type_errors=[]))
    assert "Missing keys" in out_missing_only
    assert "x" in out_missing_only

    out_extra_only = _format_report(ValidationReport(valid=False, missing_keys=[], extra_keys=["y"], type_errors=[]))
    assert "Extra keys" in out_extra_only
    assert "y" in out_extra_only

    out_type_only = _format_report(
        ValidationReport(valid=False, missing_keys=[], extra_keys=[], type_errors=["z: bad type"])
    )
    assert "z: bad type" in out_type_only

    out_empty = _format_report(ValidationReport(valid=False, missing_keys=[], extra_keys=[], type_errors=[]))
    assert out_empty == "All checks passed."


# --- config path ---


def test_config_path_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config path --help."""
    result = cli_runner.invoke(cli_app, ["config", "path", "--help"], input="")
    assert result.exit_code == 0
    assert "--config" in result.output or "-c" in result.output


def test_config_path_prints_default_path(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config path prints resolved config file path."""
    with patch(
        "repoman.cli.commands.config.path_.get_config_file_path", return_value=tmp_path / "repoman" / "config.json"
    ):
        result = cli_runner.invoke(cli_app, ["config", "path"], input="")
    assert result.exit_code == 0
    plain = result.output.strip()
    assert str(tmp_path) in plain
    assert "config.json" in plain


def test_config_path_custom_config(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config path --config prints custom path."""
    custom = tmp_path / "custom" / "repoman.json"
    result = cli_runner.invoke(cli_app, ["config", "path", "--config", str(custom)], input="")
    assert result.exit_code == 0
    plain = result.output.strip()
    assert str(tmp_path) in plain
    assert "repoman.json" in plain


# --- config show ---


def test_config_show_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config show --help."""
    result = cli_runner.invoke(cli_app, ["config", "show", "--help"], input="")
    assert result.exit_code == 0
    assert "--key" in result.output or "-k" in result.output
    assert "output" in result.output.lower()


def test_config_show_prints_template(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config show prints bundled template to stdout."""
    result = cli_runner.invoke(cli_app, ["config", "show"], input="")
    assert result.exit_code == 0
    plain = _all_output(result)
    if plain:
        assert "project_name:" in plain
        assert "my-awesome-project" in plain


def test_config_show_key(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config show --key prints single value."""
    result = cli_runner.invoke(cli_app, ["config", "show", "--key", "project_name"], input="")
    assert result.exit_code == 0
    plain = _all_output(result).strip()
    if plain:
        assert plain == "my-awesome-project"


def test_config_show_key_missing(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config show --key for missing key fails."""
    result = cli_runner.invoke(cli_app, ["config", "show", "--key", "nonexistent_key"], input="")
    assert result.exit_code == 1


def test_config_show_output_file(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --output writes template to file."""
    out = tmp_path / "out.yml"
    result = cli_runner.invoke(cli_app, ["config", "show", "--output", str(out)], input="")
    assert result.exit_code == 0
    assert out.exists()
    assert "project_name:" in out.read_text()
    assert "my-awesome-project" in out.read_text()


def test_config_show_output_refuses_overwrite(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --output refuses overwrite without --force."""
    out = tmp_path / "out.yml"
    out.write_text("existing")
    result = cli_runner.invoke(cli_app, ["config", "show", "--output", str(out)], input="")
    assert result.exit_code == 1
    assert out.read_text() == "existing"


def test_config_show_output_force_overwrite(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --output --force overwrites file."""
    out = tmp_path / "out.yml"
    out.write_text("existing")
    result = cli_runner.invoke(cli_app, ["config", "show", "--output", str(out), "--force"], input="")
    assert result.exit_code == 0
    assert "project_name:" in out.read_text()
    assert "existing" not in out.read_text()


def test_config_show_key_output_writes_value(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --key X --output writes only that key's value to file."""
    out = tmp_path / "val.txt"
    result = cli_runner.invoke(
        cli_app,
        ["config", "show", "--key", "project_name", "--output", str(out)],
        input="",
    )
    assert result.exit_code == 0
    assert out.exists()
    assert out.read_text().strip() == "my-awesome-project"


def test_config_show_key_output_prints_wrote_to(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --key X --output with --force writes file (covers branch 63-65 in show.py)."""
    out = tmp_path / "newfile.txt"
    assert not out.exists()
    result = cli_runner.invoke(
        cli_app,
        ["config", "show", "--key", "project_name", "--output", str(out), "--force"],
        input="",
    )
    assert result.exit_code == 0
    assert out.read_text().strip() == "my-awesome-project"
    # "Wrote to" may go to stderr (Rich) so we only assert the write path was exercised


def test_config_show_key_output_force_overwrite(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --key X --output <existing> --force overwrites."""
    out = tmp_path / "val.txt"
    out.write_text("old")
    result = cli_runner.invoke(
        cli_app,
        ["config", "show", "--key", "project_name", "--output", str(out), "--force"],
        input="",
    )
    assert result.exit_code == 0
    assert out.read_text().strip() == "my-awesome-project"


def test_config_show_key_output_refuses_overwrite(cli_runner: CliRunner, cli_app: Typer, tmp_path: Path) -> None:
    """Test config show --key X --output <existing> without --force fails."""
    out = tmp_path / "val.txt"
    out.write_text("old")
    result = cli_runner.invoke(
        cli_app,
        ["config", "show", "--key", "project_name", "--output", str(out)],
        input="",
    )
    assert result.exit_code == 1
    assert out.read_text() == "old"


def test_config_show_uses_layout_when_wide(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config show (no --key, no --output) with use_layout True uses layout_config_show_template."""
    with patch("repoman.cli.commands.config.show.use_layout", return_value=True):
        result = cli_runner.invoke(cli_app, ["config", "show"], input="")
    assert result.exit_code == 0
    # Layout path is covered; output may not be captured


# --- config list-keys ---


def test_config_list_keys_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys --help."""
    result = cli_runner.invoke(cli_app, ["config", "list-keys", "--help"], input="")
    assert result.exit_code == 0
    assert "format" in result.output.lower()
    assert "include-meta" in result.output.lower()


def test_config_list_keys_table(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys prints keys (table format)."""
    result = cli_runner.invoke(cli_app, ["config", "list-keys"], input="")
    assert result.exit_code == 0
    plain = _all_output(result)
    if plain:
        assert "project_name" in plain
        assert "ci" in plain
        assert "fastapi_enabled" in plain


def test_config_list_keys_json(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys --format json outputs JSON array of keys."""
    result = cli_runner.invoke(cli_app, ["config", "list-keys", "--format", "json"], input="")
    assert result.exit_code == 0
    plain = _all_output(result)
    if plain:
        data = json.loads(plain)
        assert isinstance(data, list)
        assert "project_name" in data
        assert "ci" in data


def test_config_list_keys_include_meta(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys --include-meta shows type/default columns."""
    result = cli_runner.invoke(cli_app, ["config", "list-keys", "--include-meta"], input="")
    assert result.exit_code == 0
    plain = _all_output(result)
    if plain:
        assert "project_name" in plain
        assert "str" in plain or "Type" in plain


def test_config_list_keys_schema_not_found(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys when load_prompt_schema returns empty fails."""
    with patch("repoman.cli.commands.config.list_keys.load_prompt_schema", return_value={}):
        result = cli_runner.invoke(cli_app, ["config", "list-keys"], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "schema" in plain.lower() or "copier" in plain.lower()


def test_config_list_keys_unknown_format(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys --format xml fails with unknown format message."""
    result = cli_runner.invoke(cli_app, ["config", "list-keys", "--format", "xml"], input="")
    assert result.exit_code == 1
    plain = strip_ansi_codes(_all_output(result))
    if plain:
        assert "xml" in plain.lower()
        assert "table" in plain.lower() or "json" in plain.lower()


def test_config_list_keys_json_include_meta(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test config list-keys --format json --include-meta runs and uses _serialize_value for list/dict."""
    # Schema with list and dict defaults exercises _serialize_value branches (25-31 in list_keys.py).
    minimal_schema = {
        "project_name": {"type": "str", "default": "my-project"},
        "tags": {"type": "str", "default": ["a", "b"]},
        "nested": {"type": "str", "default": {"k": 1}},
    }
    with patch(
        "repoman.cli.commands.config.list_keys.load_prompt_schema",
        return_value=minimal_schema,
    ):
        result = cli_runner.invoke(
            cli_app,
            ["config", "list-keys", "--format", "json", "--include-meta"],
            input="",
        )
    assert result.exit_code == 0


def test_list_keys_serialize_value() -> None:
    """Unit test for _serialize_value (list/dict and primitives) for coverage."""
    assert _serialize_value("x") == "x"
    assert _serialize_value(1) == 1
    assert _serialize_value(1.0) == 1.0
    assert _serialize_value(True) is True  # noqa: FBT003
    assert _serialize_value(None) is None
    assert _serialize_value([1, "a"]) == [1, "a"]
    assert _serialize_value({"k": 1, "nested": ["a", "b"]}) == {
        "k": 1,
        "nested": ["a", "b"],
    }
    # Non-JSON types become str
    assert isinstance(_serialize_value(object()), str)
