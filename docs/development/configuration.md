# Configuration

## Environment Variables

```bash
# Set log level for development
export REPOMAN_LOG_LEVEL=DEBUG

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## IDE Configuration

### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff"
}
```
