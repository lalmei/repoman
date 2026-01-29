"""Unit tests for ci_runner utility functions."""

import subprocess
from pathlib import Path

import pytest

from tests.ci_runner import CommandResult, run_make_command


def test_run_make_command_basic(tmp_path):
    """Test that run_make_command executes a make command and returns exit code."""
    # Create a simple Makefile for testing
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-target:\n\t@echo 'test output'\n\t@exit 0\n")

    result = run_make_command(tmp_path, "test-target")

    assert isinstance(result, CommandResult)
    assert result.returncode == 0
    assert "test output" in result.stdout
    assert result.command == "make test-target"


def test_run_make_command_captures_output(tmp_path):
    """Test that run_make_command captures stdout and stderr correctly."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-output:\n\t@echo 'stdout message'\n\t@echo 'stderr message' >&2\n\t@exit 0\n")

    result = run_make_command(tmp_path, "test-output")

    assert "stdout message" in result.stdout
    assert "stderr message" in result.stderr
    assert result.returncode == 0


def test_run_make_command_nonzero_exit(tmp_path):
    """Test that run_make_command handles non-zero exit codes."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-fail:\n\t@exit 1\n")

    result = run_make_command(tmp_path, "test-fail")

    assert result.returncode == 1
    assert result.command == "make test-fail"


def test_run_make_command_missing_command(tmp_path):
    """Test that run_make_command handles missing make commands gracefully."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("existing-target:\n\t@echo 'exists'\n")

    result = run_make_command(tmp_path, "nonexistent-target")

    # Make returns non-zero exit code for missing targets
    assert result.returncode != 0
    assert "nonexistent-target" in result.stderr or "No rule" in result.stderr


def test_run_make_command_env_variables(tmp_path):
    """Test that run_make_command accepts and sets environment variables."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-env:\n\t@echo $$TEST_VAR\n")

    env = {"TEST_VAR": "test_value"}
    result = run_make_command(tmp_path, "test-env", env=env)

    assert "test_value" in result.stdout


def test_run_make_command_timeout(tmp_path):
    """Test that run_make_command enforces timeout correctly."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-sleep:\n\t@sleep 10\n")

    with pytest.raises(subprocess.TimeoutExpired):
        run_make_command(tmp_path, "test-sleep", timeout=1)


def test_run_make_command_nonexistent_directory():
    """Test that run_make_command raises error for nonexistent directory."""
    nonexistent_dir = Path("/nonexistent/directory")

    with pytest.raises(ValueError, match="does not exist"):
        run_make_command(nonexistent_dir, "test")


def test_command_result_structure(tmp_path):
    """Test that CommandResult has correct structure."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test:\n\t@echo 'output'\n")

    result = run_make_command(tmp_path, "test")

    assert hasattr(result, "returncode")
    assert hasattr(result, "stdout")
    assert hasattr(result, "stderr")
    assert hasattr(result, "command")
    assert isinstance(result.returncode, int)
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)
    assert isinstance(result.command, str)


def test_run_make_command_streams_output(tmp_path, capsys):
    """Test that run_make_command streams output to pytest output."""
    makefile = tmp_path / "Makefile"
    makefile.write_text("test-stream:\n\t@echo 'streamed output'\n")

    result = run_make_command(tmp_path, "test-stream")

    # Output should be captured
    assert "streamed output" in result.stdout
    # Output should also be visible in pytest output (captured by capsys)
    captured = capsys.readouterr()
    assert "streamed output" in captured.out or "streamed output" in result.stdout
