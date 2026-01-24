"""Tests for dynamic command registration."""


def test_create_command_registered(cli_runner, cli_app) -> None:
    """Test that the 'create' command is dynamically registered and can be invoked."""
    # Test that the command exists by invoking it with --help
    # This verifies the command was registered dynamically
    result = cli_runner.invoke(cli_app, ["create", "--help"], input="")
    
    # Should succeed and show help for the create command
    assert result.exit_code == 0, "The 'create' command should be registered and accessible"
    assert "Usage:" in result.output, "Help output should be shown"
    assert "create" in result.output, "Command name should appear in help"
    assert "PROJECT_NAME" in result.output or "project_name" in result.output, "Command arguments should be shown"


def test_dynamic_command_discovery(cli_runner, cli_app) -> None:
    """Test that commands are discovered from modules in the cli directory."""
    # Test that an unknown command fails (proving command discovery is working)
    result = cli_runner.invoke(cli_app, ["nonexistent-command"], input="")
    
    # Should fail with "No such command" error
    assert result.exit_code == 2, "Unknown commands should fail"
    assert "No such command" in result.output or "no such command" in result.output.lower()
    
    # Test that the known 'create' command works
    result2 = cli_runner.invoke(cli_app, ["create", "--help"], input="")
    assert result2.exit_code == 0, "The dynamically registered 'create' command should work"
