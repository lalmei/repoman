"""Configuration management for repoman."""

from pydantic import BaseModel


class Config(BaseModel):
    """Configuration model for repoman."""

    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
