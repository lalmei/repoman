# Repoman

A Python project generator and repository management tool.

## Quick Start

```bash
# Install dependencies
uv sync

# Run tests
make test

# Generate a new project
uv run python -m repoman create my-new-project
```

## Documentation

- **Development Guide**: [docs/development/README.md](docs/development/README.md)
- **Testing Guide**: [docs/development/testing.md](docs/development/testing.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Features

- **Project Generation**: Create new Python projects from templates
- **Template Management**: Customize and manage project templates
- **CLI Interface**: Easy-to-use command-line interface
- **Rich Output**: Beautiful terminal output with themes

## Development

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
├── config/                # Configuration files
└── deployment/            # Deployment configurations
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
