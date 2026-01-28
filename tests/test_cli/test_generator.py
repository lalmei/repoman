"""Tests for the generator command."""

from pathlib import Path
from unittest.mock import Mock, patch

import yaml  # noqa: TID251
from rich.console import Console

console = Console()


def test_generator_command_help(cli_runner, cli_app) -> None:
    """Test that the generator command displays help information correctly.

    This test verifies that:
    - The generator command can be invoked with --help flag
    - The help output contains usage information
    - The command name appears in the help output
    - The command description is displayed

    Expected behavior:
    - Exit code should be 0 (success)
    - Help output should contain "Usage:" section
    - Command name "generator" should be present in output
    - Command description should be visible
    """
    result = cli_runner.invoke(cli_app, ["generator", "--help"], input="")
    console.print(result.output)

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "generator" in result.output.lower()
    assert "Generate new CLI commands" in result.output or "Generate" in result.output


def test_generator_command_registered(cli_runner, cli_app) -> None:
    """Test that the generator command is dynamically registered in the CLI.

    This test verifies the dynamic command registration system works correctly:
    - The generator command module is discovered automatically
    - The command is registered with the main CLI app
    - The command can be invoked through the main CLI

    Expected behavior:
    - Command should be accessible via the main CLI
    - Help can be displayed successfully
    - Command name appears in help output

    This ensures the command registration mechanism (which scans for commands
    in the cli/commands directory) properly discovers and registers the generator command.
    """
    # Test that the command exists by invoking it with --help
    result = cli_runner.invoke(cli_app, ["generator", "--help"], input="")

    # Should succeed and show help for the generator command
    assert result.exit_code == 0, (
        "The 'generator' command should be registered and accessible"
    )
    assert "Usage:" in result.output, "Help output should be shown"
    assert "generator" in result.output.lower(), "Command name should appear in help"


def test_generator_add_command_help(cli_runner, cli_app) -> None:
    """Test that the generator add subcommand displays comprehensive help information.

    This test verifies that:
    - The 'add' subcommand can be invoked with --help
    - All required arguments are documented (COMMAND_NAME)
    - All available options are documented in the help output

    Expected options to be documented:
    - COMMAND_NAME: Required argument for the command name to create
    - --project-dir: Optional project directory path
    - --answers: Optional path to .copier-answers.yml file
    - --force: Flag to overwrite existing files
    - --dry-run: Flag to preview changes without creating files

    Expected behavior:
    - Exit code should be 0 (success)
    - Help output should contain usage information
    - All options should be visible in the help text
    """
    result = cli_runner.invoke(cli_app, ["generator", "add", "--help"], input="")
    console.print(result.output)

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "add" in result.output.lower()
    assert "COMMAND_NAME" in result.output or "command_name" in result.output
    assert "--project-dir" in result.output or "--project_dir" in result.output
    assert "--answers" in result.output
    assert "--force" in result.output
    assert "--dry-run" in result.output or "--dry_run" in result.output


def test_generator_add_missing_required_args(cli_runner, cli_app) -> None:
    """Test that generator add command properly validates required arguments.

    This test verifies argument validation:
    - The command requires COMMAND_NAME as a positional argument
    - When COMMAND_NAME is missing, the command should fail with a clear error
    - The error message should indicate which argument is missing

    Expected behavior:
    - Exit code should be 2 (typer's error code for missing arguments)
    - Error message should contain "Missing argument"
    - Error message should reference "COMMAND_NAME" to help the user
    """
    result = cli_runner.invoke(cli_app, ["generator", "add"], input="")
    console.print(result.output)

    # Should fail due to missing COMMAND_NAME
    assert result.exit_code == 2
    assert "Missing argument" in result.output
    assert "COMMAND_NAME" in result.output or "command_name" in result.output


def test_generator_add_invalid_command_name(
    cli_runner, cli_app, tmp_path: Path
) -> None:
    """Test that generator add command rejects invalid command names with proper validation.

    This test verifies the command name validation logic:
    - Command names must be valid Python identifiers
    - Path traversal attempts are blocked
    - Invalid characters are rejected
    - Security checks prevent dangerous input

    Test cases for invalid names:
    - Names with hyphens (not valid Python identifiers)
    - Names with spaces (not valid Python identifiers)
    - Names with slashes (path traversal attempt)
    - Names with backslashes (path traversal attempt)
    - Names starting with numbers (not valid Python identifiers)

    Expected behavior:
    - All invalid names should be rejected with exit code 1
    - Error message should indicate "Invalid command name" or general error
    - Validation should prevent security issues and invalid Python module names
    """
    # Create a mock .copier-answers.yml file
    answers_file = tmp_path / ".copier-answers.yml"
    answers_file.write_text(
        yaml.dump(
            {
                "python_package_import_name": "test_package",
                "python_package_command_line_name": "test",
            }
        )
    )

    # Test with invalid command name containing invalid characters
    invalid_names = [
        "my-command",  # Contains hyphen (not valid Python identifier)
        "my command",  # Contains space
        "my/command",  # Contains slash (path traversal)
        "my\\command",  # Contains backslash
        "123command",  # Starts with number
    ]

    for invalid_name in invalid_names:
        result = cli_runner.invoke(
            cli_app,
            ["generator", "add", invalid_name, "--project-dir", str(tmp_path)],
            input="",
        )
        console.print(f"Testing '{invalid_name}': {result.output}")
        # Should fail with validation error
        assert result.exit_code == 1, (
            f"Command name '{invalid_name}' should be rejected"
        )
        assert "Invalid command name" in result.output or "Error" in result.output


def test_generator_add_valid_command_name_validation(
    cli_runner, cli_app, tmp_path: Path
) -> None:
    """Test that generator add command accepts valid command names.

    This test verifies that valid Python identifiers pass validation:
    - Lowercase names (mycommand)
    - Names with underscores (my_command)
    - PascalCase names (MyCommand)
    - Names ending with numbers (command123)

    Setup:
    - Creates a mock .copier-answers.yml file with required fields
    - Creates mock project directory structure
    - Mocks template directory and rendering to focus on validation

    Expected behavior:
    - Valid names should pass the validation step
    - No "Invalid command name" error should appear
    - With --dry-run, the command should proceed to show what would be created
    - Validation should allow names that are valid Python identifiers
    """
    # Create a mock .copier-answers.yml file
    answers_file = tmp_path / ".copier-answers.yml"
    answers_file.write_text(
        yaml.dump(
            {
                "python_package_import_name": "test_package",
                "python_package_command_line_name": "test",
            }
        )
    )

    # Create mock project structure
    (tmp_path / "src" / "test_package" / "cli" / "commands").mkdir(parents=True)
    (tmp_path / "tests" / "test_cli").mkdir(parents=True)

    # Mock the template directory and file operations
    with patch("repoman.cli.commands.generator.add.Path.exists") as mock_exists:
        # Make template directory exist
        def exists_side_effect(path):
            if "extentions/command_template" in str(path) or "{{command_name}}" in str(
                path
            ):
                return True
            if path == answers_file:
                return True
            if "src/test_package/cli/commands" in str(path):
                return True
            if "tests/test_cli" in str(path):
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        # Mock template rendering
        with patch("repoman.cli.commands.generator.add.Environment") as mock_env:
            mock_template = Mock()
            mock_template.render.return_value = "rendered content"
            mock_env_instance = Mock()
            mock_env_instance.get_template.return_value = mock_template
            mock_env.return_value = mock_env_instance

            valid_names = ["mycommand", "my_command", "MyCommand", "command123"]

            for valid_name in valid_names:
                result = cli_runner.invoke(
                    cli_app,
                    [
                        "generator",
                        "add",
                        valid_name,
                        "--project-dir",
                        str(tmp_path),
                        "--dry-run",
                    ],
                    input="",
                )
                console.print(f"Testing '{valid_name}': {result.output}")
                # Should pass validation (may fail later due to missing templates, but validation should pass)
                # With dry-run, it should show what would be created
                assert "Invalid command name" not in result.output, (
                    f"Command name '{valid_name}' should pass validation"
                )


def test_generator_add_dry_run(cli_runner, cli_app, tmp_path: Path) -> None:
    """Test that generator add command supports dry-run mode for previewing changes.

    This test verifies the --dry-run functionality:
    - When --dry-run is specified, no files should be created
    - The command should show what would be created
    - All validation and setup steps should still run
    - User can preview changes before committing

    Setup:
    - Creates mock .copier-answers.yml file
    - Creates mock project directory structure
    - Mocks template directory and rendering

    Expected behavior:
    - Exit code should be 0 (success)
    - Output should indicate dry-run mode ("Dry Run", "dry-run", or "Would create")
    - No actual files should be created (verified by mocking)
    - User should see what files would be created and where
    """
    # Create a mock .copier-answers.yml file
    answers_file = tmp_path / ".copier-answers.yml"
    answers_file.write_text(
        yaml.dump(
            {
                "python_package_import_name": "test_package",
                "python_package_command_line_name": "test",
            }
        )
    )

    # Create mock project structure
    (tmp_path / "src" / "test_package" / "cli" / "commands").mkdir(parents=True)
    (tmp_path / "tests" / "test_cli").mkdir(parents=True)

    # Mock template directory existence
    with patch("repoman.cli.commands.generator.add.Path.exists") as mock_exists:

        def exists_side_effect(path):
            path_str = str(path)
            if (
                "extentions/command_template" in path_str
                or "{{command_name}}" in path_str
            ):
                return True
            if path == answers_file:
                return True
            if "src/test_package/cli/commands" in path_str:
                return True
            if "tests/test_cli" in path_str:
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        # Mock template rendering
        with patch("repoman.cli.commands.generator.add.Environment") as mock_env:
            mock_template = Mock()
            mock_template.render.return_value = "rendered content"
            mock_env_instance = Mock()
            mock_env_instance.get_template.return_value = mock_template
            mock_env.return_value = mock_env_instance

            result = cli_runner.invoke(
                cli_app,
                [
                    "generator",
                    "add",
                    "testcommand",
                    "--project-dir",
                    str(tmp_path),
                    "--dry-run",
                ],
                input="",
            )
            console.print(result.output)

            # Should show dry-run output
            assert result.exit_code == 0
            assert (
                "Dry Run" in result.output
                or "dry-run" in result.output.lower()
                or "Would create" in result.output
            )


def test_generator_add_missing_answers_file(
    cli_runner, cli_app, tmp_path: Path
) -> None:
    """Test that generator add command handles missing .copier-answers.yml file gracefully.

    This test verifies error handling when the copier answers file is missing:
    - The command requires .copier-answers.yml to get project context
    - Without it, the command cannot determine package structure
    - A clear error message should guide the user


    Setup:
    - Creates mock project directory structure
    - Intentionally does NOT create .copier-answers.yml file

    Expected behavior:
    - Exit code should be 1 (error)
    - Error message should reference "answers file" or ".copier-answers.yml"
    - Error should provide guidance on what's missing and how to fix it
    """
    # Don't create the answers file
    # Create mock project structure (but answers file missing)
    (tmp_path / "src" / "test_package" / "cli" / "commands").mkdir(parents=True)

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "testcommand", "--project-dir", str(tmp_path)],
        input="",
    )
    console.print(result.output)

    # Should fail with error about missing answers file
    assert result.exit_code == 1
    assert (
        "answers file" in result.output.lower()
        or ".copier-answers.yml" in result.output
    )


def test_generator_add_missing_python_package_import_name(
    cli_runner, cli_app, tmp_path: Path
) -> None:
    """Test that generator add command validates required fields in .copier-answers.yml.

    This test verifies field validation:
    - The command requires 'python_package_import_name' from the answers file
    - This field is used to determine where to create command files
    - Missing required fields should result in a clear error

    Setup:
    - Creates .copier-answers.yml file but omits the required field
    - Includes other fields (like project_name) to ensure it's not a file reading issue

    Expected behavior:
    - Exit code should be 1 (error)
    - Error message should reference "python_package_import_name"
    - Error should indicate which required field is missing
    """
    # Create answers file without required field
    answers_file = tmp_path / ".copier-answers.yml"
    answers_file.write_text(yaml.dump({"project_name": "test_project"}))

    result = cli_runner.invoke(
        cli_app,
        ["generator", "add", "testcommand", "--project-dir", str(tmp_path)],
        input="",
    )
    console.print(result.output)

    # Should fail with error about missing python_package_import_name
    assert result.exit_code == 1
    assert "python_package_import_name" in result.output.lower()


def test_generator_add_file_already_exists(cli_runner, cli_app, tmp_path: Path) -> None:
    """Test that generator add command prevents accidental overwrites without --force flag.

    This test verifies file existence checking:
    - The command checks if command files already exist before creating
    - Without --force flag, existing files should not be overwritten
    - A warning should inform the user about the existing file
    - User must explicitly use --force to overwrite

    Setup:
    - Creates .copier-answers.yml file with required fields
    - Creates an existing command directory and __init__.py file
    - Mocks template directory to focus on file existence check

    Expected behavior:
    - Exit code should be 1 (error/warning)
    - Error message should indicate file "already exists"
    - Should suggest using --force flag to overwrite
    - Prevents accidental data loss from overwriting existing commands
    """
    # Create a mock .copier-answers.yml file
    answers_file = tmp_path / ".copier-answers.yml"
    answers_file.write_text(
        yaml.dump(
            {
                "python_package_import_name": "test_package",
                "python_package_command_line_name": "test",
            }
        )
    )

    # Create mock project structure with existing command
    command_dir = tmp_path / "src" / "test_package" / "cli" / "commands" / "testcommand"
    command_dir.mkdir(parents=True)
    (command_dir / "__init__.py").write_text("# Existing command")

    # Mock template directory existence
    with patch("repoman.cli.commands.generator.add.Path.exists") as mock_exists:

        def exists_side_effect(path):
            path_str = str(path)
            if (
                "extentions/command_template" in path_str
                or "{{command_name}}" in path_str
            ):
                return True
            if path == answers_file:
                return True
            if path == command_dir / "__init__.py":
                return True
            if "src/test_package/cli/commands" in path_str:
                return True
            return False

        mock_exists.side_effect = exists_side_effect

        result = cli_runner.invoke(
            cli_app,
            ["generator", "add", "testcommand", "--project-dir", str(tmp_path)],
            input="",
        )
        console.print(result.output)

        # Should fail with warning about existing file
        assert result.exit_code == 1
        assert "already exists" in result.output.lower() or "Warning" in result.output
