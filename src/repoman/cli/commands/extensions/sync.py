"""Sync Copier-managed extension instances in a repoman-generated project."""

from pathlib import Path

from typer import Argument, Exit, Option, Typer

from repoman.cli.messages import (
    dry_run_update,
    error_panel,
    format_next_steps,
    invalid_conflict_mode,
    project_dir_not_found,
)
from repoman.copier import ExtensionLifecycleError, sync_extensions
from repoman.utils.logging import get_logger_console

app = Typer(
    add_completion=True,
    help="""Sync extension instances to latest bundled templates.

Examples:

    repoman extensions sync ./my-project
    repoman extensions sync ./my-project --dry-run
    repoman extensions sync ./my-project --type command --name my_cmd
""",
)


@app.callback(invoke_without_command=True)
def sync(
    project_dir: str = Argument(..., help="Path to the project directory"),
    extension_type: str | None = Option(None, "--type", help="Only sync this extension type"),
    name: str | None = Option(None, "--name", help="Only sync this extension name"),
    force: bool = Option(False, "--force", "-f", help="Force overwrite without asking"),
    dry_run: bool = Option(False, "--dry-run", help="Show what would be synced without making changes"),
    conflict: str = Option("inline", "--conflict", help="Conflict resolution mode: 'inline' or 'rej'"),
) -> None:
    """Sync extensions in the given project (see command help for examples)."""
    _logger, console = get_logger_console()

    if conflict not in ["inline", "rej"]:
        console.print(error_panel(invalid_conflict_mode(conflict), console=console))
        raise Exit(1) from None

    project_dir_obj = Path(project_dir).resolve()
    if not project_dir_obj.exists():
        console.print(error_panel(project_dir_not_found(project_dir_obj), console=console))
        raise Exit(1) from None

    try:
        result = sync_extensions(
            project_dir=project_dir_obj,
            force=force,
            conflict=conflict,
            dry_run=dry_run,
            extension_type=extension_type,
            extension_name=name,
        )
    except ExtensionLifecycleError as e:
        console.print(error_panel(str(e), console=console))
        raise Exit(1) from e

    if dry_run:
        next_steps = [
            "Review extension sync options",
            "Run without --dry-run to apply updates",
        ]
        steps_text = format_next_steps(next_steps, console=console)
        options = {
            "project_dir": str(project_dir_obj),
            "extension_count": len(result.synced),
            "options": result.dry_run_options,
        }
        console.print(
            dry_run_update(
                project_dir=project_dir_obj,
                answers_path=project_dir_obj / ".repoman" / "extensions.yml",
                template_path=None,
                vcs_ref=None,
                copier_options_serializable=options,
                next_steps_text=steps_text,
                _console=console,
            )
        )
        return

    if not result.synced:
        console.print("No active extensions found to sync.")
        return

    synced_ids = ", ".join(instance.id for instance in result.synced)
    console.print(f"Synced extensions: {synced_ids}")
