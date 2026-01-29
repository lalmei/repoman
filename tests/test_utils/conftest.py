"""Test configuration for utility modules."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from rich.console import Console


@pytest.fixture(scope="module")
def mock_colors() -> Path:
    """Provide mock colors object for theme testing.

    **Scope**: module - shared across test classes in the module for performance
    **Returns**: MockColors instance with all required color attributes
    **Usage**: Use in theme-related tests that need color objects

    Example:
        def test_theme_creation(mock_colors: Any) -> None:
            theme = _create_theme(mock_colors)
            assert isinstance(theme, Theme)
    """

    class MockColors:
        def __init__(self):
            self.rosewater = type("Color", (), {"hex": "#f5e0dc"})()
            self.flamingo = type("Color", (), {"hex": "#f2cdcd"})()
            self.pink = type("Color", (), {"hex": "#f5c2e7"})()
            self.mauve = type("Color", (), {"hex": "#cba6f7"})()
            self.red = type("Color", (), {"hex": "#f38ba8"})()
            self.maroon = type("Color", (), {"hex": "#eba0ac"})()
            self.peach = type("Color", (), {"hex": "#fab387"})()
            self.yellow = type("Color", (), {"hex": "#f9e2af"})()
            self.green = type("Color", (), {"hex": "#a6e3a1"})()
            self.teal = type("Color", (), {"hex": "#94e2d5"})()
            self.sky = type("Color", (), {"hex": "#89dceb"})()
            self.sapphire = type("Color", (), {"hex": "#74c7ec"})()
            self.blue = type("Color", (), {"hex": "#89b4fa"})()
            self.lavender = type("Color", (), {"hex": "#b4befe"})()
            self.text = type("Color", (), {"hex": "#cdd6f4"})()
            self.subtext1 = type("Color", (), {"hex": "#bac2de"})()
            self.subtext0 = type("Color", (), {"hex": "#a6adc8"})()
            self.overlay2 = type("Color", (), {"hex": "#9399b2"})()
            self.overlay1 = type("Color", (), {"hex": "#7f849c"})()
            self.overlay0 = type("Color", (), {"hex": "#6c7086"})()
            self.surface2 = type("Color", (), {"hex": "#585b70"})()
            self.surface1 = type("Color", (), {"hex": "#45475a"})()
            self.surface0 = type("Color", (), {"hex": "#313244"})()
            self.base = type("Color", (), {"hex": "#1e1e2e"})()
            self.mantle = type("Color", (), {"hex": "#181825"})()
            self.crust = type("Color", (), {"hex": "#11111b"})()

    return MockColors()


@pytest.fixture(scope="module")
def test_console() -> None:
    """Provide a test console for logging tests.

    **Scope**: module - shared across test classes in the module for performance
    **Returns**: Rich Console instance for testing
    **Usage**: Use in logging tests that need a console object

    Example:
        def test_logging_with_console(test_console: Any) -> None:
            logger, console = get_logger_console("test", console=test_console)
            assert console is test_console
    """
    return Console()


@pytest.fixture
def temp_log_dir() -> Path:
    """Provide a temporary directory for log file testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config() -> Any:
    """Provide a mock config object for testing."""
    config = Mock()
    config.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    return config
