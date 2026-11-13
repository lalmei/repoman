# Personal site

Use Node.js 22.23.4 or newer. Run `npm ci` and `npm run dev` for local development.
Run `npm run check` and `npm run build` before publishing the static files in
`dist/`.

Edit your name, bio, and links in `src/content/profile.json`. Add one Markdown
file per project in `src/content/projects/`, with a `title` and optional
`url` in the front matter. You can delete the example project. Put your images
in `public/images/` and reference them from Markdown, for example
`![Project screenshot](/images/project.png)`. Use `src/styles/custom.css`
for CSS overrides.

## Updating the scaffold

Initialize Git and commit the generated site before customizing it. Commit
your edits before updating and work on a review branch. Keep
`.copier-answers.yml` in version control.

Run `repoman update . --plan` to check readiness and `repoman update .` to
apply the update. Review the diff and resolve any conflict markers before
committing. Run `npm ci`, `npm run check`, and `npm run build`, then preview
the built site with `npm run preview`.

The profile and custom CSS are preserved when they exist. Project Markdown and
images are yours to edit, add, or remove. Shared layouts, dependencies, and CI
can change during template upgrades. Your edits to those files may need a
manual merge if they overlap a template change.
