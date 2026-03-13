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

| Option                 | Short | Description                                  |
| ---------------------- | ----- | -------------------------------------------- |
| `--verbose`            | `-v`  | Enable verbose (DEBUG) logging               |
| `--version`            |       | Print version and exit                       |
| `--debug-info`         |       | Print debug information                      |
| `--theme`              |       | Set theme: `light` or `dark` (default: dark) |
| `--dry-run`            |       | Show changes but do not execute them         |
| `--install-completion` |       | Install shell completion                     |
| `--show-completion`    |       | Show shell completion script                 |
| `--help`               |       | Show help and exit                           |

## Commands

### create

Create a new Python project using the repoman template. For the default (interactive or answers-based) flow, use options; project name is passed with `--project_name` / `-pn`. Alternatively, use a subcommand (e.g. `create cli`) and pass the project name as a positional argument.

```bash
repoman create [OPTIONS]
# or with a preset subcommand (positional project name):
repoman create cli PROJECT_NAME [OPTIONS]
```

**Options (default create)**

| Option          | Short | Description                                                                 |
| --------------- | ----- | --------------------------------------------------------------------------- |
| `--project_name` | `-pn` | **Required** for default create. Name of the project to create.             |
| `--template`    | `-t`  | Path to custom template (defaults to bundled main template)                 |
| `--output`      | `-o`  | Output directory (defaults to current directory)                             |
| `--answers`     | `-a`  | Path to answers file for non-interactive use                                |
| `--preset`      | `-p`  | Use a preset: `cli`, `docs-only`, `library`, `fastapi`, `rag` (non-interactive) |
| `--force`       | `-f`  | Force overwrite of existing files                                          |
| `--dry-run`     |       | Show what would be created without creating                                 |

**Examples (default create)**

```bash
repoman create --project_name my-new-project
repoman create -pn my-app --output /path/to/parent --force
repoman create --project_name my-app --answers .copier-answers.yml --dry-run
repoman create -pn my-app --preset cli
```

**Create subcommands (preset-based, positional project name)**

Each subcommand creates a project using a preset and takes the project name as a positional argument:

| Subcommand | Preset   | Description                                              |
| ---------- | -------- | -------------------------------------------------------- |
| `create cli`     | cli      | Plain CLI project (no FastAPI, RAG, dataset)             |
| `create docs`    | docs_only| Documentation-only project                                |
| `create library` | library  | Library-style project (no CLI entry point)               |
| `create fastapi` | fastapi  | Project with FastAPI enabled                             |
| `create rag`     | rag      | Project with FastAPI + RAG + dataset                     |

**Examples (subcommands)**

```bash
repoman create cli my-cli-app
repoman create library my-lib --dry-run
repoman create docs docs-project --output /path/to/parent
repoman create fastapi my-api
repoman create rag my-rag-service --force
```

### update

Update an existing Python project using the repoman template (re-run Copier on a project that was created with repoman).

```bash
repoman update PROJECT_DIR [OPTIONS]
```

**Arguments**

| Argument      | Required | Description                             |
| ------------- | -------- | --------------------------------------- |
| `PROJECT_DIR` | Yes      | Path to the project directory to update |

**Options**

| Option       | Short | Description                                                                 |
| ------------ | ----- | --------------------------------------------------------------------------- |
| `--template` | `-t`  | Override template path (normally read from `.copier-answers.yml`)           |
| `--vcs-ref`  | `-r`  | Git ref/tag to update to (defaults to latest)                               |
| `--answers`  | `-a`  | Path to `.copier-answers.yml` (defaults to project_dir/.copier-answers.yml) |
| `--force`    | `-f`  | Force overwrite without asking                                              |
| `--dry-run`  |       | Show what would be updated without making changes                           |
| `--conflict` |       | Conflict resolution: `inline` or `rej` (default: inline)                    |
| `--skip-extensions` | | Skip syncing Copier-managed extensions after the base update               |

**Examples**

```bash
repoman update ./my-project
repoman update /path/to/my-project --vcs-ref v1.0 --dry-run
```

### config

Manage repoman and template configuration (e.g. generate an answers file for non-interactive create).

```bash
repoman config [COMMAND] [OPTIONS]
```

**Subcommands**

| Subcommand   | Description                                                |
| ------------ | ---------------------------------------------------------- |
| `init`       | Generate a template answers file for use with `repoman create --answers` |
| `path`       | Show the path where repoman loads/writes config            |
| `validate`   | Validate an answers file against the template schema       |
| `show`       | Print the bundled template answers or a single key         |
| `list-keys`  | List prompt keys expected by the template (from copier.yml) |

#### config init

Generate a template `.copier-answers.yml` (or custom path) that you can edit and pass to `repoman create --answers`.

```bash
repoman config init [OPTIONS]
```

**Options**

| Option       | Short | Description                                                                            |
| ------------ | ----- | -------------------------------------------------------------------------------------- |
| `--output`   | `-o`  | Output path for the answers file (default: `.copier-answers.yml` in current directory) |
| `--template` | `-t`  | Path to a custom template file (default: use bundled template)                         |
| `--force`    | `-f`  | Overwrite existing file                                                                |

**Examples**

```bash
repoman config init
repoman config init --output path/to/.copier-answers.yml
repoman config init -o my-answers.yml --force
```

#### config path

Print the path where repoman loads or writes its JSON config (respects `REPOMAN_CONFIG_PATH` and `--config`).

```bash
repoman config path [OPTIONS]
```

**Options**

| Option    | Short | Description                                                        |
| --------- | ----- | ------------------------------------------------------------------ |
| `--config`| `-c`  | Override config path (default: REPOMAN_CONFIG_PATH or OS default)  |

**Examples**

```bash
repoman config path
repoman config path --config /custom/path/config.json
```

#### config validate

Validate an answers file against the template schema (checks required keys and types).

```bash
repoman config validate [OPTIONS]
```

**Options**

| Option     | Short | Description                                              |
| ---------- | ----- | -------------------------------------------------------- |
| `--answers`| `-a`  | Path to the answers file (default: `.copier-answers.yml`) |
| `--strict` |       | Fail on extra keys not in schema                          |
| `--quiet`  | `-q`  | Only exit with code; no success message                  |

**Examples**

```bash
repoman config validate
repoman config validate --answers path/to/.copier-answers.yml --strict
```

#### config show

Print the bundled template answers to stdout, or a single key's value. Optionally write to a file.

```bash
repoman config show [OPTIONS]
```

**Options**

| Option    | Short | Description                                    |
| --------- | ----- | ---------------------------------------------- |
| `--key`   | `-k`  | Show only this key's value                     |
| `--output`| `-o`  | Write output to this path instead of stdout    |
| `--force` | `-f`  | Overwrite existing file when using `--output`  |

**Examples**

```bash
repoman config show
repoman config show --key project_name
repoman config show --output my-template.yml
```

#### config list-keys

List prompt keys the template expects (from copier.yml). Excludes copier meta keys.

```bash
repoman config list-keys [OPTIONS]
```

**Options**

| Option          | Short | Description                          |
| --------------- | ----- | ------------------------------------ |
| `--format`      | `-f`  | Output format: `table` (default) or `json` |
| `--include-meta`|       | Include type, default, and when for each key |

**Examples**

```bash
repoman config list-keys
repoman config list-keys --format json
repoman config list-keys --include-meta
```

### hotspots

Find code hotspots that may need refactoring by analyzing git history. Uses commits count, code churn, and contributor count to identify files with high change activity.

```bash
repoman hotspots [OPTIONS]
```

**Options**

| Option       | Short | Description                                                         |
| ------------ | ----- | ------------------------------------------------------------------- |
| `--path`     | `-p`  | Path to the git repository (default: current directory)              |
| `--limit`    | `-n`  | Maximum number of files to show (default: 20)                        |
| `--since`    |       | Start date (YYYY-MM-DD) for commit range                            |
| `--to`       |       | End date (YYYY-MM-DD) for commit range                               |
| `--extensions` | `-e` | Comma-separated file extensions to include (e.g. `.py,.ts`)         |
| `--format`   | `-f`  | Output format: `table` (default), `json`, or `html`                  |
| `--output`   | `-o`  | Output directory for html report (default: `hotspot_report`)         |
| `--no-header`|       | Hide column headers (for piping)                                    |

**Examples**

```bash
repoman hotspots
repoman hotspots --path /path/to/repo --limit 10
repoman hotspots --format html -o hotspot_report
repoman hotspots --since 2024-01-01 --extensions .py,.ts --format json
repoman hotspots -n 5 -f json
```

### generator add

Add a new CLI command to a repoman-generated project. Generates a command module and a test file, and stores extension instance metadata for future sync/update.

```bash
repoman generator add COMMAND_NAME [OPTIONS]
```

**Arguments**

| Argument       | Required | Description                                             |
| -------------- | -------- | ------------------------------------------------------- |
| `COMMAND_NAME` | Yes      | Name of the command to create (valid Python identifier) |

**Options**

| Option          | Short | Description                                       |
| --------------- | ----- | ------------------------------------------------- |
| `--project-dir` | `-d`  | Project directory (defaults to current directory) |
| `--answers`     | `-a`  | Path to `.copier-answers.yml` file                |
| `--kind`        |       | Extension kind: `command` (default) or `graphrag` |
| `--force`       | `-f`  | Overwrite existing files                          |
| `--dry-run`     |       | Show what would be created without creating       |

**Examples**

```bash
cd my-repoman-project
repoman generator add mycommand
repoman generator add mycommand --project-dir /path/to/project --dry-run
repoman generator add graphrag --kind graphrag
```

### extensions sync

Sync Copier-managed extension instances in a repoman-generated project.

```bash
repoman extensions sync PROJECT_DIR [OPTIONS]
```

**Options**

| Option       | Short | Description                               |
| ------------ | ----- | ----------------------------------------- |
| `--type`     |       | Sync only a specific extension type       |
| `--name`     |       | Sync only a specific extension name       |
| `--force`    | `-f`  | Force overwrite without asking            |
| `--dry-run`  |       | Show what would be synced                 |
| `--conflict` |       | Conflict resolution: `inline` or `rej`    |

**Examples**

```bash
repoman extensions sync ./my-project
repoman extensions sync ./my-project --type command --name report --dry-run
```

## Getting help

```bash
repoman --help
repoman create --help
repoman update --help
repoman config --help
repoman config init --help
repoman config path --help
repoman config validate --help
repoman config show --help
repoman config list-keys --help
repoman hotspots --help
repoman generator add --help
repoman extensions sync --help
```
