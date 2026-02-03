# Adding a CLI command

This page explains how to add a **new subcommand to a repoman-generated project’s CLI** (the project you created with `repoman create`), not how to add commands to repoman itself. Your generated project must have been created **with** a CLI (you set a CLI name when creating the project).

## Command: repoman generator add

From the **generated project** directory (or by passing `--project-dir`):

```bash
repoman generator add <command_name>
```

Example: `repoman generator add mycommand` creates a new CLI subcommand `mycommand` in your project.

- **`<command_name>`** must be a valid Python identifier (e.g. `mycommand`, `my_command`).
- Repoman uses the **command template** (under `src/repoman/extentions/command_template/` in the repoman repo) to generate files in your project.

## What gets created

- A **command module** under `src/<your_package>/cli/commands/<command_name>/` (e.g. `__init__.py` and any template files).
- A **test file** under `tests/test_cli/test_<command_name>.py`.

The new subcommand is discovered by your project’s CLI (Typer) so it appears when you run your project’s entry point (e.g. `uv run my-app mycommand`).

## Options

| Option                | Description                                                                                               |
| --------------------- | --------------------------------------------------------------------------------------------------------- |
| `--project-dir`, `-d` | Project directory (default: current directory). Use this if you are not already in the generated project. |
| `--answers`, `-a`     | Path to the project’s `.copier-answers.yml` (so repoman can resolve the package name and paths).          |
| `--force`, `-f`       | Overwrite existing files if the command or test file already exists.                                      |
| `--dry-run`           | Show what would be created without writing files.                                                         |

## Example

```bash
cd my-repoman-generated-project
repoman generator add report --dry-run   # preview
repoman generator add report             # create
```

For more on the template and the command template location, see [The template — Adding new CLI commands](../template.md). For all repoman CLI options, see the [CLI reference](../cli.md).
