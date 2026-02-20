# Configuration

For **project/answers configuration** (prompts, `.copier-answers.yml`, non-interactive use), see [Project configuration](../guides/configuration.md).

## Environment Variables

```bash
# Set log level for development
export REPOMAN_LOG_LEVEL=DEBUG

# Set Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## IDE Configuration

### VS Code

Copy the shared configuration to your workspace:

```bash
make setup-vscode
```

This copies `config/vscode/*` to `.vscode/` (settings, tasks, launch configs, recommended extensions). For both Cursor and VS Code, run `make setup-ide`.
