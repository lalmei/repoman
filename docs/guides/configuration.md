# Configuration

For **development environment** setup (environment variables, IDE), see [Development configuration](../development/configuration.md).

This page describes **project configuration**: the answers file, non-interactive use, defaults, and where they are stored.

## Configuration = answers

Repoman does not use a separate config file for itself. **Configuration** is the set of **answers** to the template prompts (project name, author, CI, optional FastAPI/RAG, etc.). Those answers drive what gets generated.

## Where configuration is stored

Answers are stored in **`.copier-answers.yml`** in the **generated project** directory (the project you created with `repoman create` or that you update with `repoman update`). That file is created the first time you run `repoman create` and is updated when you run `repoman update` (and when you change answers interactively or via `--answers`).

## Generating an answers file

To get a template answers file that you can edit and reuse (e.g. for non-interactive runs), use:

```bash
repoman config init --output path/to/.copier-answers.yml
```

If you omit `--output`, the file is written as `.copier-answers.yml` in the current directory. Edit the file with your project values, then pass it to `repoman create --answers`. See the [CLI reference](../cli.md#config) for options (`--force`, `--template`).

## Non-interactive use

To run repoman without prompts (e.g. in CI or scripts), pass an answers file:

```bash
repoman create my-project --answers path/to/.copier-answers.yml
repoman update ./my-project --answers ./my-project/.copier-answers.yml
```

The file must contain the same prompt keys and values that the template expects. See [Template prompts](../template-prompts.md) for the full list of prompts and defaults.

## Defaults

Defaults are defined in the template (in `src/repoman/copier.yml` and the template logic). If you do not provide an answer (e.g. you press Enter at a prompt), the template’s default is used. When using `--answers`, any key you omit falls back to the template default.

For the list of prompts and their defaults, see [Template prompts](../template-prompts.md). For how answers are used on update, see [Copier and answers](../concepts/copier-and-answers.md).
