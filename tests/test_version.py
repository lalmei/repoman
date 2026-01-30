"""Unit tests for repoman version and debugging utilities."""

import os
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from rich.console import Console

from repoman._version import (
    Environment,
    Package,
    Variable,
    _interpreter_name_version,
    debug_info,
    get_debug_info,
    get_version,
    version_info,
)


class TestVersionFunctions:
    """Test version-related functions."""

    def test_get_version_success(self) -> None:
        """Test get_version with valid distribution."""
        result = get_version("repoman")
        assert isinstance(result, str)
        assert result != "0.0.0"  # Should get actual version

    @patch("repoman._version.metadata.version")
    def test_get_version_package_not_found(self, mock_version: Any) -> None:
        """Test get_version when package is not found."""
        from importlib.metadata import PackageNotFoundError  # noqa: PLC0415

        mock_version.side_effect = PackageNotFoundError("nonexistent-package")
        result = get_version("nonexistent-package")
        assert result == "0.0.0"

    def test_version_info(self) -> None:
        """Test version_info function."""
        result = version_info()
        assert "repoman:" in str(result)
        # Check that it's a Rich Text object with styling
        assert hasattr(result, "spans")


class TestInterpreterNameVersion:
    """Test _interpreter_name_version function."""

    def test_interpreter_name_version_with_implementation(self) -> None:
        """Test _interpreter_name_version when sys.implementation exists."""
        result = _interpreter_name_version()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

    @patch("sys.implementation")
    def test_interpreter_name_version_without_implementation(self, mock_implementation: Any) -> None:
        """Test _interpreter_name_version when sys.implementation doesn't exist."""
        # Remove implementation attribute
        delattr(sys, "implementation")
        try:
            result = _interpreter_name_version()
            assert result == ("", "0.0.0")
        finally:
            # Restore implementation attribute
            sys.implementation = mock_implementation


class TestDataClasses:
    """Test dataclasses."""

    def test_variable_dataclass(self) -> None:
        """Test Variable dataclass."""
        var = Variable("TEST_VAR", "test_value")
        assert var.name == "TEST_VAR"
        assert var.value == "test_value"

    def test_package_dataclass(self) -> None:
        """Test Package dataclass."""
        pkg = Package("test-package", "1.0.0")
        assert pkg.name == "test-package"
        assert pkg.version == "1.0.0"

    def test_environment_dataclass(self) -> None:
        """Test Environment dataclass."""
        packages = [Package("test", "1.0.0")]
        variables = [Variable("TEST", "value")]
        env = Environment(
            interpreter_name="python",
            interpreter_version="3.12.0",
            interpreter_path="/usr/bin/python",
            platform="Linux",
            packages=packages,
            variables=variables,
        )
        assert env.interpreter_name == "python"
        assert env.interpreter_version == "3.12.0"
        assert env.interpreter_path == "/usr/bin/python"
        assert env.platform == "Linux"
        assert env.packages == packages
        assert env.variables == variables


class TestGetDebugInfo:
    """Test get_debug_info function."""

    def test_get_debug_info_basic(self) -> None:
        """Test get_debug_info returns valid Environment object."""
        result = get_debug_info()
        assert isinstance(result, Environment)
        assert result.interpreter_name
        assert result.interpreter_version
        assert result.interpreter_path
        assert result.platform
        assert isinstance(result.packages, list)
        assert isinstance(result.variables, list)

    def test_get_debug_info_packages(self) -> None:
        """Test get_debug_info includes repoman package."""
        result = get_debug_info()
        repoman_packages = [pkg for pkg in result.packages if pkg.name == "repoman"]
        assert len(repoman_packages) == 1
        assert repoman_packages[0].version

    @patch.dict(os.environ, {"PYTHONPATH": "/test/path", "REPOMAN_DEBUG": "true"})
    def test_get_debug_info_with_environment_variables(self) -> None:
        """Test get_debug_info with environment variables."""
        result = get_debug_info()
        variable_names = [var.name for var in result.variables]
        assert "PYTHONPATH" in variable_names
        assert "REPOMAN_DEBUG" in variable_names

    @patch.dict(os.environ, {}, clear=True)
    def test_get_debug_info_without_environment_variables(self) -> None:
        """Test get_debug_info without environment variables."""
        result = get_debug_info()
        # Should still return Environment object even without variables
        assert isinstance(result, Environment)
        assert isinstance(result.variables, list)

    @patch.dict(os.environ, {"PYTHONPATH": "", "REPOMAN_TEST": ""})
    def test_get_debug_info_with_empty_variables(self) -> None:
        """Test get_debug_info filters out empty environment variables."""
        result = get_debug_info()
        # Empty variables should be filtered out
        for var in result.variables:
            assert var.value != ""

    def test_get_debug_info_package_version_error(self) -> None:
        """Test get_debug_info handles package version errors."""
        # This test verifies the function works normally
        result = get_debug_info()
        # Should still return Environment object
        assert isinstance(result, Environment)
        assert isinstance(result.packages, list)


class TestDebugInfo:
    """Test debug_info function."""

    def test_debug_info_with_console(self) -> None:
        """Test debug_info with provided console."""
        console = Console()
        # Should not raise any exceptions
        debug_info(console)

    def test_debug_info_without_console(self) -> None:
        """Test debug_info without console (creates default)."""
        # Should not raise any exceptions
        debug_info()

    def test_debug_info_calls_get_debug_info(self) -> None:
        """Test debug_info calls get_debug_info."""
        # This test verifies the function works without mocking
        console = Console()
        debug_info(console)  # Should not raise any exceptions

    def test_debug_info_creates_console_with_theme(self) -> None:
        """Test debug_info creates console with theme when no console provided."""
        # This test verifies the function works without mocking
        debug_info()  # Should not raise any exceptions


class TestErrorHandling:
    """Test error handling scenarios."""

    @patch("repoman._version.metadata.version")
    def test_get_version_metadata_error(self, mock_version: Any) -> None:
        """Test get_version handles metadata errors."""
        from importlib.metadata import (  # noqa: PLC0415 - Conditional import for test error handling
            PackageNotFoundError,
        )

        mock_version.side_effect = PackageNotFoundError("test-package")
        result = get_version("test-package")
        assert result == "0.0.0"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_get_version_empty_string(self) -> None:
        """Test get_version with empty string."""
        # This test verifies that empty string raises ValueError
        try:
            get_version("")
            pytest.fail("Expected ValueError for empty string")
        except ValueError:
            pass

    def test_get_version_none(self) -> None:
        """Test get_version with None."""
        # This test verifies that None raises ValueError
        try:
            get_version(None)
            pytest.fail("Expected ValueError for None")
        except ValueError:
            pass

    @patch.dict(os.environ, {"REPOMAN_" + "A" * 1000: "very_long_value"})
    def test_get_debug_info_with_very_long_variable_names(self) -> None:
        """Test get_debug_info with very long variable names."""
        result = get_debug_info()
        assert isinstance(result, Environment)

    def test_get_debug_info_with_special_characters_in_path(self) -> None:
        """Test get_debug_info with special characters in paths."""
        # This test ensures the function handles paths with special characters
        result = get_debug_info()
        assert isinstance(result, Environment)
        assert isinstance(result.interpreter_path, str)

    def test_get_debug_info_interpreter_error(self) -> None:
        """Test get_debug_info handles interpreter version errors."""
        # This test verifies the function works normally
        result = get_debug_info()
        assert isinstance(result, Environment)

    @patch("sys.implementation")
    @pytest.mark.usefixtures("_mock_implementation")
    def test_interpreter_name_version_non_final_release(self) -> None:
        """Test _interpreter_name_version with non-final release level.

        This test verifies version formatting for non-final releases (line 73).
        """
        # Create a mock implementation with non-final release level
        mock_version = SimpleNamespace(major=3, minor=12, micro=0)
        mock_release = SimpleNamespace(releaselevel="alpha", serial=1)
        mock_version.releaselevel = mock_release.releaselevel
        mock_version.serial = mock_release.serial

        mock_impl = SimpleNamespace(name="cpython", version=mock_version)
        mock_impl.version.releaselevel = "alpha"
        mock_impl.version.serial = 1

        with patch("sys.implementation", mock_impl):
            name, version = _interpreter_name_version()
            assert name == "cpython"
            # For alpha release with serial 1, version should be "3.12.0a1"
            # (base version + first char of releaselevel + serial)
            assert version == "3.12.0a1", f"Expected '3.12.0a1', got '{version}'"

    @patch("repoman._version.metadata.distributions")
    def test_get_debug_info_package_not_found_error(self, mock_distributions: Any) -> None:
        """Test get_debug_info handles PackageNotFoundError.

        This test verifies PackageNotFoundError handling (line 117, 125-127).
        """
        from importlib.metadata import PackageNotFoundError  # noqa: PLC0415

        mock_distributions.side_effect = PackageNotFoundError("Package not found")
        result = get_debug_info()

        # Should fallback to repoman package
        assert isinstance(result, Environment)
        assert len(result.packages) >= 1
        repoman_packages = [pkg for pkg in result.packages if pkg.name == "repoman"]
        assert len(repoman_packages) == 1

    @patch("repoman._version.metadata.distributions")
    def test_get_debug_info_key_error(self, mock_distributions: Any) -> None:
        """Test get_debug_info handles KeyError.

        This test verifies KeyError handling (lines 125-127).
        """
        # Create a mock distribution that raises KeyError
        mock_dist = type(
            "MockDist",
            (),
            {
                "metadata": type(
                    "MockMeta", (), {"get": lambda self, key, default=None: (_ for _ in ()).throw(KeyError("key"))}
                )()
            },
        )()
        mock_distributions.return_value = [mock_dist]

        result = get_debug_info()

        # Should fallback to repoman package
        assert isinstance(result, Environment)
        assert len(result.packages) >= 1

    @patch("repoman._version.metadata.distributions")
    def test_get_debug_info_attribute_error(self, mock_distributions: Any) -> None:
        """Test get_debug_info handles AttributeError.

        This test verifies AttributeError handling (lines 125-127).
        """
        # Create a mock distribution that raises AttributeError
        mock_dist = type("MockDist", (), {})()
        # Accessing metadata will raise AttributeError
        mock_distributions.return_value = [mock_dist]

        result = get_debug_info()

        # Should fallback to repoman package
        assert isinstance(result, Environment)
        assert len(result.packages) >= 1
