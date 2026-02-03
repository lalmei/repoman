# Troubleshooting

This page lists common issues when using repoman (create, update, generator add) and how to resolve or debug them.

## Copier errors

- **“Answers file not found” or missing prompts**  
  Ensure the project has a `.copier-answers.yml` in its root (created when you first ran `repoman create`). If you use `--answers`, point it to a valid file with the expected keys. See [Template prompts](../template-prompts.md) and [Copier and answers](../concepts/copier-and-answers.md).

- **Copier version**  
  Repoman requires a minimum Copier version (see repoman’s `copier.yml`). Upgrade Copier (or the environment that runs repoman) if you see a version error.

- **Template not found**  
  For `repoman create`, the default template is bundled with repoman. For `repoman update`, the template path is usually read from the project’s `.copier-answers.yml`. If you use `--template`, ensure the path is correct and the template is valid.

## Path and output issues

- **Wrong output directory**  
  Use `--output` / `-o` with `repoman create` to choose where the project folder is created. Use `--project-dir` / `-d` with `repoman generator add` to point to the generated project.

- **Permission or path errors**  
  Ensure you have write access to the target directory and that paths are absolute or correct relative to the current working directory.

## Answers file

- **Answers file location**  
  By default it is `<project_dir>/.copier-answers.yml`. Override with `--answers`. For non-interactive runs, pass an answers file that matches the template’s prompt keys.

- **Generating a template**  
  To create a new answers file with all expected keys, run `repoman config init --output path/to/.copier-answers.yml`, then edit the file. See [Configuration](../guides/configuration.md#generating-an-answers-file) and the [CLI reference](../cli.md#config).

- **Answers out of sync**  
  If the template added or renamed prompts, old answers might be incomplete. Run interactively once or merge the new defaults into your answers file.

## Conflict resolution (update)

- When you run `repoman update` and have edited generated files, Copier may report conflicts. Use `--conflict inline` (default) or `--conflict rej` and resolve the conflict markers or reject files. See [Updating a project](../guides/updating-a-project.md).

- Use **`--dry-run`** to see what would be updated without writing: `repoman update ./my-project --dry-run`.

## Debugging

- **Verbose logging** — Run with `--verbose` / `-v` to get DEBUG-level logs and more detail about what repoman and Copier are doing.
- **Debug info** — Run `repoman --debug-info` to print environment and version information useful for bug reports.

For **test-specific** issues (running pytest, fixtures, CI), see [Testing troubleshooting](../development/testing-troubleshooting.md).
