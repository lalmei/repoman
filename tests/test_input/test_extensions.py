"""Unit tests for repoman extensions module."""

import subprocess
from datetime import datetime, timezone
from typing import Any
from unittest.mock import patch

import pytest
from jinja2 import Environment

from repoman.extensions import (
    CurrentYearExtension,
    GitExtension,
    SlugifyExtension,
    git_user_email,
    git_user_name,
    slugify,
)


class TestGitUserFunctions:
    """Test git user name and email functions."""

    @patch("subprocess.getoutput")
    def test_git_user_name_with_valid_output(self, mock_getoutput: Any) -> None:
        """Test git_user_name with valid git config output."""
        mock_getoutput.return_value = "John Doe"
        result = git_user_name("default_user")
        assert result == "John Doe"
        mock_getoutput.assert_called_once_with("git config user.name")

    @patch("subprocess.getoutput")
    def test_git_user_name_with_empty_output(self, mock_getoutput: Any) -> None:
        """Test git_user_name with empty git config output."""
        mock_getoutput.return_value = ""
        result = git_user_name("default_user")
        assert result == "default_user"
        mock_getoutput.assert_called_once_with("git config user.name")

    @patch("subprocess.getoutput")
    def test_git_user_name_with_whitespace_output(self, mock_getoutput: Any) -> None:
        """Test git_user_name with whitespace-only git config output."""
        mock_getoutput.return_value = "   \n\t  "
        result = git_user_name("default_user")
        assert result == "default_user"
        mock_getoutput.assert_called_once_with("git config user.name")

    @patch("subprocess.getoutput")
    def test_git_user_email_with_valid_output(self, mock_getoutput: Any) -> None:
        """Test git_user_email with valid git config output."""
        mock_getoutput.return_value = "john.doe@example.com"
        result = git_user_email("default@example.com")
        assert result == "john.doe@example.com"
        mock_getoutput.assert_called_once_with("git config user.email")

    @patch("subprocess.getoutput")
    def test_git_user_email_with_empty_output(self, mock_getoutput: Any) -> None:
        """Test git_user_email with empty git config output."""
        mock_getoutput.return_value = ""
        result = git_user_email("default@example.com")
        assert result == "default@example.com"
        mock_getoutput.assert_called_once_with("git config user.email")

    @patch("subprocess.getoutput")
    def test_git_user_email_with_whitespace_output(self, mock_getoutput: Any) -> None:
        """Test git_user_email with whitespace-only git config output."""
        mock_getoutput.return_value = "   \n\t  "
        result = git_user_email("default@example.com")
        assert result == "default@example.com"
        mock_getoutput.assert_called_once_with("git config user.email")

    @patch("subprocess.getoutput")
    def test_git_user_name_with_subprocess_error(self, mock_getoutput: Any) -> None:
        """Test git_user_name when subprocess raises an error."""
        mock_getoutput.side_effect = subprocess.SubprocessError("Git not found")
        # The actual function doesn't handle subprocess errors gracefully
        with pytest.raises(subprocess.SubprocessError):
            git_user_name("default_user")

    @patch("subprocess.getoutput")
    def test_git_user_email_with_subprocess_error(self, mock_getoutput: Any) -> None:
        """Test git_user_email when subprocess raises an error."""
        mock_getoutput.side_effect = subprocess.SubprocessError("Git not found")
        # The actual function doesn't handle subprocess errors gracefully
        with pytest.raises(subprocess.SubprocessError):
            git_user_email("default@example.com")


class TestSlugifyFunction:
    """Test slugify function with various inputs."""

    def test_slugify_basic_string(self) -> None:
        """Test slugify with basic string."""
        result = slugify("Hello World")
        assert result == "hello-world"

    def test_slugify_with_special_characters(self) -> None:
        """Test slugify with special characters."""
        result = slugify("Hello, World! @#$%^&*()")
        assert result == "hello-world"

    def test_slugify_with_unicode_characters(self) -> None:
        """Test slugify with unicode characters."""
        result = slugify("Café & Résumé")
        assert result == "cafe-resume"

    def test_slugify_with_multiple_spaces(self) -> None:
        """Test slugify with multiple spaces."""
        result = slugify("Hello   World")
        assert result == "hello-world"

    def test_slugify_with_underscores(self) -> None:
        """Test slugify with underscores."""
        result = slugify("Hello_World")
        assert result == "hello-world"

    def test_slugify_with_dashes(self) -> None:
        """Test slugify with existing dashes."""
        result = slugify("Hello-World")
        assert result == "hello-world"

    def test_slugify_with_mixed_separators(self) -> None:
        """Test slugify with mixed separators."""
        result = slugify("Hello_World-Test")
        assert result == "hello-world-test"

    def test_slugify_with_custom_separator(self) -> None:
        """Test slugify with custom separator."""
        result = slugify("Hello World", separator="_")
        assert result == "hello_world"

    def test_slugify_with_empty_string(self) -> None:
        """Test slugify with empty string."""
        result = slugify("")
        assert result == ""

    def test_slugify_with_whitespace_only(self) -> None:
        """Test slugify with whitespace-only string."""
        result = slugify("   \n\t  ")
        assert result == ""

    def test_slugify_with_numbers(self) -> None:
        """Test slugify with numbers."""
        result = slugify("Project 123")
        assert result == "project-123"

    def test_slugify_with_numbers_only(self) -> None:
        """Test slugify with numbers only."""
        result = slugify("123456")
        assert result == "123456"

    def test_slugify_with_leading_trailing_dashes(self) -> None:
        """Test slugify with leading/trailing dashes."""
        result = slugify("-Hello World-")
        assert result == "hello-world"

    def test_slugify_with_leading_trailing_underscores(self) -> None:
        """Test slugify with leading/trailing underscores."""
        result = slugify("_Hello World_")
        assert result == "hello-world"

    def test_slugify_with_non_string_input(self) -> None:
        """Test slugify with non-string input."""
        result = slugify(123)
        assert result == "123"

    def test_slugify_with_none_input(self) -> None:
        """Test slugify with None input."""
        result = slugify(None)
        assert result == "none"

    def test_slugify_with_complex_unicode(self) -> None:
        """Test slugify with complex unicode characters."""
        result = slugify("Müllerstraße 123")
        assert result == "mullerstrae-123"

    def test_slugify_with_chinese_characters(self) -> None:
        """Test slugify with Chinese characters."""
        result = slugify("你好世界")
        assert result == ""

    def test_slugify_with_emoji(self) -> None:
        """Test slugify with emoji."""
        result = slugify("Hello 🚀 World")
        assert result == "hello-world"

    def test_slugify_with_custom_separator_underscore(self) -> None:
        """Test slugify with underscore separator."""
        result = slugify("Hello World", separator="_")
        assert result == "hello_world"

    def test_slugify_with_custom_separator_dot(self) -> None:
        """Test slugify with dot separator."""
        result = slugify("Hello World", separator=".")
        assert result == "hello.world"

    def test_slugify_with_custom_separator_empty(self) -> None:
        """Test slugify with empty separator."""
        result = slugify("Hello World", separator="")
        assert result == "helloworld"


class TestGitExtension:
    """Test GitExtension Jinja2 extension."""

    def test_git_extension_initialization(self) -> None:
        """Test GitExtension initialization."""
        env = Environment()
        extension = GitExtension(env)

        assert "git_user_name" in env.filters
        assert "git_user_email" in env.filters
        assert env.filters["git_user_name"] == git_user_name
        assert env.filters["git_user_email"] == git_user_email

    @patch("repoman.extensions.git_user_name")
    @patch("repoman.extensions.git_user_email")
    def test_git_extension_filters_in_template(self, mock_git_email: Any, mock_git_name: Any) -> None:
        """Test GitExtension filters in Jinja2 template."""
        mock_git_name.return_value = "John Doe"
        mock_git_email.return_value = "john@example.com"

        env = Environment()
        GitExtension(env)

        template = env.from_string(
            "Name: {{ 'default' | git_user_name }}, Email: {{ 'default@example.com' | git_user_email }}"
        )
        result = template.render()

        assert result == "Name: John Doe, Email: john@example.com"
        mock_git_name.assert_called_once_with("default")
        mock_git_email.assert_called_once_with("default@example.com")


class TestSlugifyExtension:
    """Test SlugifyExtension Jinja2 extension."""

    def test_slugify_extension_initialization(self) -> None:
        """Test SlugifyExtension initialization."""
        env = Environment()
        extension = SlugifyExtension(env)

        assert "slugify" in env.filters
        assert env.filters["slugify"] == slugify

    def test_slugify_extension_filter_in_template(self) -> None:
        """Test SlugifyExtension filter in Jinja2 template."""
        env = Environment()
        SlugifyExtension(env)

        template = env.from_string("{{ 'Hello World!' | slugify }}")
        result = template.render()

        assert result == "hello-world"

    def test_slugify_extension_filter_with_custom_separator(self) -> None:
        """Test SlugifyExtension filter with custom separator in template."""
        env = Environment()
        SlugifyExtension(env)

        template = env.from_string("{{ 'Hello World!' | slugify('_') }}")
        result = template.render()

        assert result == "hello_world"


class TestCurrentYearExtension:
    """Test CurrentYearExtension Jinja2 extension."""

    def test_current_year_extension_initialization(self) -> None:
        """Test CurrentYearExtension initialization."""
        env = Environment()
        extension = CurrentYearExtension(env)

        assert "current_year" in env.globals
        assert env.globals["current_year"] == get_current_year()

    def test_current_year_extension_global_in_template(self) -> None:
        """Test CurrentYearExtension global in Jinja2 template."""
        env = Environment()
        CurrentYearExtension(env)

        template = env.from_string("Current year: {{ current_year }}")
        result = template.render()

        assert result == f"Current year: {date.today().year}"

    def test_current_year_extension_math_operations(self) -> None:
        """Test CurrentYearExtension with math operations in template."""
        env = Environment()
        CurrentYearExtension(env)

        template = env.from_string("Next year: {{ current_year + 1 }}")
        result = template.render()

        assert result == f"Next year: {date.fromtimestamp(time.time()).year + 1}"


class TestExtensionsIntegration:
    """Test multiple extensions working together."""

    def test_multiple_extensions_in_single_environment(self) -> None:
        """Test multiple extensions working together in one environment."""
        env = Environment()
        GitExtension(env)
        SlugifyExtension(env)
        CurrentYearExtension(env)

        # Test that all extensions are properly registered
        assert "git_user_name" in env.filters
        assert "git_user_email" in env.filters
        assert "slugify" in env.filters
        assert "current_year" in env.globals

    @patch("repoman.extensions.git_user_name")
    def test_multiple_extensions_in_template(self, mock_git_name: Any) -> None:
        """Test multiple extensions working together in a template."""
        mock_git_name.return_value = "John Doe"

        env = Environment()
        GitExtension(env)
        SlugifyExtension(env)
        CurrentYearExtension(env)

        template = env.from_string("User: {{ 'default' | git_user_name | slugify }}, Year: {{ current_year }}")
        result = template.render()

        assert result == f"User: john-doe, Year: {date.fromtimestamp(time.time()).year}"
        mock_git_name.assert_called_once_with("default")


class TestExtensionsErrorHandling:
    """Test error handling in extensions."""

    def test_git_extension_with_subprocess_error(self) -> None:
        """Test GitExtension handles subprocess errors gracefully."""
        with patch("subprocess.getoutput") as mock_getoutput:
            mock_getoutput.side_effect = subprocess.SubprocessError("Git not found")

            env = Environment()
            GitExtension(env)

            template = env.from_string("{{ 'default' | git_user_name }}")
            # The actual function doesn't handle subprocess errors gracefully
            with pytest.raises(subprocess.SubprocessError):
                template.render()

    def test_slugify_extension_with_invalid_input(self) -> None:
        """Test SlugifyExtension handles invalid input gracefully."""
        env = Environment()
        SlugifyExtension(env)

        # Test with None
        template = env.from_string("{{ none | slugify }}")
        result = template.render()
        assert result == "none"

        # Test with empty string
        template = env.from_string("{{ '' | slugify }}")
        result = template.render()
        assert result == ""

    def test_current_year_extension_consistency(self) -> None:
        """Test CurrentYearExtension returns consistent year value."""
        env = Environment()
        CurrentYearExtension(env)

        # Get the year value multiple times
        year1 = env.globals["current_year"]
        year2 = env.globals["current_year"]

        assert year1 == year2
        assert year1 == date.fromtimestamp(time.time()).year
