import os
from datetime import datetime
from logging import INFO, Formatter, Logger, getLogger
from logging.handlers import RotatingFileHandler
from typing import cast
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from {{python_package_import_name}}.config import Config
from {{python_package_import_name}}.utils.theme.theme import set_theme


def _set_up_logger(
    name: str = "{{python_package_import_name}}",
    console: Console | None = None,
    log_file: str | None = None,
    log_level: int | None = None,
    use_rotating_file_handler: bool = False,
    log_file_path: Path | None = None,
) -> Logger:
    
    
    if log_level is None:
        log_level = int(os.getenv("_{{project_name}}_LOG_LEVEL", DEBUG))

    module_logger = getLogger(name)

    if len(module_logger.handlers) > 0:
        for handler in module_logger.handlers:
            if handler.get_name() == "rich":
                return module_logger

    if not console:
        console = Console(theme=set_theme("dark"))

    rich_handler = RichHandler(rich_tracebacks=True, console=console)

    rich_handler.set_name("rich")
    module_logger.addHandler(rich_handler)

    if use_rotating_file_handler:
        if log_file is None:
            current_date = datetime.now().strftime("%Y_%m_%d")
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        module_logger = _attach_rotating_file_handler(
            module_logger,
            log_file=log_file_path,
        )

    module_logger.setLevel(level=log_level)

    return module_logger


def _attach_rotating_file_handler(
    logger: Logger,
    log_file: str,
    maximum_log_file_size_mb: int = 10,
    maximum_log_file_time_days: int = 3,
) -> Logger:
    """Attach a rotating file handler to the logger."""
    handler = RotatingFileHandler(
        log_file,
        maxBytes=maximum_log_file_size_mb * 1024 * 1024,
        backupCount=maximum_log_file_time_days,
    )
    handler.setFormatter(Formatter(Config().log_format))
    handler.set_name("rotating_file_handler")
    logger.addHandler(handler)
    return logger


def get_logger_console(
    name: str = "{{python_package_import_name}}",
    console: Console | None = None,
    log_level: int | None = None,
) -> tuple[Logger, Console]:
    """Args:
        name (str, optional): _description_. Defaults to "{{python_package_import_name}}".
        console (Console | None, optional): _description_. Defaults to None.
        log_level (int, optional): _description_. Defaults to INFO.

    Returns:
        tuple[Logger, Console]: _description_
    """

    if log_level is None:
        log_level = int(os.getenv("_{{project_name}}_LOG_LEVEL", INFO))
    root_logger = _set_up_logger(
        use_rotating_file_handler=True,
        log_level=log_level,
    )

    if name != "{{python_package_import_name}}":
        logger = getLogger(name)
        logger.handlers = root_logger.handlers
        logger.setLevel(level=root_logger.level)
        logger.propagate = False
    else:
        logger = root_logger
        if log_level != root_logger.level:
            logger.warning(f"Changing log level to {log_level}")
            logger.setLevel(level=log_level)

    if len(root_logger.handlers) > 0:
        if root_logger.handlers[0].get_name() == "rich":
            handler: RichHandler = cast("RichHandler", logger.handlers[0])
            # use console from handler
            console = handler.console
            return logger, console

    return logger, console
