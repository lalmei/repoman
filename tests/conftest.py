"""Test configuration and fixtures for repoman tests."""

import logging
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from repoman import cli
from repoman.utils.template_testing import cleanup_project_artifacts, instantiate_template


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables and paths."""
    # Store original environment variables
    original_env = {}
    for key in ["_REPOMAN_LOG_LEVEL", "PYTHONPATH"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # Set test-specific environment variables
    os.environ["_REPOMAN_LOG_LEVEL"] = "20"  # INFO level for tests

    # Ensure PYTHONPATH includes the src directory for proper imports
    src_path = str(Path(__file__).parent.parent / "src")
    if "PYTHONPATH" in os.environ:
        current_pythonpath = os.environ["PYTHONPATH"]
        if src_path not in current_pythonpath:
            os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"
    else:
        os.environ["PYTHONPATH"] = src_path

    yield

    # Restore original environment variables
    for key, value in original_env.items():
        os.environ[key] = value
    for key in ["_REPOMAN_LOG_LEVEL", "PYTHONPATH"]:
        if key not in original_env and key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Provide a CLI runner for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: CliRunner instance for testing CLI commands
    **Usage**: Use in CLI tests that need to invoke commands

    Example:
        def test_cli_command(cli_runner, cli_app):
            result = cli_runner.invoke(cli_app, ["command", "arg"])
            assert result.exit_code == 0
    """
    return CliRunner()


@pytest.fixture(scope="session")
def cli_app():
    """Provide the CLI application for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: Typer app instance for testing CLI commands
    **Usage**: Use in CLI tests that need to invoke commands

    Example:
        def test_cli_command(cli_runner, cli_app):
            result = cli_runner.invoke(cli_app, ["command", "arg"])
            assert result.exit_code == 0
    """
    return cli


def pytest_configure(config):
    """Configure pytest before test collection."""
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests that can run in isolation")
    config.addinivalue_line("markers", "integration: Integration tests that may have dependencies")
    config.addinivalue_line("markers", "cli: CLI command tests")
    config.addinivalue_line("markers", "utils: Utility function tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "isolated: Tests that must run in isolation")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add default markers based on test location."""
    for item in items:
        # Add default markers based on test file/class names and locations
        if "test_utils" in item.nodeid:
            item.add_marker(pytest.mark.utils)
            item.add_marker(pytest.mark.unit)
        elif "test_cli" in item.nodeid:
            item.add_marker(pytest.mark.cli)
            item.add_marker(pytest.mark.integration)
        else:
            # Default to unit tests for other test files
            item.add_marker(pytest.mark.unit)

        # Mark tests that use file system operations as isolated
        if any(keyword in item.nodeid.lower() for keyword in ["file", "path", "directory", "log"]):
            item.add_marker(pytest.mark.isolated)


def pytest_unconfigure(config):
    """Clean up after all tests are complete."""
    # Clean up any global resources here
    pass


@pytest.fixture(scope="session")
def sample_project_names():
    """Provide sample project names for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: List of valid project names for testing
    **Usage**: Use in tests that need sample project names

    Example:
        def test_project_creation(sample_project_names):
            for name in sample_project_names:
                # Test logic here
                pass
    """
    return [
        "test-project",
        "my-awesome-project",
        "project_with_underscores",
        "ProjectWithCaps",
        "123-numeric-project",
        "very-long-project-name-that-might-cause-issues",
    ]


@pytest.fixture(scope="session")
def sample_templates():
    """Provide sample template paths for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: List of template paths for testing
    **Usage**: Use in tests that need template paths

    Example:
        def test_template_handling(sample_templates):
            for template in sample_templates:
                # Test logic here
                pass
    """
    return [
        "default-template",
        "custom-template",
        "template-with-spaces",
        "template/with/subdirectories",
    ]


@pytest.fixture(scope="session")
def sample_project_data():
    """Provide comprehensive sample project data for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: Dictionary with various types of test data
    **Usage**: Use in tests that need different types of test data

    Example:
        def test_various_scenarios(sample_project_data):
            for name in sample_project_data["valid_names"]:
                # Test valid names
                pass
            for name in sample_project_data["invalid_names"]:
                # Test invalid names
                pass
    """
    return {
        "valid_names": [
            "test-project",
            "my_app",
            "api_service",
            "data_processor",
            "web_framework",
        ],
        "invalid_names": [
            "",  # Empty string
            "a" * 1000,  # Very long name
            "project@#$%",  # Special characters
            "project with spaces",  # Spaces
            "project\nwith\nnewlines",  # Newlines
        ],
        "template_paths": [
            "/templates/basic",
            "/templates/advanced",
            "relative/template",
            "https://github.com/user/template",
        ],
        "output_paths": [
            "/tmp/test_output",
            "./output",
            "relative/output/path",
        ],
    }


@pytest.fixture
def mock_project_structure(tmp_path):
    """Create a mock project structure for testing."""
    project_dir = tmp_path / "mock-project"
    project_dir.mkdir()

    # Create some mock files and directories
    (project_dir / "README.md").write_text("# Mock Project\n\nThis is a test project.")
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").write_text("# Mock package")
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "test_mock.py").write_text("def test_mock(): pass")

    return project_dir


@pytest.fixture
def mock_template_structure(tmp_path):
    """Create a mock template structure for testing."""
    template_dir = tmp_path / "mock-template"
    template_dir.mkdir()

    # Create mock template files
    (template_dir / "copier.yml").write_text("project_name: '{{ project_name }}'")
    (template_dir / "README.md.jinja").write_text("# {{ project_name }}\n\nGenerated project.")
    (template_dir / "src").mkdir()
    (template_dir / "src" / "main.py.jinja").write_text("print('Hello {{ project_name }}')")

    return template_dir


@pytest.fixture
def test_workspace(tmp_path):
    """Provide a clean workspace for each test with proper isolation."""
    # Create a unique workspace directory for this test
    workspace = tmp_path / f"test_workspace_{os.getpid()}_{id(tmp_path)}"
    workspace.mkdir()

    # Create common subdirectories
    (workspace / "projects").mkdir()
    (workspace / "templates").mkdir()
    (workspace / "output").mkdir()

    yield workspace

    # Cleanup is handled by pytest's tmp_path fixture


@pytest.fixture
def isolated_test_dir(tmp_path):
    """Provide an isolated test directory that's automatically cleaned up."""
    test_dir = tmp_path / f"isolated_test_{os.getpid()}_{id(tmp_path)}"
    test_dir.mkdir()

    # Store original working directory
    original_cwd = os.getcwd()

    # Change to test directory for isolation
    os.chdir(test_dir)

    yield test_dir

    # Change back to original directory
    os.chdir(original_cwd)

    # Cleanup is handled by pytest's tmp_path fixture


@pytest.fixture
def mock_copier_available(monkeypatch):
    """Mock copier availability for testing."""

    # Mock the copier import to always be available
    def mock_import_copier():
        class MockCopier:
            def run_copy(self, *args, **kwargs):
                return True

        return MockCopier()

    monkeypatch.setattr("repoman.cli.copier.copier", mock_import_copier())


@pytest.fixture
def mock_file_system(monkeypatch, tmp_path):
    """Mock file system operations for testing."""
    # Create a mock file system in tmp_path
    mock_fs = tmp_path / "mock_fs"
    mock_fs.mkdir()

    def mock_makedirs(path, exist_ok=False):
        Path(path).mkdir(parents=True, exist_ok=exist_ok)

    def mock_path_exists(path):
        return Path(path).exists()

    monkeypatch.setattr("os.makedirs", mock_makedirs)
    monkeypatch.setattr("pathlib.Path.exists", mock_path_exists)

    return mock_fs


@pytest.fixture
def mock_rich_console(monkeypatch):
    """Mock rich console for testing to avoid actual console output."""

    class MockConsole:
        def print(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    monkeypatch.setattr("rich.console.Console", MockConsole)


@pytest.fixture(autouse=True)
def isolate_test_environment():
    """Ensure each test runs in an isolated environment."""
    # Store original working directory
    original_cwd = os.getcwd()

    yield

    # Restore working directory
    os.chdir(original_cwd)


@pytest.fixture(autouse=True)
def cleanup_loggers():
    """Clean up logger state between tests to prevent interference."""
    # Store original root logger state
    original_root_level = logging.root.level
    original_root_handlers = logging.root.handlers.copy()

    # Store state of known loggers that might be used in tests
    known_loggers = ["repoman", "repoman.utils", "repoman.cli"]
    original_loggers = {}

    for name in known_loggers:
        logger = logging.getLogger(name)
        original_loggers[name] = {
            "level": logger.level,
            "handlers": logger.handlers.copy(),
            "propagate": logger.propagate,
        }

    yield

    # Restore known logger state
    for name, state in original_loggers.items():
        logger = logging.getLogger(name)
        logger.level = state["level"]
        logger.handlers.clear()
        for handler in state["handlers"]:
            logger.addHandler(handler)
        logger.propagate = state["propagate"]

    # Restore root logger state
    logging.root.level = original_root_level
    logging.root.handlers.clear()
    for handler in original_root_handlers:
        logging.root.addHandler(handler)


@pytest.fixture
def instantiated_template(tmp_path):
    """Instantiate the main template in a temporary directory.

    This fixture creates a fresh template instantiation for each test.
    All artifacts are cleaned up after the test completes, even if it fails.

    **Scope**: function - each test gets a fresh template
    **Returns**: Path to the instantiated project directory
    **Usage**: Use in tests that need an instantiated template

    Example:
        def test_something(instantiated_template):
            # instantiated_template is a Path to the project directory
            assert (instantiated_template / "pyproject.toml").exists()
    """
    project_dir = tmp_path / "test-project"
    instantiated_path = None

    try:
        # Instantiate template
        instantiated_path = instantiate_template(
            output_dir=tmp_path,
            project_name="test-project",
            force=True,
        )

        yield instantiated_path

    finally:
        # Explicit cleanup of artifacts (only if instantiation succeeded)
        if instantiated_path is not None:
            cleanup_project_artifacts(instantiated_path)
        # tmp_path fixture handles directory removal


@pytest.fixture(scope="module")
def setup_template(tmp_path_factory):
    """Setup fixture that runs make setup once for all CI tests in a module.

    This fixture uses module scope to run setup once and share it across
    all tests in the test module. This is more efficient than running setup
    for each test.

    **Scope**: module - shared across all tests in the module
    **Returns**: Path to the instantiated and set up project directory
    **Usage**: Use in CI tests that need a set up template

    Example:
        def test_ci_command(setup_template):
            # setup_template has already run 'make setup'
            # Now run other CI commands
            pass
    """
    from repoman.utils.ci_runner import run_make_command

    # Create a module-scoped temporary directory
    tmp_path = tmp_path_factory.mktemp("template-ci-module")
    project_dir = tmp_path / "test-project"
    instantiated_path = None

    try:
        # Instantiate template
        instantiated_path = instantiate_template(
            output_dir=tmp_path,
            project_name="test-project",
            force=True,
        )

        # Run make setup
        result = run_make_command(instantiated_path, "setup")
        if result.returncode != 0:
            pytest.fail(f"Setup failed:\nCommand: {result.command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")

        yield instantiated_path

    finally:
        # Explicit cleanup of artifacts (only if instantiation succeeded)
        if instantiated_path is not None:
            cleanup_project_artifacts(instantiated_path)
        # tmp_path_factory handles directory removal
