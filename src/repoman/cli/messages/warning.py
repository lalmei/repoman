"""CLI warning message panels."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from repoman.cli.messages.capability import supports_unicode_markdown


def warning_panel(message: str, console: Console | None = None) -> Panel:
    """Build a yellow Panel with title "Warning" (optionally with Unicode when supported).

    Parameters
    ----------
    message : str
        The warning message body.
    console : Console | None
        Rich Console; when supported, title may use Unicode and body
        may be rendered as Markdown.

    Returns:
    -------
    Panel
        A yellow-bordered Panel suitable for console.print().
    """
    use_unicode = supports_unicode_markdown(console)
    title = "⚠ Warning" if use_unicode else "Warning"
    if use_unicode:
        body = Markdown(message)
    else:
        body = Text(message, style="yellow")
    return Panel(body, title=title, border_style="yellow")
