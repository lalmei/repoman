"""Jinja2 extensions for repoman template rendering."""

from __future__ import annotations

import re
import subprocess
import unicodedata
from datetime import datetime, timezone

from jinja2 import Environment
from jinja2.ext import Extension


def git_user_name(default: str) -> str:
    """Get git user name from git config, falling back to default.

    Args:
        default: Default value to return if git config is not set

    Returns:
        Git user name or default value
    """
    return subprocess.getoutput("git config user.name").strip() or default  # noqa: S605, S607 - Safe: git config is a trusted command


def git_user_email(default: str) -> str:
    """Get git user email from git config, falling back to default.

    Args:
        default: Default value to return if git config is not set

    Returns:
        Git user email or default value
    """
    return subprocess.getoutput("git config user.email").strip() or default  # noqa: S605, S607 - Safe: git config is a trusted command


def slugify(value: str, separator: str = "-") -> str:
    """Convert a string to a URL-friendly slug.

    Args:
        value: String to slugify
        separator: Character to use as separator (default: "-")

    Returns:
        Slugified string
    """
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-_\s]+", separator, value).strip("-_")


class GitExtension(Extension):
    """Jinja2 extension that adds git-related filters."""

    def __init__(self, environment: Environment) -> None:
        """Initialize the Git extension with the Jinja2 environment.

        Args:
            environment: Jinja2 environment to register filters with
        """
        super().__init__(environment)
        environment.filters["git_user_name"] = git_user_name
        environment.filters["git_user_email"] = git_user_email


class SlugifyExtension(Extension):
    """Jinja2 extension that adds slugify filter."""

    def __init__(self, environment: Environment) -> None:
        """Initialize the Slugify extension with the Jinja2 environment.

        Args:
            environment: Jinja2 environment to register filters with
        """
        super().__init__(environment)
        environment.filters["slugify"] = slugify


class CurrentYearExtension(Extension):
    """Jinja2 extension that adds current_year global variable."""

    def __init__(self, environment: Environment) -> None:
        """Initialize the CurrentYear extension with the Jinja2 environment.

        Args:
            environment: Jinja2 environment to register globals with
        """
        super().__init__(environment)
        environment.globals["current_year"] = datetime.now(timezone.utc).date().year
