# Testing Troubleshooting

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
