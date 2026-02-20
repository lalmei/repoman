"""Configuration model for repoman."""

from __future__ import annotations

import os
from pathlib import Path
from typing import ClassVar

from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from repoman.config.paths import get_os_config_path


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
