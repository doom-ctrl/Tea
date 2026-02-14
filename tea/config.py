"""
Configuration management for Tea YouTube Downloader.

This module handles loading, saving, and validating configuration.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from tea.exceptions import ValidationError, ConfigurationError
from tea.constants import (
    VALID_QUALITIES,
    VALID_DUPLICATE_ACTIONS,
    VALID_MP3_QUALITIES,
    DEFAULT_CONFIG as CONSTANTS_DEFAULT_CONFIG,
)

# Re-export for backward compatibility
DEFAULT_CONFIG = CONSTANTS_DEFAULT_CONFIG


def get_config_path() -> str:
    """Get path to config file."""
    # Look in the same directory as this module
    module_dir = Path(__file__).parent.parent
    return str(module_dir / 'tea-config.json')


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration values.

    Args:
        config: Configuration dictionary to validate

    Returns:
        True if valid

    Raises:
        ValidationError: If any configuration value is invalid
    """
    # Validate default_quality
    if 'default_quality' in config:
        if config['default_quality'] not in VALID_QUALITIES:
            raise ValidationError(
                message=f"Invalid default_quality '{config['default_quality']}'. "
                f"Valid values: {', '.join(sorted(VALID_QUALITIES))}",
                field="default_quality",
                value=config['default_quality'],
            )

    # Validate concurrent_downloads
    if 'concurrent_downloads' in config:
        concurrent = config['concurrent_downloads']
        if not isinstance(concurrent, int) or not (1 <= concurrent <= 5):
            raise ValidationError(
                message=f"Invalid concurrent_downloads '{concurrent}'. "
                "Must be an integer between 1 and 5",
                field="concurrent_downloads",
                value=concurrent,
            )

    # Validate duplicate_action
    if 'duplicate_action' in config:
        if config['duplicate_action'] not in VALID_DUPLICATE_ACTIONS:
            raise ValidationError(
                message=f"Invalid duplicate_action '{config['duplicate_action']}'. "
                f"Valid values: {', '.join(VALID_DUPLICATE_ACTIONS)}",
                field="duplicate_action",
                value=config['duplicate_action'],
            )

    # Validate mp3_quality
    if 'mp3_quality' in config:
        if config['mp3_quality'] not in VALID_MP3_QUALITIES:
            raise ValidationError(
                message=f"Invalid mp3_quality '{config['mp3_quality']}'. "
                f"Valid values: {', '.join(VALID_MP3_QUALITIES)}",
                field="mp3_quality",
                value=config['mp3_quality'],
            )

    return True


class ConfigManager:
    """Manages Tea configuration loading, saving, and validation.

    This class handles all configuration operations including:
    - Loading configuration from JSON file
    - Saving configuration to JSON file
    - Validating configuration values
    - Getting and setting individual config values
    - Resetting to defaults

    Configuration is stored in tea-config.json in the project directory.

    Attributes:
        _config_path: Path to configuration file
        _config: Current configuration dictionary
        _logger: Logger instance for logging
    """

    def __init__(self, config_path: Optional[str] = None, logger=None):
        """Initialize ConfigManager with optional custom config path.

        Args:
            config_path: Path to config file. If None, uses default location.
            logger: Optional logger instance for logging operations.

        Raises:
            ConfigurationError: If config file exists but is corrupted
        """
        self._config_path = config_path or get_config_path()
        self._config: Dict[str, Any] = {}
        self._logger = logger
        self._load()

    @property
    def config_path(self) -> str:
        """Get the config file path."""
        return self._config_path

    def _load(self) -> None:
        """Load configuration from file."""
        # Start with defaults
        self._config = DEFAULT_CONFIG.copy()

        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self._config.update(user_config)

                # Validate loaded config
                try:
                    validate_config(self._config)
                except ValueError as e:
                    if self._logger:
                        self._logger.warning(f"Config validation error: {e}. Using defaults for invalid values.")
                    # Re-apply defaults for invalid values
                    for key, value in DEFAULT_CONFIG.items():
                        if key.startswith('_'):
                            continue
                        if key in self._config:
                            try:
                                temp_config = {key: self._config[key]}
                                validate_config(temp_config)
                            except ValueError:
                                self._config[key] = value

            except json.JSONDecodeError as e:
                if self._logger:
                    self._logger.warning(f"Error parsing config file: {e}. Using defaults.")
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error loading config: {e}. Using defaults.")
        else:
            # Create default config file
            self.save()

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate before saving
            validate_config(self._config)

            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)

            if self._logger:
                self._logger.info(f"Config saved to: {self._config_path}")
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
            auto_save: Save to file immediately

        Raises:
            ValueError: If the value is invalid
        """
        # Validate the new value
        validate_config({key: value})

        self._config[key] = value

        if auto_save:
            self.save()

    def update(self, updates: Dict[str, Any], auto_save: bool = True) -> None:
        """
        Update multiple configuration values.

        Args:
            updates: Dictionary of key-value pairs to update
            auto_save: Save to file immediately

        Raises:
            ValueError: If any value is invalid
        """
        # Validate all updates
        validate_config(updates)

        self._config.update(updates)

        if auto_save:
            self.save()

    @property
    def default_quality(self) -> str:
        """Get default quality setting."""
        return self.get('default_quality', '5')

    @property
    def default_output(self) -> str:
        """Get default output directory."""
        return self.get('default_output', 'downloads')

    @property
    def concurrent_downloads(self) -> int:
        """Get concurrent downloads setting."""
        return self.get('concurrent_downloads', 3)

    @property
    def mp3_quality(self) -> str:
        """Get MP3 quality setting."""
        return self.get('mp3_quality', '320')

    @property
    def duplicate_action(self) -> str:
        """Get duplicate action setting."""
        return self.get('duplicate_action', 'ask')

    @property
    def use_ai_filename_cleaning(self) -> bool:
        """Get AI filename cleaning setting."""
        return self.get('use_ai_filename_cleaning', False)

    @property
    def openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key."""
        return self.get('openrouter_api_key')

    @property
    def search_max_results(self) -> int:
        """Get search max results setting."""
        return self.get('search_max_results', 5)

    @property
    def search_min_duration(self) -> int:
        """Get search min duration setting."""
        return self.get('search_min_duration', 30)

    @property
    def search_max_duration(self) -> int:
        """Get search max duration setting."""
        return self.get('search_max_duration', 600)

    @property
    def search_use_ai(self) -> bool:
        """Get search use AI setting."""
        return self.get('search_use_ai', True)

    @property
    def search_fuzzy_threshold(self) -> int:
        """Get search fuzzy threshold setting."""
        return self.get('search_fuzzy_threshold', 70)

    @property
    def thumbnail_embed(self) -> bool:
        """Get thumbnail embedding setting."""
        return self.get('thumbnail_embed', True)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


# Convenience functions for backward compatibility
def load_config() -> Dict[str, Any]:
    """Load configuration from file (legacy function)."""
    manager = ConfigManager()
    return manager.to_dict()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file (legacy function)."""
    manager = ConfigManager()
    manager._config = config
    manager.save()
