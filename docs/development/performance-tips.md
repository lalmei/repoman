# Performance Tips

## Fast Development Workflow

```bash
# Run only fast tests during development
make test-fast

# Run specific test categories
make test-unit

# Use parallel test execution
uv run pytest -n auto tests/
```

## Efficient Testing

- Use appropriate fixture scopes (module/session for expensive setup)
- Mock external dependencies
- Keep unit tests fast (under 1 second each)
- Use `tmp_path` fixture for file operations
