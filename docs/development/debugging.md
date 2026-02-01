# Debugging

## Common Issues

1. **Import Errors**:

   ```bash
   # Ensure you're in the project root
   cd /path/to/repoman

   # Activate virtual environment
   source .venv/bin/activate

   # Use uv run for Python commands
   uv run python -c "import repoman"
   ```

2. **Test Failures**:

   ```bash
   # Run specific failing test with verbose output
   uv run pytest tests/test_cli/test_create.py::test_create_command_basic -vvv

   # Run with full traceback
   uv run pytest tests/test_cli/test_create.py::test_create_command_basic --tb=long
   ```

3. **Dependency Issues**:

   ```bash
   # Reinstall dependencies
   uv sync --reinstall

   # Update lock file
   uv lock --upgrade
   ```

## Debug Tools

```bash
# Run with debug output
uv run pytest -vvv --tb=long tests/

# Run specific test with debugger
uv run python -m pdb -m pytest tests/test_cli/test_create.py::test_create_command_basic

# Check environment
uv run python -c "import sys; print(sys.path)"
```
