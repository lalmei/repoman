# Documentation

The project uses **MkDocs** with the **Material theme** for documentation. This provides a modern, responsive documentation site with excellent features like search, navigation, and code highlighting.

## Documentation Structure

:fontawesome-solid-folder: **docs/**

- :fontawesome-solid-file-lines: `index.md` — Homepage
- :fontawesome-solid-file-lines: `cli.md` — CLI reference (subcommands and options)
- :fontawesome-solid-file-lines: `make-commands.md` — Make targets reference
- :fontawesome-solid-file-lines: `template.md` — The template (instantiated layout)
- :fontawesome-solid-file-lines: `roadmap.md` — Potential roadmap
- :fontawesome-solid-folder: **development/** — Development documentation
  - :fontawesome-solid-file-lines: `README.md` — This development guide
  - :fontawesome-solid-file-lines: `testing.md` — Comprehensive testing guide
  - :fontawesome-solid-file-lines: `instantiated-template-coverage-plan.md`
- :fontawesome-brands-css3-alt: **css/** — Custom CSS (material.css, mkdocstrings.css)
- :fontawesome-brands-js: **js/** — Custom JavaScript (e.g. feedback.js)
- :fontawesome-solid-folder: **.overrides/** — Material theme overrides (partials, etc.)

MkDocs is configured in `config/mkdocs.yml` (in the repo root). The `docs_dir` points to this `docs/` folder.

## MkDocs Configuration

The documentation is configured in `config/mkdocs.yml` with the following features:

- **Material theme** with dark/light mode support
- **Search functionality** with highlighting
- **Navigation tabs** and sections
- **Code annotation** and copying
- **Admonitions** and callouts
- **Emoji support** with Twemoji
- **Task lists** with custom checkboxes
- **API documentation** with mkdocstrings
- **Coverage reports** integration
- **Git revision dates** (when deployed)

## Building Documentation

```bash
# Install documentation dependencies
uv sync --group docs

# Build documentation
make docs

# Serve documentation locally (with live reload)
make docs-serve

# Check documentation for issues
make docs-check
```

## Documentation Features

### Material Theme Features

- **Dark/Light Mode**: Automatic theme switching based on system preference
- **Search**: Full-text search with highlighting and suggestions
- **Navigation**: Sticky navigation with tabs and sections
- **Code Blocks**: Syntax highlighting with copy functionality
- **Admonitions**: Beautiful callout boxes for notes, warnings, etc.

### Writing Documentation

Use Material theme features in your markdown:

````markdown
# Admonitions

!!! note "Note"
This is a note with a title.

!!! warning "Warning"
This is a warning.

!!! tip "Tip"
This is a tip.

# Code blocks with annotations

```python
def hello_world():
    print("Hello, World!")  # (1)
```
````

1. This is an annotation

# Task lists

- [x] Completed task
- [ ] Pending task

# Emoji support

:smile: :rocket: :warning:

# Tabs

=== "Tab 1"
Content for tab 1

=== "Tab 2"
Content for tab 2

````

### API Documentation

The project uses `mkdocstrings` for automatic API documentation:

- **Python API**: Automatically generated from docstrings
- **Cross-references**: Links between documentation sections
- **Type annotations**: Displayed in function signatures
- **Source code**: Links to GitHub repository

## Documentation Workflow

1. **Write documentation** in markdown files
2. **Add docstrings** to Python code for API docs
3. **Test locally**: `make docs-serve`
4. **Build for deployment**: `make docs`
5. **Check for issues**: `make docs-check`

## Documentation Best Practices

### Writing Style

- Use clear, concise language
- Include code examples
- Add screenshots for UI features
- Keep documentation up to date with code changes

### Structure

- Organize content logically
- Use consistent headings
- Include table of contents for long pages
- Cross-reference related sections

### Code Examples

- Use syntax highlighting
- Include complete, runnable examples
- Add annotations for complex code
- Test all code examples

## Deployment

Documentation is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment process:

1. Builds the documentation site
2. Minifies HTML for production
3. Deploys to `https://lalmei.github.io/repoman`

## Customization

### CSS Customization

Add custom styles in `docs/css/material.css`:

```css
/* Custom styles for the documentation */
.custom-class {
    color: var(--md-primary-fg-color);
}
```

### JavaScript Customization

Add custom functionality in `docs/js/feedback.js`:

```javascript
// Custom JavaScript for the documentation
document.addEventListener("DOMContentLoaded", function () {
  // Your custom code here
});
```

### Theme Overrides

Customize the Material theme in `docs/.overrides/`:

- Override template files
- Add custom components
- Modify theme behavior
````
