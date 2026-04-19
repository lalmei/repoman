# Continuous Integration

The project uses GitHub Actions for continuous integration. The CI pipeline:

1. **Runs tests** on multiple Python versions
2. **Checks code quality** (linting, type checking)
3. **Generates coverage reports**
4. **Builds documentation**

## Local CI Simulation

```bash
# Run the equivalent of CI locally
make setup
make check-docs
make check
make test-coverage
```
