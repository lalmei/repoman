"""Ingest subcommand: load documents into the RAG index."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typer import Argument, Option, Typer

from ....utils.theme.theme import set_theme
from . import _get_rag_service

app = Typer(
    add_completion=True,
    invoke_without_command=True,
    no_args_is_help=True,
    help="Ingest documents into the RAG index.",
)


@app.callback(invoke_without_command=True)
def ingest(
    path: str = Argument(..., help="Path to file or directory to ingest"),
    corpus_id: str = Option("default", "--corpus-id", "-c", help="Corpus id"),
    theme: str = Option("dark", "--theme", help="Theme: light or dark"),
) -> None:
    """Ingest a document from path into the RAG index."""
    console = Console(theme=set_theme(theme))
    try:
        service = _get_rag_service()
        result = service.ingest(path=path, corpus_id=corpus_id)
        msg = Text(
            f"Ingested {result.chunks_ingested} chunks from {result.source} (corpus: {result.corpus_id})",
            style="green",
        )
        console.print(Panel(msg, title="Success", border_style="green"))
    except FileNotFoundError as e:
        console.print(
            Panel(Text(str(e), style="red"), title="Error", border_style="red")
        )
        raise SystemExit(1) from e
    except Exception as e:
        console.print(
            Panel(Text(str(e), style="red"), title="Error", border_style="red")
        )
        raise SystemExit(1) from e
