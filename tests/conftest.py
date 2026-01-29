"""Test configuration and fixtures for repoman tests."""

import logging
import os
import re
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from repoman import cli
from tests.template_testing import cleanup_project_artifacts, instantiate_template


def strip_ansi_codes(text: str) -> str:
    """Strip ANSI escape codes from text for easier pattern matching in tests.

    Args:
        text: Text that may contain ANSI escape codes

    Returns:
        Plain text without ANSI codes
    """
    # Remove ANSI escape sequences (including Rich's hyperlinks)
    ansi_escape = re.compile(
        r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|]8;[^;]*;[^\\]*\\|]8;;)"
    )
    return ansi_escape.sub("", text)


@pytest.fixture(autouse=True)
def setup_test_environment() -> None:
    """Set up test environment variables, paths, and working directory isolation."""
    # Store original environment variables
    original_env = {}
    for key in ["_REPOMAN_LOG_LEVEL", "PYTHONPATH", "NO_ALBUMENTATIONS_UPDATE"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    # Store original working directory
    original_cwd = os.getcwd()

    # Set test-specific environment variables
    os.environ["_REPOMAN_LOG_LEVEL"] = "20"  # INFO level for tests
    os.environ["NO_ALBUMENTATIONS_UPDATE"] = "1"

    # Ensure PYTHONPATH includes the src directory for proper imports
    src_path = str(Path(__file__).parent.parent / "src")
    if "PYTHONPATH" in os.environ:
        current_pythonpath = os.environ["PYTHONPATH"]
        if src_path not in current_pythonpath:
            os.environ["PYTHONPATH"] = f"{src_path}:{current_pythonpath}"
    else:
        os.environ["PYTHONPATH"] = src_path

    yield

    # Restore working directory
    os.chdir(original_cwd)

    # Restore original environment variables
    for key, value in original_env.items():
        os.environ[key] = value
    for key in ["_REPOMAN_LOG_LEVEL", "PYTHONPATH", "NO_ALBUMENTATIONS_UPDATE"]:
        if key not in original_env and key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="session")
def cli_runner() -> CliRunner:
    """Provide a CLI runner for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: CliRunner instance for testing CLI commands
    **Usage**: Use in CLI tests that need to invoke commands

    Example:
        def test_cli_command(cli_runner: CliRunner, cli_app: Typer) -> None:
            result = cli_runner.invoke(cli_app, ["command", "arg"])
            assert result.exit_code == 0
    """
    return CliRunner()


@pytest.fixture(scope="session")
def cli_app() -> Any:
    """Provide the CLI application for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: Typer app instance for testing CLI commands
    **Usage**: Use in CLI tests that need to invoke commands

    Example:
        def test_cli_command(cli_runner: CliRunner, cli_app: Typer) -> None:
            result = cli_runner.invoke(cli_app, ["command", "arg"])
            assert result.exit_code == 0
    """
    return cli


@pytest.fixture(scope="session")
def sample_project_names() -> Any:
    """Provide sample project names for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: List of valid project names for testing
    **Usage**: Use in tests that need sample project names

    Example:
        def test_project_creation(sample_project_names: Any) -> None:
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
def sample_templates() -> Any:
    """Provide sample template paths for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: List of template paths for testing
    **Usage**: Use in tests that need template paths

    Example:
        def test_template_handling(sample_templates: Any) -> None:
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
def sample_project_data() -> Any:
    """Provide comprehensive sample project data for testing.

    **Scope**: session - shared across all tests for maximum performance
    **Returns**: Dictionary with various types of test data
    **Usage**: Use in tests that need different types of test data

    Example:
        def test_various_scenarios(sample_project_data: Any) -> None:
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
            "/tmp/test_output",  # noqa: S108 - Test fixture: safe temp path for testing
            "./output",
            "relative/output/path",
        ],
    }


@pytest.fixture
def mock_project_structure(tmp_path: Path) -> Any:
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
def mock_template_structure(tmp_path: Path) -> Any:
    """Create a mock template structure for testing."""
    template_dir = tmp_path / "mock-template"
    template_dir.mkdir()

    # Create mock template files
    (template_dir / "copier.yml").write_text("project_name: '{{ project_name }}'")
    (template_dir / "README.md.jinja").write_text(
        "# {{ project_name }}\n\nGenerated project."
    )
    (template_dir / "src").mkdir()
    (template_dir / "src" / "main.py.jinja").write_text(
        "print('Hello {{ project_name }}')"
    )

    return template_dir


@pytest.fixture
def test_workspace(tmp_path: Path) -> None:
    """Provide a clean workspace for each test with proper isolation."""
    # Create a unique workspace directory for this test
    workspace = tmp_path / f"test_workspace_{os.getpid()}_{id(tmp_path)}"
    workspace.mkdir()

    # Create common subdirectories
    (workspace / "projects").mkdir()
    (workspace / "templates").mkdir()
    (workspace / "output").mkdir()

    return workspace

    # Cleanup is handled by pytest's tmp_path fixture


@pytest.fixture
def mock_copier_available(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Mock copier library availability for testing."""

    # Mock the copier import to always be available
    def mock_import_copier() -> Any:
        class MockCopier:
            def run_copy(self, *_args: Any, **_kwargs: Any) -> bool:
                return True

        return MockCopier()

    # Mock the copier library itself, not the command module
    monkeypatch.setattr("copier.copier", mock_import_copier())


@pytest.fixture
def mock_file_system(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """Mock file system operations for testing."""
    # Create a mock file system in tmp_path
    mock_fs = tmp_path / "mock_fs"
    mock_fs.mkdir()

    def mock_makedirs(path: Path, *, exist_ok: bool = False) -> Any:
        Path(path).mkdir(parents=True, exist_ok=exist_ok)

    def mock_path_exists(path: Path) -> Path:
        return Path(path).exists()

    monkeypatch.setattr("os.makedirs", mock_makedirs)
    monkeypatch.setattr("pathlib.Path.exists", mock_path_exists)

    return mock_fs


@pytest.fixture
def mock_rich_console(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock rich console for testing to avoid actual console output."""

    class MockConsole:
        def print(self, *args: Any, **kwargs: Any) -> Path:
            pass

        def __getattr__(self, name: str):
            return lambda *args, **kwargs: None

    monkeypatch.setattr("rich.console.Console", MockConsole)


@pytest.fixture(autouse=True)
def cleanup_loggers() -> None:
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


def _get_default_answers_file() -> Path | None:
    """Get the default answers file path if it exists.

    Returns:
        Path to default answers file, or None if it doesn't exist
    """
    current_file = Path(__file__)
    default_answers = current_file.parent / "fixtures" / "default_copier_answers.yml"
    if default_answers.exists():
        return default_answers
    return None


def _create_template_instance(
    tmp_path_base: Path, project_name: str, *, run_setup: bool = False
) -> Path:
    """Helper to create template instance with optional setup.

    Args:
        tmp_path_base: Base temporary directory path (from tmp_path or tmp_path_factory)
        project_name: Name of the project to create
        run_setup: If True, run 'make setup' after instantiation

    Returns:
        Path to the instantiated project directory

    Raises:
        pytest.fail: If setup fails when run_setup=True
    """
    instantiated_path = None
    try:
        # Get default answers file if available
        default_answers = _get_default_answers_file()

        # Instantiate template
        instantiated_path = instantiate_template(
            output_dir=tmp_path_base,
            project_name=project_name,
            answers_file=default_answers,
            force=True,
        )

        # Optionally run make setup
        if run_setup:
            from tests.ci_runner import (  # noqa: PLC0415 - Conditional import to avoid circular dependency
                run_make_command,
            )

            result = run_make_command(instantiated_path, "setup")
            if result.returncode != 0:
                pytest.fail(
                    f"Setup failed:\nCommand: {result.command}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
                )
    except Exception:
        # Cleanup on error
        if instantiated_path is not None:
            cleanup_project_artifacts(instantiated_path)
        raise
    else:
        return instantiated_path


@pytest.fixture
def instantiated_template(tmp_path: Path) -> Path:
    """Instantiate the main template in a temporary directory.

    This fixture creates a fresh template instantiation for each test.
    All artifacts are cleaned up after the test completes, even if it fails.

    **Scope**: function - each test gets a fresh template
    **Returns**: Path to the instantiated project directory
    **Usage**: Use in tests that need an instantiated template

    Example:
        def test_something(instantiated_template: Any) -> None:
            # instantiated_template is a Path to the project directory
            assert (instantiated_template / "pyproject.toml").exists()
    """
    instantiated_path = None

    try:
        instantiated_path = _create_template_instance(
            tmp_path, "test-project", run_setup=False
        )
        yield instantiated_path

    finally:
        # Explicit cleanup of artifacts (only if instantiation succeeded)
        if instantiated_path is not None:
            cleanup_project_artifacts(instantiated_path)
        # tmp_path fixture handles directory removal


@pytest.fixture(scope="module")
def setup_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Setup fixture that runs make setup once for all CI tests in a module.

    This fixture uses module scope to run setup once and share it across
    all tests in the test module. This is more efficient than running setup
    for each test.

    **Scope**: module - shared across all tests in the module
    **Returns**: Path to the instantiated and set up project directory
    **Usage**: Use in CI tests that need a set up template

    Example:
        def test_ci_command(setup_template: Any) -> None:
            # setup_template has already run 'make setup'
            # Now run other CI commands
            pass
    """
    # Create a module-scoped temporary directory
    tmp_path = tmp_path_factory.mktemp("template-ci-module")
    instantiated_path = None

    try:
        instantiated_path = _create_template_instance(
            tmp_path, "test-project", run_setup=True
        )

        yield instantiated_path

    finally:
        # Explicit cleanup of artifacts (only if instantiation succeeded)
        if instantiated_path is not None:
            cleanup_project_artifacts(instantiated_path)
        # tmp_path_factory handles directory removal
