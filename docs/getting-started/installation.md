# Installation

This page describes how to install repoman and verify the installation.

## Requirements

- **Python 3.12+**
- **uv** — [Astral’s uv](https://docs.astral.sh/uv/) is the recommended way to run repoman (install with `curl -LsSf https://astral.sh/uv/install.sh | sh` on macOS/Linux, or see the [uv docs](https://docs.astral.sh/uv/) for Windows).

## Install from the repoman repository

If you have cloned the repoman repo:

```bash
cd repoman
uv sync
```

This creates a virtual environment and installs repoman and its dependencies. Use `uv run repoman` to run the CLI (see [Quick start](quickstart.md) and [CLI reference](../cli.md)).

## Install with pip or uv (standalone)

To install repoman as a standalone tool:

```bash
# With pip (after cloning or from a source tree)
pip install -e /path/to/repoman

# Or with uv
uv pip install -e /path/to/repoman
```

You can then run `repoman` from the command line without `uv run`.

## Verify the installation

```bash
# If you use uv run (from repo)
uv run repoman --version

# If repoman is installed (pip / uv pip install)
repoman --version
```

You should see the repoman version. For next steps, see [Quick start](quickstart.md) and the [CLI reference](../cli.md).
