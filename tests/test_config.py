"""
Tests for ConfigManager module.

Tests cover:
- Configuration loading
- Configuration saving
- Configuration validation
- Default values
- Invalid configuration handling
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, mock_open

from tea.config import (
    ConfigManager,
    DEFAULT_CONFIG,
    get_config_path,
    validate_config,
    VALID_QUALITIES,
    VALID_DUPLICATE_ACTIONS,
    VALID_MP3_QUALITIES,
)
from tea.exceptions import ConfigurationError, ValidationError


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager class functionality."""

    def test_init_default_path(self, mock_logger: MagicMock):
        """Test ConfigManager initialization with default path."""
        manager = ConfigManager(logger=mock_logger)
        assert manager._config_path is not None
        assert manager._logger is mock_logger

    def test_init_custom_path(self, temp_config_file: Path, mock_logger: MagicMock):
        """Test ConfigManager initialization with custom path."""
        manager = ConfigManager(
            config_path=str(temp_config_file),
            logger=mock_logger
        )
        assert manager._config_path == str(temp_config_file)

    def test_load_config_success(self, config_manager: ConfigManager, temp_config_file: Path):
        """Test successful configuration loading."""
        config = config_manager.load()
        assert "default_quality" in config
        assert config["default_quality"] == "5"

    def test_load_config_missing_file(self, mock_logger: MagicMock, temp_dir: Path):
        """Test loading config when file doesn't exist creates default."""
        missing_path = temp_dir / "missing-config.json"
        manager = ConfigManager(
            config_path=str(missing_path),
            logger=mock_logger
        )

        config = manager.load()
        assert config == DEFAULT_CONFIG

    def test_load_config_invalid_json(self, config_manager: ConfigManager, temp_config_file: Path):
        """Test loading config with invalid JSON."""
        # Write invalid JSON
        with open(temp_config_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(ConfigurationError):
            config_manager.load()

    def test_save_config_success(self, config_manager: ConfigManager, temp_config_file: Path):
        """Test successful configuration saving."""
        test_config = {"default_quality": "1", "default_output": "test_output"}

        config_manager.save(test_config)

        with open(temp_config_file, "r") as f:
            saved_config = json.load(f)

        assert saved_config["default_quality"] == "1"
        assert saved_config["default_output"] == "test_output"

    def test_save_config_creates_directory(self, mock_logger: MagicMock, temp_dir: Path):
        """Test saving config creates directory if it doesn't exist."""
        new_dir = temp_dir / "subdir" / "nested"
        new_config_path = new_dir / "config.json"

        manager = ConfigManager(
            config_path=str(new_config_path),
            logger=mock_logger
        )

        manager.save(DEFAULT_CONFIG)

        assert new_config_path.exists()

    def test_get_value(self, config_manager: ConfigManager):
        """Test getting individual configuration values."""
        config_manager.load()
        assert config_manager.get("default_quality") == "5"

    def test_get_value_with_default(self, config_manager: ConfigManager):
        """Test getting missing value returns default."""
        config_manager.load()
        result = config_manager.get("nonexistent_key", default="fallback")
        assert result == "fallback"

    def test_set_value(self, config_manager: ConfigManager):
        """Test setting individual configuration values."""
        config_manager.load()
        config_manager.set("default_quality", "1")
        assert config_manager.get("default_quality") == "1"

    def test_set_invalid_quality(self, config_manager: ConfigManager):
        """Test setting invalid quality raises ValidationError."""
        config_manager.load()
        with pytest.raises(ValidationError):
            config_manager.set("default_quality", "invalid")

    def test_validate_config_valid(self):
        """Test validate_config with valid configuration."""
        config = DEFAULT_CONFIG.copy()
        assert validate_config(config) is True

    def test_validate_config_invalid_quality(self):
        """Test validate_config with invalid quality."""
        config = DEFAULT_CONFIG.copy()
        config["default_quality"] = "invalid"
        assert validate_config(config) is False

    def test_validate_config_invalid_duplicate_action(self):
        """Test validate_config with invalid duplicate action."""
        config = DEFAULT_CONFIG.copy()
        config["duplicate_action"] = "invalid_action"
        assert validate_config(config) is False

    def test_validate_config_invalid_mp3_quality(self):
        """Test validate_config with invalid MP3 quality."""
        config = DEFAULT_CONFIG.copy()
        config["mp3_quality"] = "999"
        assert validate_config(config) is False

    def test_validate_config_invalid_concurrent_downloads(self):
        """Test validate_config with invalid concurrent downloads."""
        config = DEFAULT_CONFIG.copy()
        config["concurrent_downloads"] = 0  # Must be positive
        assert validate_config(config) is False

    def test_reset_to_defaults(self, config_manager: ConfigManager, temp_config_file: Path):
        """Test resetting configuration to defaults."""
        # Modify config
        config_manager.load()
        config_manager.set("default_quality", "1")

        # Reset
        config_manager.reset_to_defaults()
        assert config_manager.get("default_quality") == "5"

    def test_get_config_path(self):
        """Test get_config_path returns valid path."""
        path = get_config_path()
        assert path is not None
        assert "tea-config.json" in path


@pytest.mark.unit
class TestConfigConstants:
    """Test configuration constants."""

    def test_default_config_exists(self):
        """Test DEFAULT_CONFIG is defined."""
        assert DEFAULT_CONFIG is not None
        assert isinstance(DEFAULT_CONFIG, dict)

    def test_default_config_has_required_keys(self):
        """Test DEFAULT_CONFIG has all required keys."""
        required_keys = [
            "default_quality",
            "default_output",
            "concurrent_downloads",
            "thumbnail_embed",
            "mp3_quality",
            "duplicate_action",
        ]
        for key in required_keys:
            assert key in DEFAULT_CONFIG

    def test_valid_qualities(self):
        """Test VALID_QUALITIES contains expected values."""
        assert "5" in VALID_QUALITIES  # Audio only
        assert "1" in VALID_QUALITIES  # Best quality
        assert "best" in VALID_QUALITIES

    def test_valid_duplicate_actions(self):
        """Test VALID_DUPLICATE_ACTIONS contains expected values."""
        assert "ask" in VALID_DUPLICATE_ACTIONS
        assert "download" in VALID_DUPLICATE_ACTIONS
        assert "skip" in VALID_DUPLICATE_ACTIONS

    def test_valid_mp3_qualities(self):
        """Test VALID_MP3_QUALITIES contains expected values."""
        assert "128" in VALID_MP3_QUALITIES
        assert "320" in VALID_MP3_QUALITIES
