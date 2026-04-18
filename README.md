# Repoman

A Python project generator and repository management tool.

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
make test

# Generate a new project
uv run python -m repoman create --project_name my-new-project
```

## Documentation

- **CLI Reference**: [docs/cli.md](docs/cli.md) — subcommands and options
- **Make Commands**: [docs/make-commands.md](docs/make-commands.md) — development targets
- **Template reference**: [docs/template.md](docs/template.md) — what the template is and what it generates
- **Roadmap**: [docs/roadmap.md](docs/roadmap.md) — potential future directions
- **Development Guide**: [docs/development/README.md](docs/development/README.md)
- **Testing Guide**: [docs/development/testing.md](docs/development/testing.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Features

- **Project Generation**: Create new Python projects from templates
- **Template Management**: Customize and manage project templates
- **CLI Interface**: Easy-to-use command-line interface
- **Rich Output**: Beautiful terminal output with themes
- **Compliance Readiness Checks**: Analyze repositories against built-in software governance profiles and produce badge-style reports

## CLI

Repoman provides three main commands:

- **`create`** — Create a new project from the template (`uv run repoman create --project_name my-project`)
- **`update`** — Update an existing project with the latest template
- **`compliance check`** — Evaluate a repo against built-in `soc2-software` and `oss-best-practices` profiles
- **`compliance init`** — Generate a starter `compliance.yml` for manual evidence and waivers
- **`generator add`** — Add a new CLI command to a repoman-generated project

Run `uv run repoman --help` for global options. See [CLI reference](docs/cli.md) for full options and examples.

## Development

Run `make help` for all make targets. Common targets:

- **Testing**: `make test`, `make test-coverage`, `make test-unit`, `make test-cli`, etc.
- **Code quality**: `make format`, `make lint`, `make fix`, `make check`
- **Compliance**: `make compliance-check` to run repoman against this repo's own `compliance.yml` baseline
- **Documentation**: `make docs`, `make docs-serve`

See [Make commands](docs/make-commands.md) for the full list.

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit      # Unit tests only
make test-utils     # Utility tests only
make test-cli       # CLI tests only

# Run with coverage
make test-coverage
```

For detailed testing information, see [docs/development/testing.md](docs/development/testing.md).

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Fix linting issues
make fix
```

## Project Structure

```
repoman/
├── src/repoman/           # Source code
├── tests/                 # Test suite
├── docs/                  # Documentation
│   └── development/       # Development guides
└── config/                # Configuration files
```

(The `deployment/` directory appears in **generated** projects, not in this repo.)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
