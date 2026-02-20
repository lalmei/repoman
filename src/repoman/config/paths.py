"""OS-specific config path resolution for repoman."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def get_os_config_path(app_name: str) -> Path:
    """Return the standard OS-specific config file path.

    Linux uses $XDG_CONFIG_HOME (default ~/.config). macOS uses
    ~/Library/Application Support (no env var). Windows uses %APPDATA%
    (fallback: ~/AppData/Roaming).

    Args:
        app_name: Application name (e.g. "repoman").

    Returns:
        Path to config.json in the app's config directory.
    """
    home = Path.home()
    system = platform.system()

    match system:
        case "Windows":
            base = Path(os.environ.get("APPDATA", str(home / "AppData" / "Roaming")))
        case "Darwin":  # macOS
            base = home / "Library" / "Application Support"
        case "Linux":
            base = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))
        case _:
            # Fallback to XDG-like config for unknown OS
            base = Path(os.environ.get("XDG_CONFIG_HOME", str(home / ".config")))

    return base / app_name / "config.json"
