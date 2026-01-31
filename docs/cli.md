# CLI Reference

Repoman provides a command-line interface for generating and managing Python projects from templates.

## Running repoman

From the project root (with dependencies installed):

```bash
uv run repoman [COMMAND] [OPTIONS]
# or
uv run python -m repoman [COMMAND] [OPTIONS]
```

If repoman is installed (e.g. `pip install` or `uv pip install -e .`):

```bash
repoman [COMMAND] [OPTIONS]
```

## Global options

These options apply to the main `repoman` command and can be used with any subcommand:

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Enable verbose (DEBUG) logging |
| `--version` | | Print version and exit |
| `--debug-info` | | Print debug information |
| `--theme` | | Set theme: `light` or `dark` (default: dark) |
| `--dry-run` | | Show changes but do not execute them |
| `--install-completion` | | Install shell completion |
| `--show-completion` | | Show shell completion script |
| `--help` | | Show help and exit |

## Commands

### create

Create a new Python project using the repoman template.

```bash
repoman create PROJECT_NAME [OPTIONS]
```

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `PROJECT_NAME` | Yes | Name of the project to create |

**Options**

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Path to custom template (defaults to bundled main template) |
| `--output` | `-o` | Output directory (defaults to current directory) |
| `--answers` | `-a` | Path to answers file for non-interactive use |
| `--force` | `-f` | Force overwrite of existing files |
| `--dry-run` | | Show what would be created without creating |

**Examples**

```bash
repoman create my-new-project
repoman create my-app --output /path/to/parent --force
repoman create my-app --answers .copier-answers.yml --dry-run
```

### update

Update an existing Python project using the repoman template (re-run Copier on a project that was created with repoman).

```bash
repoman update PROJECT_DIR [OPTIONS]
```

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `PROJECT_DIR` | Yes | Path to the project directory to update |

**Options**

| Option | Short | Description |
|--------|-------|-------------|
| `--template` | `-t` | Override template path (normally read from `.copier-answers.yml`) |
| `--vcs-ref` | `-r` | Git ref/tag to update to (defaults to latest) |
| `--answers` | `-a` | Path to `.copier-answers.yml` (defaults to project_dir/.copier-answers.yml) |
| `--force` | `-f` | Force overwrite without asking |
| `--dry-run` | | Show what would be updated without making changes |
| `--conflict` | | Conflict resolution: `inline` or `rej` (default: inline) |

**Examples**

```bash
repoman update ./my-project
repoman update /path/to/my-project --vcs-ref v1.0 --dry-run
```

### generator add

Add a new CLI command to a repoman-generated project. Generates a command module and a test file.

```bash
repoman generator add COMMAND_NAME [OPTIONS]
```

**Arguments**

| Argument | Required | Description |
|----------|----------|-------------|
| `COMMAND_NAME` | Yes | Name of the command to create (valid Python identifier) |

**Options**

| Option | Short | Description |
|--------|-------|-------------|
| `--project-dir` | `-d` | Project directory (defaults to current directory) |
| `--answers` | `-a` | Path to `.copier-answers.yml` file |
| `--force` | `-f` | Overwrite existing files |
| `--dry-run` | | Show what would be created without creating |

**Examples**

```bash
cd my-repoman-project
repoman generator add mycommand
repoman generator add mycommand --project-dir /path/to/project --dry-run
```

## Getting help

```bash
repoman --help
repoman create --help
repoman update --help
repoman generator add --help
```
