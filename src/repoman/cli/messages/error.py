"""CLI error message panels."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from repoman.cli.messages.capability import supports_unicode_markdown


def error_panel(message: str, console: Console | None = None) -> Panel:
    """Build a red Panel with title "Error" (optionally with Unicode when supported).

    Parameters
    ----------
    message : str
        The error message body.
    console : Console | None
        Rich Console; when supported, title may use Unicode (e.g. ⚠) and body
        may be rendered as Markdown.

    Returns:
    -------
    Panel
        A red-bordered Panel suitable for console.print().
    """
    use_unicode = supports_unicode_markdown(console)
    title = "⚠ Error" if use_unicode else "Error"
    if use_unicode:
        body = Markdown(message)
    else:
        body = Text(message, style="red")
    return Panel(body, title=title, border_style="red")
