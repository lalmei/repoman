"""Tests for theme utilities."""

from typing import Any

import pytest
from rich.theme import Theme

from repoman.utils.theme.terminal_colors import get_rich_color
from repoman.utils.theme.theme import _create_theme, set_theme


class TestThemeCreation:
    """Test theme creation functionality."""

    def test_create_theme_with_valid_colors(self) -> None:
        """Test that _create_theme creates a valid Theme object."""

        # Mock colors object with hex attributes
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

        colors = MockColors()
        theme = _create_theme(colors)

        assert isinstance(theme, Theme)
        assert theme.styles is not None

        # When inherit=True, Rich includes default styles plus our custom ones
        # Our custom styles should be present
        assert "rosewater" in theme.styles
        assert "text" in theme.styles
        assert "base" in theme.styles

        # Check that specific colors are set correctly
        # Rich converts hex strings to Style objects, so we check the color attribute
        assert hasattr(theme.styles["rosewater"], "color")
        assert hasattr(theme.styles["text"], "color")
        assert hasattr(theme.styles["base"], "color")

        # Check that the color values contain our hex strings
        assert "#f5e0dc" in str(theme.styles["rosewater"])
        assert "#cdd6f4" in str(theme.styles["text"])
        assert "#1e1e2e" in str(theme.styles["base"])

    def test_create_theme_inheritance(self) -> None:
        """Test that created theme has inherit=True behavior."""

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

        colors = MockColors()
        theme = _create_theme(colors)

        # When inherit=True, Rich includes default styles plus our custom ones
        # This means the total count will be much higher than just our 25
        assert len(theme.styles) > 25

        # But our custom styles should be present
        assert "rosewater" in theme.styles
        assert "text" in theme.styles
        assert "base" in theme.styles


class TestSetTheme:
    """Test theme setting functionality."""

    def test_set_theme_dark(self) -> None:
        """Test setting dark theme."""
        theme = set_theme("dark")
        assert isinstance(theme, Theme)
        assert theme.styles is not None

    def test_set_theme_light(self) -> None:
        """Test setting light theme."""
        theme = set_theme("light")
        assert isinstance(theme, Theme)
        assert theme.styles is not None

    def test_set_theme_invalid_name(self) -> None:
        """Test that invalid theme names raise ValueError."""
        with pytest.raises(ValueError, match="Unknown theme: invalid"):
            set_theme("invalid")

    def test_set_theme_default_is_dark(self) -> None:
        """Test that default theme is dark."""
        theme_default = set_theme()
        theme_dark = set_theme("dark")

        # Both should be Theme objects
        assert isinstance(theme_default, Theme)
        assert isinstance(theme_dark, Theme)

        # They should be equivalent since default is dark
        assert theme_default.styles == theme_dark.styles

    def test_set_theme_dark_vs_light_different(self) -> None:
        """Test that dark and light themes are different."""
        theme_dark = set_theme("dark")
        theme_light = set_theme("light")

        # Both should be Theme objects
        assert isinstance(theme_dark, Theme)
        assert isinstance(theme_light, Theme)

        # They should have different styles (different color palettes)
        assert theme_dark.styles != theme_light.styles


class TestTerminalColors:
    """Test terminal color mapping functionality."""

    def test_get_rich_color_known_labels(self) -> None:
        """Test that known labels return correct colors."""
        assert get_rich_color("TP") == "green"
        assert get_rich_color("FP") == "maroon"
        assert get_rich_color("FN") == "red"
        assert get_rich_color("TN") == "peach"
        assert get_rich_color("header") == "subtext1"
        assert get_rich_color("border") == "overlay1"

    def test_get_rich_color_unknown_label(self) -> None:
        """Test that unknown labels return default 'text' color."""
        assert get_rich_color("unknown") == "text"
        assert get_rich_color("") == "text"
        assert get_rich_color("CUSTOM_LABEL") == "text"

    def test_get_rich_color_case_sensitive(self) -> None:
        """Test that color mapping is case sensitive."""
        assert get_rich_color("tp") == "text"  # lowercase should return default
        assert get_rich_color("Tp") == "text"  # mixed case should return default
        assert get_rich_color("TP") == "green"  # exact match should work

    def test_get_rich_color_special_characters(self) -> None:
        """Test that special characters in labels are handled correctly."""
        assert get_rich_color("TP_123") == "text"  # alphanumeric with underscore
        assert get_rich_color("TP-123") == "text"  # alphanumeric with hyphen
        assert get_rich_color("TP.123") == "text"  # alphanumeric with dot
        assert get_rich_color("TP 123") == "text"  # alphanumeric with space


class TestThemeErrorHandling:
    """Test error handling and edge cases in theme utilities."""

    def test_create_theme_with_invalid_colors(self) -> None:
        """Test theme creation with invalid color objects."""
        # Test with None colors
        with pytest.raises(AttributeError):
            _create_theme(None)

        # Test with empty colors object
        class EmptyColors:
            pass

        with pytest.raises(AttributeError):
            _create_theme(EmptyColors())

        # Test with colors object missing required attributes
        class PartialColors:
            def __init__(self):
                self.rosewater = type("Color", (), {"hex": "#f5e0dc"})()
                # Missing other required colors

        with pytest.raises(AttributeError):
            _create_theme(PartialColors())

    def test_create_theme_with_malformed_color_values(self) -> None:
        """Test theme creation with malformed color values."""

        class MalformedColors:
            def __init__(self):
                self.rosewater = type("Color", (), {"hex": "invalid_hex"})()
                self.flamingo = type("Color", (), {"hex": "#invalid"})()
                self.pink = type("Color", (), {"hex": "not_a_color"})()
                self.mauve = type("Color", (), {"hex": "#"})()  # Empty hex
                self.red = type("Color", (), {"hex": "#12345"})()  # Too short
                self.maroon = type("Color", (), {"hex": "#1234567"})()  # Too long
                self.peach = type("Color", (), {"hex": "#GGGGGG"})()  # Invalid chars
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

        # Should raise StyleSyntaxError for malformed colors
        colors = MalformedColors()
        with pytest.raises(Exception, match=r".*"):  # Rich will raise StyleSyntaxError
            _create_theme(colors)

    def test_create_theme_with_missing_color_attributes(self) -> None:
        """Test theme creation when color objects are missing hex attributes."""

        class ColorsWithoutHex:
            def __init__(self):
                self.rosewater = type("Color", (), {})()  # No hex attribute
                self.flamingo = type(
                    "Color", (), {"rgb": (242, 205, 205)}
                )()  # Wrong attribute
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

        # Should raise AttributeError for missing hex attributes
        colors = ColorsWithoutHex()
        with pytest.raises(AttributeError):
            _create_theme(colors)

    def test_set_theme_with_invalid_names(self) -> None:
        """Test set_theme with invalid theme names."""
        # Test with None
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme(None)

        # Test with empty string
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("")

        # Test with invalid theme name
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("invalid_theme")

        # Test with non-string types
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme(123)

        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme(["dark", "light"])

        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme({"theme": "dark"})

    def test_set_theme_with_edge_case_names(self) -> None:
        """Test set_theme with edge case theme names."""
        # Test with whitespace-only names
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("   ")

        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("\t\n")

        # Test with very long names
        long_name = "a" * 1000
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme(long_name)

        # Test with unicode names
        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("dark-🚀")

        with pytest.raises(ValueError, match="Unknown theme"):
            set_theme("light-中文")

    def test_get_rich_color_with_edge_cases(self) -> None:
        """Test get_rich_color with edge case inputs."""
        # Test with None - should return default since .get() handles None gracefully
        result = get_rich_color(None)
        assert result == "text"  # Should return default

        # Test with empty string
        result = get_rich_color("")
        assert result == "text"  # Should return default

        # Test with whitespace-only string
        result = get_rich_color("   ")
        assert result == "text"  # Should return default

        # Test with very long strings
        long_label = "a" * 1000
        result = get_rich_color(long_label)
        assert result == "text"  # Should return default

        # Test with unicode strings
        unicode_label = "TP-🚀-中文"
        result = get_rich_color(unicode_label)
        assert result == "text"  # Should return default

        # Test with special characters
        special_label = "TP@#$%^&*()"
        result = get_rich_color(special_label)
        assert result == "text"  # Should return default

    def test_theme_creation_with_corrupted_color_data(self) -> None:
        """Test theme creation with corrupted or unexpected color data."""

        # Test with colors that have non-string hex values
        class CorruptedColors:
            def __init__(self):
                self.rosewater = type(
                    "Color", (), {"hex": 12345}
                )()  # Integer instead of string
                self.flamingo = type(
                    "Color", (), {"hex": None}
                )()  # None instead of string
                self.pink = type(
                    "Color", (), {"hex": True}
                )()  # Boolean instead of string
                self.mauve = type(
                    "Color", (), {"hex": [1, 2, 3]}
                )()  # List instead of string
                self.red = type(
                    "Color", (), {"hex": {"r": 255, "g": 0, "b": 0}}
                )()  # Dict instead of string
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

        # Should raise Exception for corrupted color data
        colors = CorruptedColors()
        with pytest.raises(Exception, match=r".*"):  # Rich will raise various errors
            _create_theme(colors)

    def test_theme_creation_under_memory_pressure(self) -> None:
        """Test theme creation under memory pressure conditions."""
        # Create many theme objects to simulate memory pressure
        themes = []
        try:
            for i in range(100):  # Reduced from 1000 to avoid test timeouts

                class MockColors:
                    def __init__(self, _index: Any):
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

                colors = MockColors(i)
                theme = _create_theme(colors)
                themes.append(theme)

                # Verify theme is still functional
                assert isinstance(theme, Theme)
                assert theme.styles is not None

        except MemoryError:
            # Memory error is acceptable under extreme conditions
            pass
        finally:
            # Clean up themes
            themes.clear()
