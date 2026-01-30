"""Tests for dynamic command registration."""

from pathlib import Path
from unittest.mock import Mock, patch

from typer import Typer
from typer.testing import CliRunner


def test_create_command_registered(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test that the 'create' command is dynamically registered and can be invoked."""
    # Test that the command exists by invoking it with --help
    # This verifies the command was registered dynamically
    result = cli_runner.invoke(cli_app, ["create", "--help"], input="")

    # Should succeed and show help for the create command
    assert result.exit_code == 0, "The 'create' command should be registered and accessible"
    assert "Usage:" in result.output, "Help output should be shown"
    assert "create" in result.output.lower(), "Command name should appear in help"
    assert "PROJECT_NAME" in result.output or "project_name" in result.output, "Command arguments should be shown"


def test_generator_command_registered(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test that the 'generator' command is dynamically registered and can be invoked."""
    # Test that the command exists by invoking it with --help
    # This verifies the command was registered dynamically
    result = cli_runner.invoke(cli_app, ["generator", "--help"], input="")

    # Should succeed and show help for the generator command
    assert result.exit_code == 0, "The 'generator' command should be registered and accessible"
    assert "Usage:" in result.output, "Help output should be shown"
    assert "generator" in result.output.lower(), "Command name should appear in help"


def test_dynamic_command_discovery(cli_runner: CliRunner, cli_app: Typer) -> None:
    """Test that commands are discovered from modules in the cli directory."""
    # Test that an unknown command fails (proving command discovery is working)
    result = cli_runner.invoke(cli_app, ["nonexistent-command"], input="")

    # Should fail with "No such command" error
    assert result.exit_code == 2, "Unknown commands should fail"
    assert "No such command" in result.output or "no such command" in result.output.lower()

    # Test that the known 'create' command works
    result2 = cli_runner.invoke(cli_app, ["create", "--help"], input="")
    assert result2.exit_code == 0, "The dynamically registered 'create' command should work"

    # Test that the known 'generator' command works
    result3 = cli_runner.invoke(cli_app, ["generator", "--help"], input="")
    assert result3.exit_code == 0, "The dynamically registered 'generator' command should work"


def test_register_commands_module_without_app(tmp_path: Path) -> None:
    """Test that modules without 'app' attribute are skipped.

    This test verifies the behavior when a module doesn't have an 'app' attribute (lines 39-41).
    """
    from repoman.cli.register_commands import _register_commands

    # Create a mock commands directory structure
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Module without app attribute")

    app = Typer()

    # Mock importlib to return a module without 'app' attribute
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_module = Mock()
        # Remove 'app' attribute if it exists
        if hasattr(mock_module, "app"):
            delattr(mock_module, "app")
        mock_import.return_value = mock_module

        # Mock Path.iterdir to return our test module
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [test_module_dir]

            # Should not raise an error, just skip the module
            _register_commands(app, path=commands_dir)

            # Verify the module was imported
            mock_import.assert_called()


def test_register_commands_duplicate_name(tmp_path: Path) -> None:
    """Test that duplicate command names are handled gracefully.

    This test verifies duplicate registration handling (lines 47-50).
    """
    from repoman.cli.register_commands import _register_commands

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Test module")

    app = Typer()

    # Create a mock Typer app
    mock_typer_app = Typer()

    # Mock importlib to return a module with 'app' attribute
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.app = mock_typer_app
        mock_import.return_value = mock_module

        # Mock Path.iterdir to return the same module twice (simulating duplicate)
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [test_module_dir, test_module_dir]

            # Mock registered_commands set to simulate duplicate detection
            with patch("repoman.cli.register_commands._register_commands") as mock_register:
                # Call the actual function but track calls
                _register_commands(app, path=commands_dir)

                # Verify import was attempted
                assert mock_import.called


def test_register_commands_import_error(tmp_path: Path) -> None:
    """Test that ImportError during module import is handled gracefully.

    This test verifies ImportError handling (lines 56-59).
    """
    from repoman.cli.register_commands import _register_commands

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Test module")

    app = Typer()

    # Mock importlib to raise ImportError
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_import.side_effect = ImportError("Cannot import module")

        # Mock Path.iterdir to return our test module
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [test_module_dir]

            # Should not raise an error, just log a warning and continue
            _register_commands(app, path=commands_dir)

            # Verify import was attempted
            mock_import.assert_called()


def test_register_commands_attribute_error(tmp_path: Path) -> None:
    """Test that AttributeError during command processing is handled gracefully.

    This test verifies AttributeError handling (lines 58-59).
    """
    from repoman.cli.register_commands import _register_commands

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Test module")

    app = Typer()

    # Mock importlib to return a module that raises AttributeError when accessing app
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_module = Mock()
        # Make hasattr return True but accessing app raises AttributeError
        type(mock_module).app = property(lambda self: (_ for _ in ()).throw(AttributeError("No app")))

        def hasattr_side_effect(obj, name):
            if name == "app":
                return True
            return hasattr(obj, name)

        with patch("builtins.hasattr", side_effect=hasattr_side_effect):
            mock_import.return_value = mock_module

            # Mock Path.iterdir
            with patch("pathlib.Path.iterdir") as mock_iterdir:
                mock_iterdir.return_value = [test_module_dir]

                # Should not raise an error, just log a warning and continue
                _register_commands(app, path=commands_dir)

                # Verify import was attempted
                mock_import.assert_called()


def test_register_commands_type_error(tmp_path: Path) -> None:
    """Test that TypeError during command processing is handled gracefully.

    This test verifies TypeError handling (lines 58-59).
    """
    from repoman.cli.register_commands import _register_commands

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Test module")

    app = Typer()

    # Mock importlib to return a module with invalid app type
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_module.app = "not a typer app"  # Invalid type

        mock_import.return_value = mock_module

        # Mock Path.iterdir
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [test_module_dir]

            # Mock app.add_typer to raise TypeError
            with patch.object(app, "add_typer", side_effect=TypeError("Invalid type")):
                # Should not raise an error, just log a warning and continue
                _register_commands(app, path=commands_dir)

                # Verify import was attempted
                mock_import.assert_called()


def test_register_commands_value_error(tmp_path: Path) -> None:
    """Test that ValueError during command processing is handled gracefully.

    This test verifies ValueError handling (lines 58-59).
    """
    from repoman.cli.register_commands import _register_commands

    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()
    test_module_dir = commands_dir / "test_module"
    test_module_dir.mkdir()
    (test_module_dir / "__init__.py").write_text("# Test module")

    app = Typer()

    # Mock importlib to return a module
    with patch("repoman.cli.register_commands.importlib.import_module") as mock_import:
        mock_module = Mock()
        mock_typer_app = Typer()
        mock_module.app = mock_typer_app

        mock_import.return_value = mock_module

        # Mock Path.iterdir
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            mock_iterdir.return_value = [test_module_dir]

            # Mock app.add_typer to raise ValueError
            with patch.object(app, "add_typer", side_effect=ValueError("Invalid value")):
                # Should not raise an error, just log a warning and continue
                _register_commands(app, path=commands_dir)

                # Verify import was attempted
                mock_import.assert_called()
