# Potential roadmap

This page outlines possible future directions for repoman and its main template. These are **not commitments**; priorities and scope may change. Contributors are welcome to open issues or pull requests to suggest or implement items.

## Purpose

The roadmap is indicative. It helps align ideas and contributions; it does not guarantee any particular feature or timeline.

## Template and generator

- **More CI backends:** Support for additional CI systems or workflow variants (e.g. more Azure/GitLab options).
- **Optional features:** Clearer or more granular toggles (e.g. optional CLI, optional FastAPI) so projects can start minimal and add only what they need.
- **License and copyright:** More license options or easier customization of copyright text in generated files.
- **Template variants:** Consider a “minimal” vs “full” variant (e.g. library-only vs app + CLI + FastAPI) to reduce generated surface area when not needed.

## CLI and UX

- **Additional repoman subcommands:** For example, list available templates, validate answers file, or show diff before update.
- **Better defaults or prompts:** Smarter defaults (e.g. from Git or repo URL), clearer prompt text, or optional non-interactive defaults for CI.

## Testing and quality

- **Higher instantiated-template coverage:** Improve test coverage of the **generated** project (the instantiated template). See [Instantiated template coverage plan](development/instantiated-template-coverage-plan.md) for the current plan and status.
- **More generated tests:** Additional or improved generated tests for FastAPI/app (e.g. ASGI, health endpoints, error handling).

## Documentation and DX

- **More in-template docs:** Richer generated docs (e.g. usage examples, API overview) that are tailored to the chosen options.
- **“What changed” on update:** After `repoman update`, summarize or list which files were updated and how, to make upgrades easier to review.
- **Migration notes:** Document breaking or notable changes between template versions so users can migrate safely.

---

If you have ideas or want to work on any of these, open an issue or start a discussion in the repository.
