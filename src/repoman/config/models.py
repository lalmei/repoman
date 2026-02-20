"""Configuration model for repoman."""

from __future__ import annotations

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration model for repoman (log format, etc.). Used by the main CLI callback for logging and options."""

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
