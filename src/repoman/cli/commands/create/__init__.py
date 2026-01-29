"""Create command for generating repositories from templates.

This module re-exports the copier command as 'create' for better UX.
"""

from repoman.cli.commands.copier import app

__all__ = ["app"]
