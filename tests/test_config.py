"""Unit tests for repoman.config module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from repoman.config import Config, get_os_config_path, load_answers, validate_answers_file


def test_load_answers_file_exists(tmp_path: Path) -> None:
    """load_answers returns dict from existing YAML file."""
    p = tmp_path / "answers.yml"
    p.write_text("foo: bar\ncount: 42\n")
    data = load_answers(p)
    assert data == {"foo": "bar", "count": 42}


def test_load_answers_empty_file(tmp_path: Path) -> None:
    """load_answers returns empty dict for empty file."""
    p = tmp_path / "empty.yml"
    p.write_text("")
    data = load_answers(p)
    assert data == {}


def test_load_answers_file_not_found() -> None:
    """load_answers raises FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError, match="Answers file not found"):
        load_answers(Path("/nonexistent/answers.yml"))


def test_load_answers_invalid_yaml(tmp_path: Path) -> None:
    """load_answers raises yaml.YAMLError for invalid YAML."""
    p = tmp_path / "bad.yml"
    p.write_text("foo: [unclosed\n")
    with pytest.raises(yaml.YAMLError):
        load_answers(p)


def test_validate_answers_file_valid_uses_fixture() -> None:
    """validate_answers_file returns valid report for fixture file with full answers."""
    fixture_path = Path(__file__).parent / "fixtures" / "default_copier_answers.yml"
    report = validate_answers_file(fixture_path)
    assert report.valid is True, f"Expected valid: {report}"


def test_validate_answers_file_missing_keys(tmp_path: Path) -> None:
    """validate_answers_file returns invalid report when required keys missing."""
    p = tmp_path / "answers.yml"
    p.write_text("{}")
    report = validate_answers_file(p)
    assert report.valid is False
    assert len(report.missing_keys) >= 1


def test_validate_answers_file_nonexistent() -> None:
    """validate_answers_file raises FileNotFoundError when file does not exist."""
    with pytest.raises(FileNotFoundError, match="Answers file not found"):
        validate_answers_file(Path("/nonexistent/answers.yml"))


# --- get_os_config_path tests ---


def test_get_os_config_path_linux_and_macos(tmp_path: Path) -> None:
    """get_os_config_path returns ~/.config/app/config.json on Linux/macOS."""
    with (
        patch("repoman.config.paths.platform.system", return_value="Linux"),
        patch("repoman.config.paths.Path.home", return_value=tmp_path),
    ):
        result = get_os_config_path("myapp")
    assert result == tmp_path / ".config" / "myapp" / "config.json"


def test_get_os_config_path_linux_xdg_config_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_os_config_path uses XDG_CONFIG_HOME when set on Linux."""
    custom_config = tmp_path / "custom_config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(custom_config))
    with patch("repoman.config.paths.platform.system", return_value="Linux"):
        result = get_os_config_path("myapp")
    assert result == custom_config / "myapp" / "config.json"


def test_get_os_config_path_windows(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_os_config_path returns %APPDATA%/app/config.json on Windows."""
    monkeypatch.delenv("APPDATA", raising=False)
    with (
        patch("repoman.config.paths.platform.system", return_value="Windows"),
        patch("repoman.config.paths.Path.home", return_value=tmp_path),
    ):
        result = get_os_config_path("myapp")
    assert result == tmp_path / "AppData" / "Roaming" / "myapp" / "config.json"


def test_get_os_config_path_windows_appdata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """get_os_config_path uses APPDATA when set on Windows."""
    custom_appdata = tmp_path / "CustomAppData"
    monkeypatch.setenv("APPDATA", str(custom_appdata))
    with patch("repoman.config.paths.platform.system", return_value="Windows"):
        result = get_os_config_path("myapp")
    assert result == custom_appdata / "myapp" / "config.json"


# --- Config.load tests ---


def test_config_load_explicit_path(tmp_path: Path) -> None:
    """Config.load uses custom_path when provided and loads from JSON."""
    config_file = tmp_path / "repoman" / "config.json"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('{"log_format": "custom %(message)s"}')

    config = Config.load(custom_path=config_file)
    assert config.log_format == "custom %(message)s"


def test_config_load_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Config.load uses REPOMAN_CONFIG_PATH when custom_path is None."""
    config_dir = tmp_path / "custom"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    config_file.write_text('{"log_format": "from env path"}')
    monkeypatch.setenv("REPOMAN_CONFIG_PATH", str(config_file))

    config = Config.load(custom_path=None)
    assert config.log_format == "from env path"


def test_config_load_creates_directory(tmp_path: Path) -> None:
    """Config.load creates parent directory if it does not exist."""
    config_file = tmp_path / "new_dir" / "repoman" / "config.json"
    assert not config_file.parent.exists()

    Config.load(custom_path=config_file)
    assert config_file.parent.exists()


def test_config_load_defaults_when_no_file(tmp_path: Path) -> None:
    """Config.load returns defaults when config file does not exist."""
    config_file = tmp_path / "repoman" / "config.json"
    config_file.parent.mkdir(parents=True)

    config = Config.load(custom_path=config_file)
    assert config.log_format == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def test_config_load_env_overrides_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variable REPOMAN_LOG_FORMAT overrides value from JSON file."""
    config_file = tmp_path / "repoman" / "config.json"
    config_file.parent.mkdir(parents=True)
    config_file.write_text('{"log_format": "from file"}')
    monkeypatch.setenv("REPOMAN_LOG_FORMAT", "from env")

    config = Config.load(custom_path=config_file)
    assert config.log_format == "from env"
