"""repoman is a tool for creating and managing repositories."""

from __future__ import annotations

from repoman._version import debug_info, get_version
from repoman.cli import cli

__all__: list[str] = ["cli", "debug_info", "get_version"]
