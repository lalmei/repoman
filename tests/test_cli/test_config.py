"""Tests for the config command and config init subcommand."""

from pathlib import Path

from typer import Typer
from typer.testing import CliRunner

from repoman.resources import get_copier_answers_template
from tests.conftest import strip_ansi_codes


def _all_output(result: object) -> str:
    """Combine stdout and stderr (Rich panels often go to stderr)."""
    out = getattr(result, "output", "")
    err = getattr(result, "stderr", None) or ""
    return out + err


def test_config_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test repoman config --help shows parent help and lists init."""
    result = cli_runner.invoke(cli_app, ["config", "--help"], input="")
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "config" in result.output.lower()
    assert "init" in result.output.lower()
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
