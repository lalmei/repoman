# Package Management

## Adding Dependencies

```bash
# Add runtime dependency
uv add requests

# Add development dependency
uv add --dev pytest-cov

# Add dependency with specific version
uv add "requests>=2.25.0"

# Add dependency with extras
uv add "requests[security]"
```

## Managing Dependencies

```bash
# Update all dependencies
uv lock --upgrade

# Update specific dependency
uv add --upgrade requests

# Remove dependency
uv remove requests

# Show dependency tree
uv tree
```
