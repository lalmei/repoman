"""Jinja extensions available to the C++ Copier template."""

from repoman.extensions import CurrentYearExtension, GitExtension, SlugifyExtension

__all__ = ["CurrentYearExtension", "GitExtension", "SlugifyExtension"]
