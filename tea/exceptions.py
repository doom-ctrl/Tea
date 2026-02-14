"""
Custom exception hierarchy for Tea YouTube Downloader.

This module defines all custom exceptions used throughout the Tea application,
providing specific exception types for different error scenarios.
"""

from typing import Optional, Dict, Any


class TeaError(Exception):
    """Base exception for all Tea application errors.

    All custom exceptions in the Tea application inherit from this base class,
    allowing for broad exception handling that catches all Tea-specific errors.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize TeaError.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of the error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class DownloadError(TeaError):
    """Raised when a download operation fails.

    This exception is used when:
    - Download fails after max retries
    - Network issues prevent download
    - Video is unavailable or restricted
    - File system errors during download
    """

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        retry_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize DownloadError.

        Args:
            message: Human-readable error message
            url: The URL that failed to download
            retry_count: Number of retries attempted
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if url:
            error_details["url"] = url
        if retry_count is not None:
            error_details["retry_count"] = retry_count

        super().__init__(message, error_details)
        self.url = url
        self.retry_count = retry_count


class ValidationError(TeaError):
    """Raised when input validation fails.

    This exception is used when:
    - URL validation fails
    - File path validation fails
    - Timestamp format is invalid
    - Quality selection is invalid
    - User input doesn't meet requirements
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize ValidationError.

        Args:
            message: Human-readable error message
            field: The field that failed validation
            value: The invalid value
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            error_details["value"] = str(value)

        super().__init__(message, error_details)
        self.field = field
        self.value = value


class ConfigurationError(TeaError):
    """Raised when configuration is invalid or cannot be loaded.

    This exception is used when:
    - Config file is corrupted (invalid JSON)
    - Required config values are missing
    - Config values are outside valid ranges
    - Config file cannot be read or written
    """

    def __init__(
        self,
        message: str,
        config_path: Optional[str] = None,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize ConfigurationError.

        Args:
            message: Human-readable error message
            config_path: Path to the configuration file
            config_key: The configuration key that is invalid
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if config_path:
            error_details["config_path"] = config_path
        if config_key:
            error_details["config_key"] = config_key

        super().__init__(message, error_details)
        self.config_path = config_path
        self.config_key = config_key


class FFmpegError(TeaError):
    """Raised when an FFmpeg operation fails.

    This exception is used when:
    - FFmpeg is not installed or not in PATH
    - FFmpeg command fails during execution
    - Video/audio splitting fails
    - MP3 extraction fails
    - Metadata embedding fails
    """

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        exit_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize FFmpegError.

        Args:
            message: Human-readable error message
            command: The FFmpeg command that failed
            exit_code: The exit code from FFmpeg
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if command:
            error_details["command"] = command
        if exit_code is not None:
            error_details["exit_code"] = exit_code

        super().__init__(message, error_details)
        self.command = command
        self.exit_code = exit_code


class HistoryError(TeaError):
    """Raised when history operations fail.

    This exception is used when:
    - History file is corrupted
    - History cannot be saved or loaded
    - Duplicate checking fails
    """

    def __init__(
        self,
        message: str,
        history_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize HistoryError.

        Args:
            message: Human-readable error message
            history_path: Path to the history file
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if history_path:
            error_details["history_path"] = history_path

        super().__init__(message, error_details)
        self.history_path = history_path


class TimestampError(TeaError):
    """Raised when timestamp processing fails.

    This exception is used when:
    - Timestamp parsing fails
    - Timestamp format is invalid
    - Chapter extraction fails
    - Timestamp file cannot be read
    """

    def __init__(
        self,
        message: str,
        timestamp_value: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize TimestampError.

        Args:
            message: Human-readable error message
            timestamp_value: The timestamp value that caused the error
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if timestamp_value:
            error_details["timestamp"] = timestamp_value

        super().__init__(message, error_details)
        self.timestamp_value = timestamp_value


class SearchError(TeaError):
    """Raised when search operations fail.

    This exception is used when:
    - YouTube search API fails
    - No results found
    - Search query is invalid
    - AI-powered search fails
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SearchError.

        Args:
            message: Human-readable error message
            query: The search query that failed
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if query:
            error_details["query"] = query

        super().__init__(message, error_details)
        self.query = query
