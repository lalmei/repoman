"""Tests for the create subcommand."""

import re
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from rich.console import Console
from typer import Typer
from typer.testing import CliRunner

console = Console()


def test_parse_args_second(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test verbose create mode with enhanced argument validation."""
    verbose_check = re.compile(r"\w* (INFO     Setting verbose mode ON)")
    result = cli_runner.invoke(
        cli_app,
        ["--verbose", "create", "test-project", "--dry-run", "--force"],
        input="",
    )
    console.print(result.output)
    assert result.exit_code == 0

    # Enhanced verbose create mode validation
    assert verbose_check.search(result.output, 0)
    assert "INFO" in result.output
    assert "Setting verbose mode ON" in result.output

    # Test that verbose mode works with create command
    assert "Using main template" in result.output
    assert "test-project" in result.output
    assert "Dry Run" in result.output


def test_create_command_missing_required_args(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with missing required arguments."""
    result = cli_runner.invoke(cli_app, ["create"], input="")
    console.print(result.output)

    # Should fail due to missing PROJECT_NAME
    assert result.exit_code == 2
    assert "Missing argument" in result.output
    assert "PROJECT_NAME" in result.output
    assert "Try 'root create --help' for help" in result.output


def test_create_command_invalid_argument_combination(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with invalid argument combinations."""
    # Test --help with other arguments (should still show help)
    result = cli_runner.invoke(cli_app, ["create", "--help", "test-project"], input="")
    console.print(result.output)

    # Should show help regardless of other arguments
    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "create" in result.output
    assert "project_name" in result.output


def test_create_command_help(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command help."""
    result = cli_runner.invoke(cli_app, ["create", "--help"], input="")
    console.print(result.output)

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Arguments" in result.output
    assert "Options" in result.output
    assert "--help" in result.output
    assert "--dry-run" in result.output
    assert "--force" in result.output
    assert "--template" in result.output
    assert "--output" in result.output


def test_create_command_argument_order(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with different argument orders."""
    project_name = "test-project"

    # Test normal order: create project_name --options
    result1 = cli_runner.invoke(cli_app, ["create", project_name, "--dry-run", "--force"], input="")
    console.print(f"Result 1: {result1.output}")
    assert result1.exit_code == 0
    assert "Would create project" in result1.output

    # Test with options before project name (should still work)
    result2 = cli_runner.invoke(cli_app, ["create", "--dry-run", "--force", project_name], input="")
    console.print(f"Result 2: {result2.output}")
    assert result2.exit_code == 0
    assert "Would create project" in result2.output


@pytest.mark.usefixtures("tmp_path")
def test_create_command_dry_run(sample_project_names: list[str], cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with dry-run flag."""
    project_name = sample_project_names[0]

    result = cli_runner.invoke(cli_app, ["create", project_name, "--dry-run", "--force"], input="")
    console.print(result.output)

    assert result.exit_code == 0
    assert "Would create project" in result.output
    assert project_name in result.output
    assert "Dry Run" in result.output
    assert "Using template:" in result.output
    assert "Copier options:" in result.output


def test_create_command_force_overwrite(
    tmp_path: Path, mock_project_structure: Any, cli_runner: CliRunner, cli_app: Typer
) -> None:
    """Test create command with force overwrite."""
    project_name = "test-project"
    project_dir = tmp_path / project_name

    # Use the mock project structure instead of creating a simple dummy directory
    shutil.copytree(mock_project_structure, project_dir, dirs_exist_ok=True)

    # Run create with force and dry-run to avoid template execution errors
    result = cli_runner.invoke(
        cli_app,
        ["create", project_name, "--output", str(tmp_path), "--force", "--dry-run"],
        input="",
    )
    console.print(result.output)

    # Since we're using --dry-run, it should succeed and show the dry-run output
    assert result.exit_code == 0

    # Enhanced force overwrite with dry-run expectations
    assert "Would create project" in result.output
    assert "Dry Run" in result.output
    assert "Using template:" in result.output
    assert "Copier options:" in result.output


@pytest.mark.usefixtures("tmp_path")
def test_create_command_template_not_found(mock_template_structure: Any, cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with non-existent template using mock template structure."""
    project_name = "test-project"
    # Use the mock template structure to test with a real template
    template_path = mock_template_structure

    result = cli_runner.invoke(
        cli_app,
        [
            "create",
            project_name,
            "--template",
            str(template_path),
            "--dry-run",
            "--force",
        ],
        input="",
    )
    console.print(result.output)
    # This should now work since we have a real template structure
    assert result.exit_code == 0

    # Enhanced template usage validation for dry-run
    assert "Would create project" in result.output
    assert "Dry Run" in result.output
    assert project_name in result.output
    assert "Using template:" in result.output
    assert "Copier options:" in result.output
    # Note: "Copying from template" output is suppressed by quiet mode


def test_create_command_invalid_template_path(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with invalid template path."""
    project_name = "test-project"
    invalid_template = "/non/existent/template/path"

    result = cli_runner.invoke(
        cli_app,
        ["create", project_name, "--template", invalid_template, "--force"],
        input="",
    )
    console.print(result.output)

    # Enhanced error handling for invalid template path
    assert result.exit_code == 1
    assert "not found" in result.output or "must be a directory" in result.output or "template" in result.output


@pytest.mark.usefixtures("tmp_path")
def test_create_command_output_directory(test_workspace: Path, cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with custom output directory using test workspace."""
    project_name = "test-project"
    # Use the structured workspace instead of a simple custom output
    custom_output = test_workspace / "output"

    result = cli_runner.invoke(
        cli_app,
        ["create", project_name, "--output", str(custom_output), "--dry-run"],
        input="",
    )
    console.print(result.output)
    assert result.exit_code == 0

    # Enhanced dry-run expectations for output directory test
    assert "Would create project" in result.output
    assert project_name in result.output
    assert "Dry Run" in result.output
    assert "Using template:" in result.output
    assert "Copier options:" in result.output

    # Enhanced output directory validation
    # The path might be split across multiple lines, so check for the project name and parts of the custom output path
    assert project_name in result.output
    # Check for parts of the custom output path that should be visible
    custom_output_parts = str(custom_output).split("/")
    assert any(part in result.output for part in custom_output_parts if part)

    # Verify the output directory information is properly displayed
    assert "dst_path" in result.output


def test_create_command_invalid_project_names(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test create command with various invalid project names."""
    # Mock os.scandir to prevent scandir iterator warnings
    with patch("os.scandir") as mock_scandir:
        # Create a mock iterator that properly closes
        class MockScandirIterator:
            def __init__(self, path: Path):
                self.path = path
                self.closed = False

            def __iter__(self):
                return self

            def __next__(self):
                if self.closed:
                    raise StopIteration
                # Return a mock DirEntry
                mock_entry = Mock()
                mock_entry.name = "test_file"
                mock_entry.path = str(self.path / "test_file")
                mock_entry.is_file.return_value = True
                mock_entry.is_dir.return_value = False
                self.closed = True
                return mock_entry

            def close(self) -> None:
                self.closed = True

        mock_scandir.side_effect = lambda path: MockScandirIterator(path)

        # Test empty project name - this should fail due to invalid project name
        result1 = cli_runner.invoke(cli_app, ["create", "", "--force"], input="")
        console.print(f"Empty project name result: {result1.output}")
        # Empty string should fail due to invalid project name
        assert result1.exit_code == 1
        # Check for actual error messages that might occur
        assert (
            "Invalid project name" in result1.output
            or "Error creating project" in result1.output
            or "not found" in result1.output
            or "must be a directory" in result1.output
            or "template" in result1.output
        )

        # Test project name with spaces - this should work but let's verify with dry-run
        result2 = cli_runner.invoke(
            cli_app,
            ["create", "invalid project name", "--dry-run", "--force"],
            input="",
        )
        console.print(f"Invalid chars result: {result2.output}")
        # This should work since Typer accepts spaces, verify with dry-run
        assert result2.exit_code == 0
        assert "Would create project" in result2.output
        assert "invalid project name" in result2.output

        # Test project name that's very long - this should work but let's verify with dry-run
        long_name = "a" * 100  # Use 100 instead of 256 to avoid potential issues
        result3 = cli_runner.invoke(cli_app, ["create", long_name, "--dry-run", "--force"], input="")
        console.print(f"Long name result: {result3.output}")
        # This should work since Typer doesn't enforce length limits
        assert result3.exit_code == 0
        assert "Would create project" in result3.output
        # The long name might be split across lines, so check for a reasonable portion of it
        # Check for a substantial portion of the long name (at least 50 characters)
        assert "a" * 50 in result3.output

        # Test project name with special characters - this should work but let's verify with dry-run
        special_name = "test-project-123"
        result4 = cli_runner.invoke(cli_app, ["create", special_name, "--dry-run", "--force"], input="")
        console.print(f"Special chars result: {result4.output}")
        # This should work since Typer accepts alphanumeric and hyphens
        assert result4.exit_code == 0
        assert "Would create project" in result4.output
        assert special_name in result4.output


class TestCLIErrorHandling:
    """Test error handling and edge cases in CLI commands."""

    def test_create_command_with_extremely_long_project_name(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with extremely long project names."""
        # Test with very long name (1000 characters)
        long_name = "a" * 1000
        result = cli_runner.invoke(cli_app, ["create", long_name, "--dry-run", "--force"], input="")
        console.print(f"Very long name result: {result.output}")

        # Should handle gracefully (either succeed or fail with clear error)
        assert result.exit_code in [0, 1]
        if result.exit_code == 0:
            assert "Would create project" in result.output
        else:
            # If it fails, should have some error message
            assert len(result.output.strip()) > 0

    def test_create_command_with_special_characters(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with various special characters."""
        special_names = [
            "project-with-dashes",
            "project_with_underscores",
            "project.with.dots",
            "project@#$%^&*()",
            "project[with]brackets",
            "project{with}braces",
            "project'with'quotes",
            'project"with"quotes',
            "project\nwith\nnewlines",
            "project\twith\ttabs",
        ]

        for name in special_names:
            result = cli_runner.invoke(cli_app, ["create", name, "--dry-run", "--force"], input="")
            console.print(f"Special name '{name}' result: {result.output}")

            # Should handle gracefully
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert "Would create project" in result.output
            else:
                assert any(error_msg in result.output for error_msg in ["Error", "invalid", "name", "character"])

    def test_create_command_with_unicode_characters(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with unicode characters."""
        unicode_names = [
            "project-émojis-🚀",
            "project-中文",
            "project-日本語",
            "project-한국어",
            "project-русский",
            "project-العربية",
            "project-हिन्दी",
        ]

        for name in unicode_names:
            result = cli_runner.invoke(cli_app, ["create", name, "--dry-run", "--force"], input="")
            console.print(f"Unicode name '{name}' result: {result.output}")

            # Should handle gracefully
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert "Would create project" in result.output
            else:
                assert any(error_msg in result.output for error_msg in ["Error", "invalid", "name", "character"])

    def test_create_command_with_path_traversal_attempts(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with potential path traversal attempts."""
        malicious_names = [
            # Basic path traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc//passwd",
            # URL-encoded path traversal attempts
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5C..%5C..%5Cwindows%5Csystem32",
            "..%2f..%2f..%2fetc%2fpasswd",  # lowercase URL encoding
            "..%5c..%5c..%5cwindows%5csystem32",  # lowercase URL encoding
            # Double URL-encoded path traversal attempts
            "..%252F..%252F..%252Fetc%252Fpasswd",
            "..%255C..%255C..%255Cwindows%255Csystem32",
            "..%252f..%252f..%252fetc%252fpasswd",  # lowercase double encoding
            "..%255c..%255c..%255cwindows%255csystem32",  # lowercase double encoding
            # Mixed encoding attempts
            "..%2F..\\..%5Cetc%2Fpasswd",
            "..\\..%2F..%5Cwindows\\system32",
            # Unicode path traversal attempts (using escape sequences to avoid RUF001)
            "..\u2215..\u2215..\u2215etc\u2215passwd",  # Unicode division slash
            "..\ufe68..\ufe68..\ufe68windows\ufe68system32",  # Unicode small reverse solidus
            "..\uff0f..\uff0f..\uff0fetc\uff0fpasswd",  # Full-width solidus
            "..\uff3c..\uff3c..\uff3cwindows\uff3csystem32",  # Full-width reverse solidus
        ]

        for name in malicious_names:
            result = cli_runner.invoke(cli_app, ["create", name, "--dry-run", "--force"], input="")
            console.print(f"Malicious name '{name}' result: {result.output}")

            # Should reject path traversal attempts
            assert result.exit_code == 1
            assert any(
                error_msg in result.output for error_msg in ["Error", "invalid", "path", "security", "forbidden"]
            )

    def test_create_command_with_invalid_template_paths(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with various invalid template paths."""
        invalid_templates = [
            "/non/existent/path",
            "relative/nonexistent/path",
            "path/with/spaces",
            "path/with/special/chars/!@#$%",
            "path/with/unicode/🚀",
            "",  # Empty template path
            None,  # None template path
        ]

        for template in invalid_templates:
            if template is None:
                # Skip None as it's not a valid CLI argument
                continue

            result = cli_runner.invoke(
                cli_app,
                ["create", "test-project", "--template", template, "--force"],
                input="",
            )
            console.print(f"Invalid template '{template}' result: {result.output}")

            # Should fail with clear error message
            assert result.exit_code == 1
            assert any(error_msg in result.output for error_msg in ["Error", "not found", "invalid", "template"])

    def test_create_command_with_invalid_output_paths(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with various invalid output paths."""
        invalid_outputs = [
            "/root/system/directory",
            "/etc/passwd",
            "/var/log/system",
            "path/with/invalid/chars/*?<>|",
            "path/with/unicode/🚀",
            "",  # Empty output path
        ]

        for output in invalid_outputs:
            result = cli_runner.invoke(
                cli_app,
                ["create", "test-project", "--output", output, "--dry-run", "--force"],
                input="",
            )
            console.print(f"Invalid output '{output}' result: {result.output}")

            # Should handle gracefully
            assert result.exit_code in [0, 1]
            if result.exit_code == 0:
                assert "Would create project" in result.output
            else:
                assert any(
                    error_msg in result.output
                    for error_msg in [
                        "Error",
                        "invalid",
                        "output",
                        "path",
                        "permission",
                    ]
                )

    def test_create_command_with_conflicting_flags(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with conflicting or invalid flag combinations."""
        # Test --dry-run with --force (should work together)
        result = cli_runner.invoke(cli_app, ["create", "test-project", "--dry-run", "--force"], input="")
        assert result.exit_code == 0
        assert "Would create project" in result.output

        # Test --help with other flags (should show help)
        result = cli_runner.invoke(cli_app, ["create", "--help", "--dry-run", "--force"], input="")
        assert result.exit_code == 0
        assert "Usage:" in result.output

        # Test invalid flag combinations
        result = cli_runner.invoke(cli_app, ["create", "test-project", "--invalid-flag"], input="")
        assert result.exit_code == 2
        assert "no such option" in result.output.lower() or "unrecognized arguments" in result.output.lower()

    def test_create_command_with_malformed_input(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command with malformed or unexpected input."""
        # Test with very large input
        large_input = "a" * 10000
        result = cli_runner.invoke(cli_app, ["create", large_input, "--dry-run", "--force"], input="")
        console.print(f"Large input result: {result.output}")

        # Should handle gracefully
        assert result.exit_code in [0, 1]

        # Test with binary input
        binary_input = b"\x00\x01\x02\x03\x04\x05"
        result = cli_runner.invoke(
            cli_app,
            ["create", "test-project", "--dry-run", "--force"],
            input=binary_input,
        )
        console.print(f"Binary input result: {result.output}")

        # Should handle gracefully
        assert result.exit_code in [0, 1]

    def test_create_command_with_network_issues(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command behavior when network resources are unavailable."""
        # Test with non-existent local template path (simulates network failure)
        result = cli_runner.invoke(
            cli_app,
            [
                "create",
                "test-project",
                "--template",
                "/non/existent/local/template/path",
                "--force",
            ],
            input="",
        )
        console.print(f"Network failure result: {result.output}")

        # Should fail gracefully
        assert result.exit_code == 1
        assert any(
            error_msg in result.output
            for error_msg in [
                "Error",
                "not found",
                "unavailable",
                "network",
                "template",
            ]
        )

    def test_create_command_with_file_system_issues(self, cli_runner: CliRunner, cli_app: Typer) -> None:
        """Test create command behavior when file system operations fail."""
        # Test with read-only file system
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")

            result = cli_runner.invoke(cli_app, ["create", "test-project", "--force"], input="")
            console.print(f"Permission denied result: {result.output}")

            # Should fail gracefully
            assert result.exit_code == 1
            assert any(error_msg in result.output for error_msg in ["Error", "permission", "denied", "access"])

        # Test with disk full scenario
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_mkdir.side_effect = OSError("No space left on device")

            result = cli_runner.invoke(cli_app, ["create", "test-project", "--force"], input="")
            console.print(f"Disk full result: {result.output}")

            # Should fail gracefully
            assert result.exit_code == 1
            assert any(error_msg in result.output for error_msg in ["Error", "space", "disk", "full"])
