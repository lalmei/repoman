"""OS-specific config path resolution for repoman."""

from __future__ import annotations

import os
import platform
from pathlib import Path


def get_os_config_path(app_name: str) -> Path:
    """Return the standard OS-specific config file path.

    Linux and macOS use $XDG_CONFIG_HOME/app_name/config.json or
    ~/.config/app_name/config.json. Windows uses %APPDATA%/app_name/config.json
    (fallback: ~/AppData/Roaming/app_name/config.json).

    Args:
        app_name: Application name (e.g. "repoman").

    Returns:
        Path to config.json in the app's config directory.
    """
    home = Path.home()
    system = platform.system()

    match system:
        case "Windows":
            base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
        case "Darwin":  # macOS
            base = Path(os.environ.get(home / ".config", home / "Library" / "Application Support"))
        case "Linux":
            base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        case _:
            # Fallback to XDG-like config for unknown OS
            base = Path(os.environ.get(home / ".config"))

    return base / app_name / "config.json"
