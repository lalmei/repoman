# Creating a project

This guide walks you through running `repoman create`, answering prompts, and what to do next.

## Basic usage

```bash
repoman create <project_name>
```

Or with uv from the repoman repo: `uv run repoman create <project_name>`.

You will be prompted for project name, description, author, repository and copyright details, Python package and CLI names, CI system, and optional features (FastAPI, RAG, notebooks, dataset). See [Template prompts](../template-prompts.md) for the full list. You can press Enter to accept defaults.

## Options

| Option             | Description                                                                                              |
| ------------------ | -------------------------------------------------------------------------------------------------------- |
| `--output`, `-o`   | Output directory (default: current directory). The project folder will be created here.                  |
| `--answers`, `-a`  | Path to an answers file for **non-interactive** use. Copier will use these answers instead of prompting. |
| `--force`, `-f`    | Overwrite existing files if the target directory or files already exist.                                 |
| `--dry-run`        | Show what would be created without writing files.                                                        |
| `--template`, `-t` | Path to a custom template (default: repoman’s bundled main template).                                    |

## Non-interactive use

To create a project without prompts (e.g. in CI or scripts):

1. Create or reuse a `.copier-answers.yml` (or similar) with the same keys as the template prompts.
2. Run:

   ```bash
   repoman create my-project --answers path/to/answers.yml
   ```

Defaults are defined in the template; your answers file overrides them.

## After creation

The template runs `git init` after generating files, so the project already has a `.git` directory.

1. **Enter the project:** `cd my-project`
2. **Install dependencies:** `uv sync` (or `pip install -e .`)
3. **Run tests:** `make test`
4. **Open in your IDE** and start coding. Use `make check` for lint/format/type checks and `make docs-serve` to preview the docs.

For the layout and options of the generated project, see [Generated project](../concepts/generated-project.md) and [Template structure](../template-structure.md). For all subcommands and options, see the [CLI reference](../cli.md).
