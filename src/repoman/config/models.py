"""Configuration model for repoman."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from repoman.utils.paths import get_os_config_path


class Config(BaseSettings):
    """Configuration model for repoman (log format, etc.). Used by the main CLI callback for logging and options."""

    model_config = SettingsConfigDict(
        env_prefix="REPOMAN_",
        extra="ignore",
    )

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    _load_path: ClassVar[Path | None] = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customise settings sources to support dynamic JSON file loading."""
        sources: list[PydanticBaseSettingsSource] = [
            init_settings,
            env_settings,
        ]
        if cls._load_path is not None:
            sources.append(JsonConfigSettingsSource(settings_cls, json_file=cls._load_path))
        sources.extend([dotenv_settings, file_secret_settings])
        return tuple(sources)

    @classmethod
    def load(cls, custom_path: Path | None = None) -> Config:
        """Load config from explicit path, REPOMAN_CONFIG_PATH env, or OS default.

        Priority: custom_path > REPOMAN_CONFIG_PATH > get_os_config_path("repoman").
        Creates the config directory if it does not exist.

        Args:
            custom_path: Explicit path to config.json. Overrides env and OS default.

        Returns:
            Config instance.
        """
        env_override = os.environ.get("REPOMAN_CONFIG_PATH")
        file_path = custom_path or (Path(env_override) if env_override else get_os_config_path("repoman"))
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cls._load_path = file_path
            return cls()
        finally:
            cls._load_path = None


def get_config_file_path(custom_path: Path | None = None) -> Path:
    """Resolve the config file path (same priority as Config.load).

    Priority: custom_path > REPOMAN_CONFIG_PATH > get_os_config_path("repoman").
    Does not create directories or load the file.

    Args:
        custom_path: Explicit path to config.json. Overrides env and OS default.

    Returns:
        Resolved path to config.json.
    """
    env_override = os.environ.get("REPOMAN_CONFIG_PATH")
    file_path = custom_path or (Path(env_override) if env_override else get_os_config_path("repoman"))
    return Path(file_path)


def get_project_config_path(project_dir: Path) -> Path:
    """Return the project-level config file path.

    Convention: project_dir/.repoman/config.json. Does not create directories
    or verify the file exists.

    Args:
        project_dir: Project root directory.

    Returns:
        Path to .repoman/config.json inside the project.
    """
    return Path(project_dir) / ".repoman" / "config.json"


def _load_json_if_exists(path: Path) -> dict:
    """Load JSON from path if file exists, else return empty dict."""
    if not path.exists() or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively. Override values take precedence."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_hierarchical(
    project_dir: Path | None = None,
    custom_path: Path | None = None,
) -> Config:
    """Load config with global and optional project-level overrides.

    Load order: global config (custom_path or REPOMAN_CONFIG_PATH or OS default)
    first, then project-level .repoman/config.json if project_dir is given and
    the file exists. Project values override global for overlapping keys.

    Args:
        project_dir: Project root. If set and .repoman/config.json exists, its
            values override global config.
        custom_path: Explicit path to global config.json. Overrides env and
            OS default for the global layer only.

    Returns:
        Merged Config instance.
    """
    global_path = get_config_file_path(custom_path)
    global_data = _load_json_if_exists(global_path)

    if project_dir is not None:
        project_path = get_project_config_path(project_dir)
        project_data = _load_json_if_exists(project_path)
        if project_data:
            global_data = _deep_merge(global_data, project_data)

    return Config.model_validate(global_data)
