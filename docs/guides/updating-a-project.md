# Updating a project

This page explains when and how to run `repoman update`, how answers are reused, and how to handle conflicts.

## When to update

Run `repoman update` when:

- The repoman template has changed (e.g. you pulled template fixes or new features in the repoman repo).
- You want to re-apply the template to an existing project that was created with repoman, so it gets the latest layout, CI, or optional features (where the template allows).

Start with a clean Git checkout and commit the generated project before its first update. Updates reuse saved answers, use defaults for new questions, and let Copier merge downstream edits. Review the diff before committing. Copy tasks are skipped during upgrades. Trusted template migrations can still run.

## Basic usage

```bash
repoman update <project_dir>
```

Example: from the repo root, `repoman update ./my-project`. Repoman (and Copier) read `.copier-answers.yml` from `<project_dir>` and re-run the template against that directory.

Before updating, you can inspect the repository or preview the update plan:

```bash
repoman inspect --path ./my-project
repoman update ./my-project --plan
```

## How answers are reused

- The **answers file** is by default `<project_dir>/.copier-answers.yml`. It was created when you first ran `repoman create` (or a previous update).
- Copier uses these answers to render the template again. Copier merges changes from the new template with committed downstream edits.
- You can override the answers file with `--answers path/to/answers.yml`.

## Options

| Option             | Description                                                                          |
| ------------------ | ------------------------------------------------------------------------------------ |
| `--template`, `-t` | Override the template path (normally read from the project’s `.copier-answers.yml`). |
| `--vcs-ref`, `-r`  | Git ref or tag to use for the template (e.g. a specific version).                    |
| `--answers`, `-a`  | Path to `.copier-answers.yml` (default: `<project_dir>/.copier-answers.yml`).        |
| `--force`, `-f`    | Compatibility flag. Updates already use saved answers and defaults.                                                            |
| `--trust`          | Allow custom templates to load extensions and run migrations. |
| `--plan`           | Show an update plan and blockers without writing files.                             |
| `--dry-run`        | Show what would be updated without writing files.                                    |
| `--repair`         | Repair Copier metadata in the answers file instead of running update.                |
| `--commit`         | Commit value to write when using `--repair`.                                         |
| `--conflict`       | Conflict resolution: `inline` or `rej` (default: inline).                            |
| `--skip-extensions`| Omit extension follow-up from the base update plan.                |

## Handling conflicts

If you have edited generated files and the template has changed, Copier may report conflicts:

- **`inline`** — Conflict markers are written in the file; resolve them by hand.
- **`rej`** — Reject files (e.g. `.rej` files) are written; apply or discard changes as needed.

Use `--plan` to see blockers and intended update inputs, or `--dry-run` to preview Copier options without applying changes. For more help, see [Troubleshooting](../reference/troubleshooting.md) and the [CLI reference](../cli.md).

## Copier update metadata

`repoman update` uses Copier’s **update** path (`Worker.run_update()`). Copier must load the **previous** template identity from your answers file so it can diff against the template version you are updating to. At minimum it needs **`_src_path`** (where the template came from) and **`_commit`** (the Git revision that was used last time), stored in `.copier-answers.yml`.

Official release wheels record the upstream repository and the exact template commit for generated Python projects. To test a local template revision, pass the Git checkout root to `repoman create --template` with `--vcs-ref` and `--trust`. Ordinary local builds of the wheel can scaffold projects offline; they do not embed release provenance.

If **`_commit` is missing** (or empty) while **`_src_path` is set**, Copier cannot resolve the old template and you will see an error such as: *Cannot update because cannot obtain old template references from `.copier-answers.yml`.* The same requirement applies whether you use `repoman update` or Copier’s CLI.

Common ways this happens:

- The answers file was **hand-edited** and `_commit` was removed or left blank.
- An older release or canary omitted the source revision. Restore the verified original revision before attempting a merge.
- The file was **not produced by a full Copier copy** (e.g. partially checked in).

### Repairing a missing `_commit`

You can repair the metadata directly through repoman:

```bash
repoman update ./my-project --repair --commit v1.2.3
repoman update ./my-project --repair --template /path/to/repoman --commit v1.2.3
```

`--repair` updates only the answers file. It does **not** run Copier or sync extensions.

1. Identify the **template** your project points to: the `_src_path` value in `.copier-answers.yml` (or use `repoman update --template /path/to/checkout` to aim at a local clone while fixing things).
2. Use a checkout whose **Git root** matches how Copier tracks the template. For repoman itself, the template is configured under `src/repoman/` in the repo (see [The template](../template.md)); `_src_path` should usually refer to a **repository root** with the top-level `copier.yml`, not only a lone subdirectory such as `main_template/`, so Git metadata and tags resolve correctly.
3. From that repository root, run:

   ```bash
   git describe --tags --always
   ```

4. Add the output to `.copier-answers.yml` as **`_commit`**, for example:

   ```yaml
   _commit: v1.2.3-4-gabcdef
   ```

5. Commit the repaired answers, then run `repoman update`. Pass `--trust` if the verified custom template needs Copier extensions or migrations.

You can use **`repoman config validate`** to be warned when `_src_path` is set but `_commit` is missing; use **`--fail-missing-copier-commit`** if you want validation to fail in that case.

## Extension sync

Commit the base template update before syncing command extensions. Copier requires a clean checkout for each merge.

```bash
repoman extensions sync --vcs-ref v1.2.3 ./my-project
repoman extensions sync --name my_command --vcs-ref v1.2.3 ./my-project
```

If several extensions are active, select and review each one individually. New command extensions generated from a versioned template record their own source and revision. Older extensions created without a revision need a verified baseline before they can be merged.
