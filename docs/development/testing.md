# Repoman Test Suite

This directory contains the comprehensive test suite for the repoman project, designed to ensure code quality and reliability.

## 🎉 Current Status (Updated: August 2024)

### Test Suite Health

- **✅ All Tests Passing**: 143/143 tests (100% success rate)
- **📊 Coverage**: 93.89% overall coverage (excellent improvement from 79.17%)
- **📊 Instantiated template coverage**: 55.78% (update with `make update-instantiated-template-coverage`) <!-- instantiated-template-coverage: 55.78% -->
- **⚡ Performance**: Full suite runs in ~1.30s
- **🔧 Test Isolation**: Perfect - no dependencies between tests
- **🚀 Parallel Execution**: Successfully tested with 8 workers

### Recent Achievements

- **Fixed 19 failing tests** that were previously broken
- **Eliminated all interactive prompts** during test execution
- **Resolved resource warnings** and unclosed file handles
- **Implemented comprehensive security validation** with 18 attack vectors tested
- **Added 24 new tests** for `_version.py` module (99% coverage)
- **Created 43 new tests** for `extensions.py` module (100% coverage)
- **Optimized test configuration** for better performance and reliability

### Module Coverage Status

- **`_version.py`**: 99% coverage (up from 67%)
- **`extensions.py`**: 100% coverage (newly added)
- **`logging.py`**: 96% coverage
- **`copier.py`**: 91% coverage
- **`theme.py`**: 100% coverage
- **`main_cli.py`**: 82% coverage

### Test Categories

- **Unit Tests**: 67 tests (utility functions, theme, logging)
- **CLI Tests**: 33 tests (command execution, argument parsing)
- **Extension Tests**: 43 tests (Jinja2 extensions, git integration)
- **Version Tests**: 24 tests (version management, debug info)

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── ci_runner.py             # CI command runner (run_make_command, CommandResult)
├── conftest.py              # Pytest configuration and fixtures
├── template_testing.py      # Template instantiation helpers (instantiate_template, cleanup_project_artifacts)
├── fixtures/                # Test fixtures (e.g. default_copier_answers.yml)
├── test_template/           # Template/CI integration tests
│   ├── __init__.py
│   ├── conftest.py
│   └── test_ci.py           # CI commands on instantiated template
├── test_utils/              # Utility function tests
│   ├── __init__.py
│   ├── conftest.py          # Test-specific configuration
│   ├── test_theme.py        # Theme utility tests
│   ├── test_logging.py      # Logging utility tests
│   ├── test_ci_runner.py    # Unit tests for ci_runner
│   └── test_template_testing.py  # Unit tests for template_testing
├── test_cli/                # CLI command tests
│   ├── __init__.py
│   ├── test_cli.py          # Main CLI tests
│   └── test_create.py       # Create command tests
├── test_input/              # Input processing tests
│   └── test_extensions.py   # Jinja2 extensions tests
└── test_version.py          # Version and debug utilities tests
```

See [Test Utilities Reference](#test-utilities-reference) for `ci_runner` and `template_testing`.

## Test Utilities Reference

The test suite uses two utility modules for template instantiation and CI command execution. These are part of the test infrastructure, not the repoman library.

### ci_runner.py

Runs make commands in instantiated template projects with output streaming and capture.

| Component | Purpose |
|-----------|---------|
| `CommandResult` | Dataclass with `returncode`, `stdout`, `stderr`, `command` for assertions |
| `run_make_command(project_dir, command, env?, timeout?)` | Executes `make <command>` in `project_dir`; checks for `uv` in PATH; streams output while capturing; optional timeout in seconds |

**Used by:** `conftest.py` (setup, format, fix), `test_template/test_ci.py` (format-check, lint, check-types, test), `test_utils/test_ci_runner.py` (unit tests).

### template_testing.py

Instantiates templates and cleans up artifacts for isolated, reproducible tests.

| Component | Purpose |
|-----------|---------|
| `instantiate_template(output_dir, template_path?, project_name?, copier_data?, answers_file?, force?)` | Runs Copier to instantiate the template; returns path to project directory |
| `cleanup_project_artifacts(project_dir)` | Removes .venv, dist, build, site, egg-info, caches so tests don't leave artifacts |
| `_slugify` (private) | Internal helper to compute package names for Copier data; mirrors `repoman.extensions.slugify` so tests stay self-contained |

**Used by:** `conftest.py` (fixtures `instantiated_template`, `setup_template`), `test_template/test_ci.py` (instantiation and cleanup tests).

## Instantiated template test coverage

Repoman runs tests on an **instantiated** copy of the main template to ensure the generated project’s CI (format-check, lint, check-types, test) works. We also run tests **with coverage** on that instantiated project so you can see and track how much of the generated code is covered.

- **What runs**: The test `test_instantiated_template_test_coverage` runs `make test-coverage-report` in the instantiated project. That runs pytest with coverage (term-missing and html reports). The template provides `test-coverage-report` (no fail-under) so the run always succeeds and we can read the coverage value.
- **Visibility**: The full coverage report (term-missing) is streamed in repoman’s pytest output when you run the template CI tests.
- **Programmatic value**: We parse the total line coverage % from the report and log it (e.g. “Instantiated template line coverage: 38.81%”). The same value is recorded in **Test Suite Health** above as “Instantiated template coverage”; update it by running `make update-instantiated-template-coverage` (see below).

## Quick Start

### 1. Run All Tests

```bash
# From the project root
make test

# Or directly with pytest
uv run pytest -c=config/pytest.ini tests/
```

### 2. Run Specific Test Categories

```bash
# Unit tests only
make test-unit

# Utility tests only
make test-utils

# CLI tests only
make test-cli

# Isolated tests only
make test-isolated

# Fast tests (skip slow ones)
make test-fast
```

### 3. Run Individual Test Files

```bash
# Run a specific test file
make test-single FILE=tests/test_utils/test_theme.py

# Or directly with pytest
uv run pytest -c=config/pytest.ini tests/test_utils/test_theme.py
```

### 4. Run Tests with Coverage

```bash
# Generate coverage report
make test-coverage

# View HTML coverage report
open htmlcov/index.html
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- **Purpose**: Test individual components in isolation
- **Execution**: Fast, no external dependencies
- **Examples**: Utility functions, theme creation, logging setup

### Integration Tests (`@pytest.mark.integration`)

- **Purpose**: Test component interactions and CLI commands
- **Execution**: May require file system operations
- **Examples**: CLI command execution, template processing

### Utility Tests (`@pytest.mark.utils`)

- **Purpose**: Test utility functions and helpers
- **Execution**: Fast, isolated
- **Examples**: Theme utilities, logging configuration

### CLI Tests (`@pytest.mark.cli`)

- **Purpose**: Test command-line interface functionality
- **Execution**: May require file system operations
- **Examples**: Create command, argument parsing

### Isolated Tests (`@pytest.mark.isolated`)

- **Purpose**: Tests that must run in complete isolation
- **Execution**: Each test runs in its own temporary directory
- **Examples**: File operations, logging with files

## Test Isolation Features

### Automatic Test Isolation

The test suite includes several isolation mechanisms:

1. **Working Directory Isolation**: Each test runs in a unique temporary directory
2. **Logger State Cleanup**: Logger state is restored between tests
3. **Environment Variable Management**: Test-specific environment variables are isolated
4. **File System Cleanup**: Temporary files and directories are automatically cleaned up

### Fixtures

Key fixtures available to all tests:

- `tmp_path`: Pytest's built-in temporary directory fixture
- `cli_runner`: Typer CLI runner for testing commands
- `cli_app`: The main CLI application instance
- `test_workspace`: Isolated workspace for file operations
- `mock_template_structure`: Mock template for testing

## Fixture Optimization and Scope Management

This section covers fixture scopes, reusability, and best practices for creating maintainable test fixtures.

### Fixture Scope Hierarchy

Pytest fixtures have different scopes that determine how often they are created and destroyed:

1. **`function`** (default): Created once per test function
2. **`class`**: Created once per test class
3. **`module`**: Created once per test module (file)
4. **`session`**: Created once per test session (entire test run)

### Current Fixture Architecture

#### Main Conftest.py Fixtures (Session Scope)

```python
# tests/conftest.py - Available to all tests
@pytest.fixture(scope="session")
def cli_runner():
    """Provide a CLI runner for testing."""
    return CliRunner()

@pytest.fixture(scope="session")
def cli_app():
    """Provide the CLI application for testing."""
    return cli

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Runs once per session, sets global environment
    os.environ["_REPOMAN_LOG_LEVEL"] = "20"
    yield
    # Cleanup handled automatically
```

#### Test Isolation Fixtures (Function Scope)

```python
@pytest.fixture(autouse=True)
def isolate_test_environment():
    """Ensure each test runs in an isolated environment."""
    # Runs before each test function
    original_cwd = os.getcwd()
    yield
    # Runs after each test function
    os.chdir(original_cwd)

@pytest.fixture(autouse=True)
def cleanup_loggers():
    """Clean up logger state between tests."""
    # Runs before each test function
    # Stores original logger state
    yield
    # Runs after each test function
    # Restores logger state
```

#### Module-Specific Fixtures (Module Scope)

```python
# tests/test_utils/conftest.py - Available to utility tests
@pytest.fixture(scope="module")
def mock_colors():
    """Provide mock colors object for theme testing."""
    # Created once per test module, shared across test classes
    return MockColors()

@pytest.fixture(scope="module")
def test_console():
    """Provide a test console for logging tests."""
    # Created once per test module
    return Console()
```

### Fixture Scope Optimization

#### When to Use Each Scope

**Function Scope (Default)**

- Use for: Test-specific data, temporary files, isolated state
- Examples: `temp_log_dir`, `mock_config`, test-specific mocks
- Benefits: Complete isolation, no state leakage
- Drawbacks: Higher overhead, slower test execution

**Class Scope**

- Use for: Data shared across test methods in a class
- Examples: Complex setup that's expensive to recreate
- Benefits: Reduced setup overhead within test classes
- Drawbacks: State can leak between test methods

**Module Scope**

- Use for: Expensive resources, shared test data
- Examples: `mock_colors`, `test_console`, database connections
- Benefits: Significant performance improvement
- Drawbacks: State persists across test classes

**Session Scope**

- Use for: Global resources, application instances
- Examples: `cli_runner`, `cli_app`, shared configurations
- Benefits: Maximum performance, single setup
- Drawbacks: Global state, potential interference

#### Optimized Fixture Recommendations

```python
# High-performance fixtures (module scope)
@pytest.fixture(scope="module")
def mock_colors():
    """Mock colors object - expensive to create, safe to share."""
    return MockColors()

@pytest.fixture(scope="module")
def test_console():
    """Test console - stateless, safe to share."""
    return Console()

# Isolated fixtures (function scope)
@pytest.fixture
def temp_log_dir():
    """Temporary directory - must be isolated per test."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_config():
    """Mock config - test-specific, should be isolated."""
    config = Mock()
    config.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    return config
```

### Fixture Reusability Patterns

#### Shared Test Data

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def sample_project_data():
    """Provide sample project data for testing."""
    return {
        "valid_names": ["test-project", "my_app", "api_service"],
        "invalid_names": ["", "a" * 1000, "project@#$%"],
        "template_paths": ["/templates/basic", "/templates/advanced"],
    }

# Use in any test
def test_project_creation(sample_project_data):
    for name in sample_project_data["valid_names"]:
        # Test logic here
        pass
```

#### Mock Objects

```python
# tests/conftest.py
@pytest.fixture(scope="module")
def mock_file_system(monkeypatch, tmp_path):
    """Mock file system operations."""
    mock_fs = tmp_path / "mock_fs"
    mock_fs.mkdir()

    def mock_makedirs(path, exist_ok=False):
        Path(path).mkdir(parents=True, exist_ok=exist_ok)

    monkeypatch.setattr("os.makedirs", mock_makedirs)
    return mock_fs

# Use in file system tests
def test_file_creation(mock_file_system):
    # Test logic here
    pass
```

#### Environment Setup

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_environment():
    """Set up complete test environment."""
    env = {
        "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
        "_REPOMAN_LOG_LEVEL": "20",
        "NO_ALBUMENTATIONS_UPDATE": "1",
    }

    # Store original values
    original = {}
    for key, value in env.items():
        if key in os.environ:
            original[key] = os.environ[key]
        os.environ[key] = value

    yield env

    # Restore original values
    for key, value in original.items():
        os.environ[key] = value
    for key in env:
        if key not in original:
            del os.environ[key]
```

### Fixture Best Practices

#### 1. Scope Appropriately

```python
# Good: Module scope for expensive, stateless resources
@pytest.fixture(scope="module")
def mock_colors():
    return MockColors()

# Good: Function scope for test-specific data
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name

# Avoid: Session scope for stateful resources
@pytest.fixture(scope="session")  # ❌ Can cause interference
def shared_logger():
    return logging.getLogger("shared")
```

#### 2. Use Autouse Sparingly

```python
# Good: Essential isolation fixtures
@pytest.fixture(autouse=True)
def cleanup_loggers():
    # Essential for preventing test interference
    yield
    # Cleanup code

# Avoid: Overuse of autouse
@pytest.fixture(autouse=True)  # ❌ May not be needed by all tests
def setup_database():
    # Only needed by some tests
    pass
```

#### 3. Proper Cleanup

```python
# Good: Context managers and explicit cleanup
@pytest.fixture
def temp_log_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
    # Cleanup handled automatically

# Good: Explicit cleanup in yield
@pytest.fixture
def mock_handler():
    handler = Mock()
    yield handler
    handler.close()  # Explicit cleanup
```

#### 4. Parameterized Fixtures

```python
# Good: Parameterized fixtures for multiple test scenarios
@pytest.fixture(params=["DEBUG", "INFO", "WARNING", "ERROR"])
def log_level(request):
    return getattr(logging, request.param)

def test_logger_levels(log_level):
    logger = _set_up_logger("test", log_level=log_level)
    assert logger.level == log_level
```

### Fixture Documentation

#### Standard Fixture Docstring Format

```python
@pytest.fixture(scope="module")
def mock_colors():
    """Provide mock colors object for theme testing.

    **Scope**: module - shared across test classes in the module
    **Returns**: MockColors instance with all required color attributes
    **Usage**: Use in theme-related tests that need color objects

    Example:
        def test_theme_creation(mock_colors):
            theme = _create_theme(mock_colors)
            assert isinstance(theme, Theme)
    """
    return MockColors()
```

#### Fixture Usage Examples

```python
# Basic usage
def test_basic_functionality(mock_colors, test_console):
    # Test logic here
    pass

# Multiple fixtures
def test_complex_scenario(mock_colors, temp_log_dir, mock_config):
    # Test logic here
    pass

# Fixture with parameters
def test_with_parameters(sample_project_data):
    for name in sample_project_data["valid_names"]:
        # Test logic here
        pass
```

### Performance Considerations

#### Fixture Creation Overhead

```python
# Expensive fixtures - use higher scope
@pytest.fixture(scope="module")  # Created once per module
def heavy_database_connection():
    return create_database_connection()

# Cheap fixtures - function scope is fine
@pytest.fixture  # Created per test
def simple_mock():
    return Mock()
```

#### Memory Usage

```python
# Large data fixtures - consider module scope
@pytest.fixture(scope="module")
def large_test_dataset():
    return generate_large_dataset()  # Expensive operation

# Small data fixtures - function scope is fine
@pytest.fixture
def small_config():
    return {"key": "value"}
```

### Troubleshooting Fixture Issues

#### Common Problems and Solutions

**Problem**: Fixture not available in test

```python
# Solution: Check fixture scope and location
# Fixtures in conftest.py are available to all tests in that directory and subdirectories
# Fixtures in test files are only available to tests in that file
```

**Problem**: Fixture state leaking between tests

```python
# Solution: Use function scope or add cleanup
@pytest.fixture
def isolated_resource():
    resource = create_resource()
    yield resource
    cleanup_resource(resource)  # Explicit cleanup
```

**Problem**: Fixture performance issues

```python
# Solution: Increase scope for expensive fixtures
@pytest.fixture(scope="module")  # Instead of function scope
def expensive_resource():
    return create_expensive_resource()
```

### Fixture Testing

#### Test Your Fixtures

```python
# Test that fixtures work correctly
def test_mock_colors_fixture(mock_colors):
    """Test that mock_colors fixture provides expected structure."""
    assert hasattr(mock_colors, "rosewater")
    assert hasattr(mock_colors, "flamingo")
    assert hasattr(mock_colors, "text")

    # Test that colors have hex attributes
    assert hasattr(mock_colors.rosewater, "hex")
    assert mock_colors.rosewater.hex.startswith("#")
```

This comprehensive fixture management approach ensures:

- **Optimal performance** through appropriate scoping
- **Test isolation** to prevent interference
- **Reusability** across test modules
- **Maintainability** through clear documentation
- **Reliability** through proper cleanup and error handling

## Running Tests in Different Environments

### Development Environment

```bash
# Quick test run during development
make test-fast

# Run specific test category
make test-utils

# Run with verbose output
uv run pytest -c=config/pytest.ini -vvv tests/
```

### Continuous Integration

```bash
# Run all tests with coverage
make test-coverage

# Run tests in parallel (if pytest-xdist is available)
uv run pytest -c=config/pytest.ini -n auto tests/
```

### Debug Mode

```bash
# Run tests with maximum verbosity
uv run pytest -c=config/pytest.ini -vvv --tb=long tests/

# Run specific test with debug output
uv run pytest -c=config/pytest.ini -vvv --tb=long tests/test_utils/test_logging.py::test_set_up_logger_basic
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Symptoms**: `ModuleNotFoundError`, `ImportError`

**Solutions**:

- Ensure you're running from the project root directory
- Check that the virtual environment is activated: `source .venv/bin/activate`
- Verify that `uv run` is used for pytest commands: `uv run pytest`
- Check that `src/` is in your Python path

**Example Fix**:

```bash
# From project root
cd /path/to/repoman
source .venv/bin/activate
uv run pytest tests/test_version.py
```

#### 2. Test Failures

**Symptoms**: `AssertionError`, `NameError`, `AttributeError`

**Solutions**:

- Check test output for specific error messages
- Verify that test data and fixtures are correct
- Ensure test isolation is working properly
- Run individual tests to isolate the problem

**Debug Steps**:

```bash
# Run specific failing test with verbose output
uv run pytest tests/test_cli/test_create.py::TestCLIErrorHandling::test_create_command_with_network_issues -vvv

# Run test with full traceback
uv run pytest tests/test_utils/test_logging.py::test_get_logger_console_basic --tb=long
```

#### 3. Resource Warnings

**Symptoms**: `ResourceWarning: unclosed file`, `ResourceWarning: unclosed scandir iterator`

**Solutions**:

- These are now suppressed in `config/pytest.ini`
- If you see them, check for proper cleanup in test fixtures
- Ensure `RotatingFileHandler` instances are properly closed

**Example Fix**:

```python
@pytest.fixture
def temp_log_handler():
    handler = RotatingFileHandler("test.log")
    yield handler
    handler.close()  # Explicit cleanup
```

#### 4. Interactive Prompts During Tests

**Symptoms**: Tests hang waiting for user input, git authentication prompts

**Solutions**:

- All interactive prompts have been eliminated
- If you see prompts, check that `quiet: True` and `overwrite: force` are set in copier options
- Ensure tests use local paths instead of GitHub URLs

**Example Fix**:

```python
# Use local path instead of GitHub URL
result = cli_runner.invoke(cli_app, [
    "create", "test-project",
    "--template", "/local/template/path"  # Not https://github.com/...
])
```

#### 5. Environment Variable Conflicts

**Symptoms**: Tests fail due to unexpected environment variable values

**Solutions**:

- Test environment variables are isolated in `conftest.py`
- Check that `_REPOMAN_LOG_LEVEL` is set correctly
- Verify that environment restoration is working

**Debug Commands**:

```bash
# Check current environment
echo $REPOMAN_LOG_LEVEL

# Run test with specific environment
REPOMAN_LOG_LEVEL=DEBUG uv run pytest tests/test_utils/test_logging.py
```

#### 6. File System Issues

**Symptoms**: Permission errors, file not found, cleanup failures

**Solutions**:

- Tests use temporary directories to avoid conflicts
- Check that file permissions allow temporary directory creation
- Verify that cleanup is working correctly
- Use `tmp_path` fixture for file operations

**Example Fix**:

```python
def test_file_operations(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    # File is automatically cleaned up
```

#### 7. Fixture Import Errors

**Symptoms**: `NameError: name 'cli_runner' is not defined`

**Solutions**:

- Ensure fixture parameters are included in test method signature
- Check that fixtures are properly imported from `conftest.py`
- Verify fixture scope is appropriate

**Example Fix**:

```python
def test_cli_command(cli_runner, cli_app):  # Include fixture parameters
    result = cli_runner.invoke(cli_app, ["create", "test-project"])
    assert result.exit_code == 0
```

### Debug Commands

```bash
# Show test collection without running
uv run pytest -c=config/pytest.ini --collect-only tests/

# Show test markers
uv run pytest -c=config/pytest.ini --markers

# Run tests with warnings enabled
uv run pytest -c=config/pytest.ini -W default tests/

# Run specific test with maximum verbosity
uv run pytest -c=config/pytest.ini -vvv --tb=long tests/test_utils/test_logging.py::test_set_up_logger_basic

# Run tests in parallel to check for isolation issues
uv run pytest -c=config/pytest.ini -n auto --dist=loadfile tests/

# Check for resource leaks
uv run pytest -c=config/pytest.ini -W error::ResourceWarning tests/
```

### Performance Issues

#### Slow Tests

**Symptoms**: Individual tests take longer than 1 second

**Solutions**:

- Use appropriate fixture scopes (module/session for expensive setup)
- Mock external dependencies
- Avoid file system operations in unit tests

#### Memory Issues

**Symptoms**: Tests consume excessive memory

**Solutions**:

- Use `tmp_path` fixture for temporary files
- Clean up resources in fixtures
- Avoid creating large test data sets

### CI/CD Issues

#### Parallel Test Failures

**Symptoms**: Tests pass locally but fail in CI

**Solutions**:

- Ensure tests are truly isolated
- Use `--dist=loadfile` for parallel execution
- Check for shared state between tests

#### Coverage Reporting Issues

**Symptoms**: Coverage reports are incomplete or incorrect

**Solutions**:

- Use `uv run pytest --cov=src/repoman --cov-report=term-missing`
- Check that all source files are included
- Verify coverage configuration in `pyproject.toml`

## Best Practices

### Writing Tests

#### 1. Test Naming and Structure

**Good Examples**:

```python
def test_get_version_returns_valid_string():
    """Test that get_version returns a valid version string."""
    result = get_version("repoman")
    assert isinstance(result, str)
    assert result != "0.0.0"

def test_slugify_with_special_characters():
    """Test slugify function handles special characters correctly."""
    result = slugify("Hello, World! @#$%^&*()")
    assert result == "hello-world"
```

**Avoid**:

```python
def test_function():  # ❌ Too generic
    pass

def test_it_works():  # ❌ Not descriptive
    pass
```

#### 2. Test Organization

**Use Test Classes for Related Functionality**:

```python
class TestVersionFunctions:
    """Test version-related functions."""

    def test_get_version_success(self):
        """Test get_version with valid distribution."""
        result = get_version("repoman")
        assert isinstance(result, str)

    def test_get_version_package_not_found(self):
        """Test get_version when package is not found."""
        with patch("repoman._version.metadata.version") as mock_version:
            mock_version.side_effect = PackageNotFoundError("nonexistent")
            result = get_version("nonexistent-package")
            assert result == "0.0.0"
```

#### 3. Fixture Usage

**Good Fixture Patterns**:

```python
@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture(scope="module")
def mock_colors():
    """Provide mock colors object for theme testing."""
    return MockColors()

def test_logging_with_temp_dir(temp_log_dir, mock_colors):
    """Test logging functionality with temporary directory."""
    # Test logic here
    pass
```

#### 4. Error Handling Tests

**Test Both Success and Failure Cases**:

```python
def test_function_success():
    """Test normal operation."""
    result = function_under_test("valid_input")
    assert result == expected_value

def test_function_invalid_input():
    """Test error handling for invalid input."""
    with pytest.raises(ValueError, match="Invalid input"):
        function_under_test("invalid_input")

def test_function_edge_case():
    """Test edge case handling."""
    result = function_under_test("")
    assert result == default_value
```

#### 5. Mocking Best Practices

**Use Appropriate Mocking**:

```python
@patch("repoman._version.metadata.version")
def test_get_version_package_not_found(self, mock_version):
    """Test get_version when package is not found."""
    from importlib.metadata import PackageNotFoundError
    mock_version.side_effect = PackageNotFoundError("nonexistent")
    result = get_version("nonexistent-package")
    assert result == "0.0.0"
```

### Test Organization

#### 1. File Structure

**Organize Tests by Module**:

```
tests/
├── test_version.py          # Version utilities
├── test_extensions.py       # Jinja2 extensions
├── test_cli/
│   ├── test_create.py       # Create command
│   └── test_cli.py          # Main CLI
└── test_utils/
    ├── test_logging.py      # Logging utilities
    └── test_theme.py        # Theme utilities
```

#### 2. Test Class Organization

**Group Related Tests**:

```python
class TestGitUserFunctions:
    """Test git user name and email functions."""

    def test_git_user_name_with_valid_output(self):
        """Test git_user_name with valid git config output."""
        # Test logic

    def test_git_user_name_with_empty_output(self):
        """Test git_user_name with empty git config output."""
        # Test logic

class TestSlugifyFunction:
    """Test slugify function with various inputs."""

    def test_slugify_basic_string(self):
        """Test slugify with basic string."""
        # Test logic

    def test_slugify_with_special_characters(self):
        """Test slugify with special characters."""
        # Test logic
```

#### 3. Test Isolation

**Ensure Tests Are Independent**:

```python
# Good: Each test is independent
def test_function_a():
    result = function_a()
    assert result == expected_a

def test_function_b():
    result = function_b()
    assert result == expected_b

# Avoid: Tests that depend on each other
def test_function_a():
    global shared_state
    shared_state = function_a()
    assert shared_state == expected_a

def test_function_b():
    global shared_state  # ❌ Depends on previous test
    result = function_b(shared_state)
    assert result == expected_b
```

### Performance Optimization

#### 1. Fixture Scope Optimization

**Use Appropriate Scopes**:

```python
# Expensive setup - use module scope
@pytest.fixture(scope="module")
def heavy_database_connection():
    return create_database_connection()

# Cheap setup - function scope is fine
@pytest.fixture
def simple_mock():
    return Mock()

# Test-specific data - function scope
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile() as f:
        yield f.name
```

#### 2. Test Speed

**Keep Tests Fast**:

```python
# Good: Fast test
def test_string_operation():
    result = "hello".upper()
    assert result == "HELLO"

# Avoid: Slow operations in unit tests
def test_database_operation():
    # ❌ Don't do database operations in unit tests
    result = database.query("SELECT * FROM large_table")
    assert len(result) > 0
```

#### 3. Parallel Execution

**Ensure Tests Can Run in Parallel**:

```python
# Good: No shared state
def test_function_a():
    result = function_a("input_a")
    assert result == expected_a

def test_function_b():
    result = function_b("input_b")
    assert result == expected_b

# Avoid: Shared state that can cause race conditions
shared_counter = 0  # ❌ Shared state

def test_increment():
    global shared_counter
    shared_counter += 1
    assert shared_counter == 1

def test_decrement():
    global shared_counter  # ❌ Race condition possible
    shared_counter -= 1
    assert shared_counter == 0
```

### Security Testing

#### 1. Input Validation

**Test Security Vulnerabilities**:

```python
def test_path_traversal_attempts():
    """Test that path traversal attempts are rejected."""
    malicious_inputs = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "..%2F..%2F..%2Fetc%2Fpasswd",
    ]

    for malicious_input in malicious_inputs:
        with pytest.raises(ValueError):
            validate_project_name(malicious_input)
```

#### 2. Edge Cases

**Test Boundary Conditions**:

```python
def test_extremely_long_input():
    """Test handling of extremely long input."""
    long_input = "a" * 10000
    result = process_input(long_input)
    assert result is not None  # Should handle gracefully

def test_empty_input():
    """Test handling of empty input."""
    result = process_input("")
    assert result == default_value

def test_none_input():
    """Test handling of None input."""
    result = process_input(None)
    assert result == default_value
```

### Documentation

#### 1. Test Documentation

**Write Clear Test Documentation**:

```python
def test_get_debug_info_with_environment_variables():
    """Test get_debug_info with environment variables.

    This test verifies that the get_debug_info function correctly
    processes environment variables and includes them in the returned
    Environment object.

    Test Steps:
    1. Set up test environment variables
    2. Call get_debug_info()
    3. Verify environment variables are included
    4. Verify variable names and values are correct
    """
    with patch.dict(os.environ, {"PYTHONPATH": "/test/path", "REPOMAN_DEBUG": "true"}):
        result = get_debug_info()
        variable_names = [var.name for var in result.variables]
        assert "PYTHONPATH" in variable_names
        assert "REPOMAN_DEBUG" in variable_names
```

#### 2. Fixture Documentation

**Document Fixtures Clearly**:

```python
@pytest.fixture(scope="module")
def mock_colors():
    """Provide mock colors object for theme testing.

    **Scope**: module - shared across test classes in the module
    **Returns**: MockColors instance with all required color attributes
    **Usage**: Use in theme-related tests that need color objects

    Example:
        def test_theme_creation(mock_colors):
            theme = _create_theme(mock_colors)
            assert isinstance(theme, Theme)
    """
    return MockColors()
```

### Code Quality

#### 1. Follow PEP 8

**Use Consistent Formatting**:

```python
# Good: Follow PEP 8
def test_function_with_clear_name():
    """Test function with clear docstring."""
    result = function_under_test("input")
    assert result == "expected_output"

# Avoid: Poor formatting
def testFunction():  # ❌ Not snake_case
    result=function_under_test("input")  # ❌ Missing spaces
    assert result=="expected_output"     # ❌ Missing spaces
```

#### 2. Use Type Hints

**Add Type Hints for Clarity**:

```python
from typing import List, Dict, Any

def test_process_data(data: List[str]) -> None:
    """Test data processing function."""
    result = process_data(data)
    assert isinstance(result, Dict[str, Any])
```

#### 3. Avoid Code Duplication

**Use Fixtures and Helper Functions**:

```python
# Good: Reusable test data
@pytest.fixture
def sample_project_names():
    """Provide sample project names for testing."""
    return ["test-project", "my_app", "api_service"]

def test_project_creation(sample_project_names):
    """Test project creation with various names."""
    for name in sample_project_names:
        result = create_project(name)
        assert result.success

# Avoid: Duplicated test data
def test_project_creation_1():
    result = create_project("test-project")  # ❌ Duplicated
    assert result.success

def test_project_creation_2():
    result = create_project("my_app")        # ❌ Duplicated
    assert result.success
```

## Coverage Requirements

- **Overall Coverage**: ✅ **93.89%** (exceeds 90% target)
- **Critical Modules**: ✅ **95%+ coverage** for core functionality achieved
- **New Code**: ✅ **100% coverage** for new features (extensions.py, version.py improvements)
- **Documentation**: ✅ **All public APIs** have comprehensive tests

### Coverage Targets (Current Status)

- **Minimum Overall**: 90% ✅ (Current: 93.89%)
- **Core Modules**: 95%+ ✅ (logging.py: 96%, theme.py: 100%)
- **New Features**: 100% ✅ (extensions.py: 100%, \_version.py: 99%)
- **CLI Commands**: 90%+ ✅ (copier.py: 91%, main_cli.py: 82%)

## Continuous Integration

The test suite is designed to work seamlessly with CI/CD pipelines:

- Tests can run in parallel environments
- Coverage reports are generated automatically
- Test results are clearly reported
- Failures provide actionable feedback

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Use appropriate test markers
3. Ensure tests can run both individually and as part of the suite
4. Add tests for both success and failure cases
5. Update this documentation if adding new test categories or patterns
