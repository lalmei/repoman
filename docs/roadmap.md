# Potential roadmap

This page outlines possible future directions for repoman and its main template. These are **not commitments**; priorities and scope may change. Contributors are welcome to open issues or pull requests to suggest or implement items.

## Purpose

The roadmap is indicative. It helps align ideas and contributions; it does not guarantee any particular feature or timeline.

## Template and generator

- **More CI backends:** Support for additional CI systems or workflow variants (e.g. more Azure/GitLab options).
- **Optional features:** Clearer or more granular toggles (e.g. optional CLI, optional FastAPI) so projects can start minimal and add only what they need.
- **License and copyright:** More license options or easier customization of copyright text in generated files.
- **Template variants:** Consider a “minimal” vs “full” variant (e.g. library-only vs app + CLI + FastAPI) to reduce generated surface area when not needed.

## Configuration

- **Hierarchical config:** Merge global (`~/.config/repoman/config.json`) with project-level config (e.g. `.repoman/config.json`) so project overrides can layer on top of system defaults.
- **`repoman config path` or `repoman config init`:** Subcommand to show the system config file path or create an initial config file with defaults.
- **Full env-overrides-file behavior:** Ensure environment variables (e.g. `REPOMAN_LOG_FORMAT`) properly override values loaded from the JSON config file via pydantic-settings source chain.

## CLI and UX

- **Additional repoman subcommands:** For example, list available templates, validate answers file, or show diff before update.
- **Better defaults or prompts:** Smarter defaults (e.g. from Git or repo URL), clearer prompt text, or optional non-interactive defaults for CI.

## Concrete next issues (inspect-first)

This section turns the roadmap into a short implementation backlog for repoman's
main lifecycle flow. The order is intentional: later items depend on earlier
ones.

### 1. Add `repoman inspect`

**Goal:** Give users a single read-only command that explains whether a
repository is repoman-managed and whether it is safe to update.

**Scope**

- Add a pure logic module that inspects a target repository and returns:
  - whether `.copier-answers.yml` exists
  - template source and commit metadata
  - active feature flags from answers
  - extension manifest summary from `.repoman/extensions.yml`
  - update-readiness warnings (for example, missing `_commit`)
- Add a CLI command under `repoman inspect`.
- Support human-readable and machine-readable output.

**Proposed command shape**

```bash
repoman inspect
repoman inspect --path ./my-project --format table
repoman inspect --path ./my-project --format json
repoman inspect --path ./my-project --no-header
```

**Out of scope**

- Mutating or repairing repository files.
- Running Copier update.
- Computing a full file diff.

**Implementation notes**

- Keep CLI formatting in `repoman.cli`.
- Put repository inspection logic in a pure module so `update` and future
  commands can reuse it.

### 2. Add update preflight / plan mode

**Goal:** Show what `repoman update` is going to do before any files are
written.

**Scope**

- Add a preflight path that reuses `inspect` results before update.
- Summarize:
  - update blockers
  - template source/ref that will be used
  - extension sync operations that would run
  - likely review steps after update
- Keep the first version summary-oriented rather than trying to render a full
  patch.

**Proposed command shape**

```bash
repoman update PROJECT_DIR --plan
repoman update PROJECT_DIR --plan --vcs-ref v1.2.0
repoman update PROJECT_DIR --dry-run
```

**Out of scope**

- A line-by-line diff viewer.
- Automatic migration execution beyond normal Copier update behavior.

**Implementation notes**

- `--plan` should be more explanatory than today's `--dry-run`.
- `--dry-run` can stay as the lower-level "show Copier options / no writes"
  path if needed.

### 3. Add Copier metadata repair workflow

**Goal:** Make broken update metadata recoverable without manual editing of
`.copier-answers.yml`.

**Scope**

- Add a guided repair command for missing or invalid Copier metadata.
- Validate `_src_path` / `_commit` consistency before repair.
- Allow users to provide explicit template path and commit/ref.
- Reuse the same validation rules surfaced by `inspect`.

**Proposed command shape**

```bash
repoman update PROJECT_DIR --repair --template /path/to/repoman --commit v1.2.3
repoman inspect PROJECT_DIR
```

**Out of scope**

- Guessing remote refs over the network.
- Reconstructing arbitrary lost answers outside Copier metadata.

**Implementation notes**

- `inspect` should detect and explain the problem first.
- `update --repair` should be explicit and opt-in because it mutates tracked
  project metadata.

### 4. Add post-create feature overlays

**Goal:** Let users add major capabilities after project creation instead of
forcing all choices into `repoman create`.

**Scope**

- Add a dedicated `features` command group for post-create enablement.
- Start with a small supported set such as:
  - `fastapi`
  - `notebooks`
  - `datasets`
- Ensure answers and extension metadata stay in sync when a feature is added.
- Support dry-run for generated file changes.

**Proposed command shape**

```bash
repoman features list PROJECT_DIR
repoman features enable fastapi PROJECT_DIR
repoman features enable notebooks PROJECT_DIR --dry-run
```

**Out of scope**

- Toggling every Copier prompt after creation.
- Safe removal of large features before a migration strategy exists.

**Implementation notes**

- Prefer extension-style overlays over special-casing `update`.
- Treat the first release as additive only.

### 5. Improve `create` auto-detection

**Goal:** Reduce prompt friction by deriving obvious defaults from local Git
state.

**Scope**

- Infer author name, email, username, repository provider, namespace, and
  repository name from local Git config and remotes when available.
- Keep current prompt keys and answers-file format stable.
- Fall back cleanly when Git data is missing.

**Proposed command shape**

```bash
repoman create --project_name my-project
repoman create --project_name my-project --preset cli
```

**Out of scope**

- Network lookups against GitHub, GitLab, or Azure APIs.
- Changing the template schema only to support auto-detection.

### Suggested implementation order

1. `repoman inspect`
2. `repoman update --plan`
3. `repoman update --repair`
4. `repoman features ...`
5. `repoman create` auto-detection improvements

### Why this order

- `inspect` creates the reusable repository-state model.
- `update --plan` depends on that model and improves the riskiest workflow.
- `update --repair` closes the most painful failure mode discovered by `inspect`.
- Feature overlays should build on the same repository-state and lifecycle
  metadata.
- Create-time auto-detection is valuable, but it is less urgent than making the
  existing lifecycle predictable.

## Testing and quality

- **Higher instantiated-template coverage:** Improve test coverage of the **generated** project (the instantiated template). See [Instantiated template coverage plan](development/instantiated-template-coverage-plan.md) for the current plan and status.
- **More generated tests:** Additional or improved generated tests for FastAPI/app (e.g. ASGI, health endpoints, error handling).

## Documentation and DX

- **More in-template docs:** Richer generated docs (e.g. usage examples, API overview) that are tailored to the chosen options.
- **“What changed” on update:** After `repoman update`, summarize or list which files were updated and how, to make upgrades easier to review.
- **Migration notes:** Document breaking or notable changes between template versions so users can migrate safely.

## Documentation and maintenance (post-review follow-ups)

Potential improvements identified during documentation and project reviews:

- **Positional project name for create:** Consider adding a positional project name to the default `repoman create` command so `repoman create my-project` works without `--project_name` (would require a small CLI change for simpler UX).
- **Rename extentions/ to extensions/:** Consider renaming the `extentions/` directory to `extensions/` with a documented migration plan (update paths, templates, tests, and docs).
- **Keep CLI reference in sync:** When adding new create options or subcommands, update the CLI reference and all create examples across the docs so they stay consistent.

---

If you have ideas or want to work on any of these, open an issue or start a discussion in the repository.
