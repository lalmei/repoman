# Testing Fixtures

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
