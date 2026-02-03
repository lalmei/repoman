# Updating a project

This page explains when and how to run `repoman update`, how answers are reused, and how to handle conflicts.

## When to update

Run `repoman update` when:

- The repoman template has changed (e.g. you pulled template fixes or new features in the repoman repo).
- You want to re-apply the template to an existing project that was created with repoman, so it gets the latest layout, CI, or optional features (where the template allows).

Updates reuse the project’s stored answers so only changed template output is applied.

## Basic usage

```bash
repoman update <project_dir>
```

Example: from the repo root, `repoman update ./my-project`. Repoman (and Copier) read `.copier-answers.yml` from `<project_dir>` and re-run the template against that directory.

## How answers are reused

- The **answers file** is by default `<project_dir>/.copier-answers.yml`. It was created when you first ran `repoman create` (or a previous update).
- Copier uses these answers to render the template again. Only files that differ from the new template output are updated (unless you use `--force`).
- You can override the answers file with `--answers path/to/answers.yml`.

## Options

| Option             | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `--template`, `-t` | Override the template path (normally read from the project’s `.copier-answers.yml`). |
| `--vcs-ref`, `-r`  | Git ref or tag to use for the template (e.g. a specific version).                    |
| `--answers`, `-a`  | Path to `.copier-answers.yml` (default: `<project_dir>/.copier-answers.yml`).        |
| `--force`, `-f`    | Overwrite without asking.                                                            |
| `--dry-run`        | Show what would be updated without writing files.                                    |
| `--conflict`       | Conflict resolution: `inline` or `rej` (default: inline).                            |

## Handling conflicts

If you have edited generated files and the template has changed, Copier may report conflicts:

- **`inline`** — Conflict markers are written in the file; resolve them by hand.
- **`rej`** — Reject files (e.g. `.rej` files) are written; apply or discard changes as needed.

Use `--dry-run` to see what would be updated before applying. For more help, see [Troubleshooting](../reference/troubleshooting.md) and the [CLI reference](../cli.md).
