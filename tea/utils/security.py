"""
Security utilities for Tea YouTube Downloader.

This module provides validation and sanitization functions to protect
against common security vulnerabilities including path traversal,
command injection, and unsafe file operations.
"""

import os
import re
from typing import List, Optional
from urllib.parse import urlparse


# Allowed YouTube domains
YOUTUBE_DOMAINS = {
    'youtube.com',
    'www.youtube.com',
    'm.youtube.com',
    'youtu.be'
}

# Allowed file extensions for user uploads
ALLOWED_TIMESTAMP_EXTENSIONS = {'.json'}

# Allowed quality values
ALLOWED_QUALITIES = {'best', '720p', '480p', '360p', 'audio', '5', '4', '3', '2', '1'}

# Timestamp format regex (MM:SS or HH:MM:SS)
TIMESTAMP_PATTERN = re.compile(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$')


class SecurityValidationError(Exception):
    """Raised when security validation fails"""
    pass


def validate_file_path(
    filepath: str,
    allowed_extensions: Optional[List[str]] = None,
    base_dir: Optional[str] = None
) -> str:
    """
    Validate and sanitize a file path to prevent path traversal attacks.

    Args:
        filepath: User-provided file path
        allowed_extensions: List of allowed extensions (e.g., ['.json', '.txt'])
        base_dir: Base directory that the path must stay within (optional)

    Returns:
        Sanitized absolute file path

    Raises:
        SecurityValidationError: If path validation fails
    """
    if not filepath or not isinstance(filepath, str):
        raise SecurityValidationError("File path cannot be empty")

    # Remove surrounding quotes
    filepath = filepath.strip().strip('"').strip("'")

    # Check for null bytes (potential exploit)
    if '\x00' in filepath:
        raise SecurityValidationError("File path contains null bytes")

    # Reject obvious path traversal attempts
    if '../' in filepath or '..\\' in filepath:
        raise SecurityValidationError("Path traversal not allowed")

    # Resolve to absolute path
    try:
        abs_path = os.path.abspath(filepath)
    except (ValueError, OSError) as e:
        raise SecurityValidationError(f"Invalid file path: {e}")

    # Check if path is within base directory if specified
    if base_dir:
        try:
            base_abs = os.path.abspath(base_dir)
            # Use realpath to resolve symlinks
            abs_path_real = os.path.realpath(abs_path)
            base_abs_real = os.path.realpath(base_abs)

            if not abs_path_real.startswith(base_abs_real):
                raise SecurityValidationError(
                    f"File path must be within {base_dir}"
                )
        except (OSError, ValueError) as e:
            raise SecurityValidationError(f"Path validation error: {e}")

    # Validate file extension
    if allowed_extensions:
        _, ext = os.path.splitext(abs_path)
        if ext.lower() not in allowed_extensions:
            raise SecurityValidationError(
                f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"
            )

    return abs_path


def sanitize_path(path: str) -> str:
    """
    Sanitize a path for safe use in file operations.

    Removes dangerous characters and resolves relative paths.

    Args:
        path: Path to sanitize

    Returns:
        Sanitized path string
    """
    if not path or not isinstance(path, str):
        return ''

    # Remove null bytes
    path = path.replace('\x00', '')

    # Remove surrounding quotes and whitespace
    path = path.strip().strip('"').strip("'")

    # Remove any remaining path traversal sequences
    path = path.replace('../', '').replace('..\\', '')

    return path


def validate_url(url: str) -> bool:
    """
    Validate that a URL is a YouTube URL.

    Args:
        url: URL to validate

    Returns:
        True if valid YouTube URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False

    # Reject protocol-relative URLs that could be exploited
    if url.startswith('//'):
        return False

    # Reject javascript: and data: URLs
    if url.lower().startswith(('javascript:', 'data:', 'vbscript:', 'file:')):
        return False

    try:
        parsed = urlparse(url)

        # Must have a scheme (http or https)
        if parsed.scheme not in ('http', 'https'):
            return False

        # Must have a netloc
        if not parsed.netloc:
            return False

        # Check if domain is YouTube
        domain = parsed.netloc.lower()
        if domain not in YOUTUBE_DOMAINS:
            return False

        return True

    except Exception:
        return False


def sanitize_metadata(value: str) -> str:
    """
    Sanitize metadata values for safe use in FFmpeg commands.

    Removes or escapes special characters that could be used
    for command injection.

    Args:
        value: Metadata value to sanitize

    Returns:
        Sanitized string safe for use in shell commands
    """
    if not value or not isinstance(value, str):
        return ''

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove potentially dangerous shell metacharacters
    # These could be used for command injection if passed to shell
    dangerous_chars = ['$', '`', '\\', '\n', '\r', '\x1b']
    for char in dangerous_chars:
        value = value.replace(char, '')

    # Limit length to prevent buffer overflow type issues
    value = value[:200]

    return value


def validate_timestamp(timestamp: str) -> bool:
    """
    Validate timestamp format (MM:SS or HH:MM:SS).

    Args:
        timestamp: Timestamp string to validate

    Returns:
        True if valid timestamp format, False otherwise
    """
    if not timestamp or not isinstance(timestamp, str):
        return False

    # Remove whitespace
    timestamp = timestamp.strip()

    # Check format with regex
    match = TIMESTAMP_PATTERN.match(timestamp)
    if not match:
        return False

    # Extract time components
    minutes = int(match.group(1))
    seconds = int(match.group(2))
    hours = int(match.group(3)) if match.group(3) else 0

    # Validate ranges
    if hours > 23:
        return False
    if minutes > 59:
        return False
    if seconds > 59:
        return False

    return True


def is_path_safe(path: str, base_dir: str = None) -> bool:
    """
    Check if a path is safe (no path traversal, within base_dir).

    Args:
        path: Path to check
        base_dir: Base directory that path must stay within (optional)

    Returns:
        True if path is safe, False otherwise
    """
    try:
        validate_file_path(path, base_dir=base_dir)
        return True
    except SecurityValidationError:
        return False


def validate_quality(quality: str) -> bool:
    """
    Validate quality selection.

    Args:
        quality: Quality value to validate

    Returns:
        True if valid quality, False otherwise
    """
    return quality in ALLOWED_QUALITIES


def validate_concurrent_workers(value: str) -> bool:
    """
    Validate concurrent worker count.

    Args:
        value: String value to validate

    Returns:
        True if valid worker count (1-5), False otherwise
    """
    try:
        num = int(value)
        return 1 <= num <= 5
    except (ValueError, TypeError):
        return False


def sanitize_clip_title(title: str) -> str:
    """
    Sanitize a clip title for safe use in filenames and metadata.

    Args:
        title: Title to sanitize

    Returns:
        Sanitized title
    """
    if not title or not isinstance(title, str):
        return 'Untitled'

    # Apply metadata sanitization first
    title = sanitize_metadata(title)

    # Replace filesystem-unsafe characters
    title = re.sub(r'[<>:"/\\|?*&]', '_', title)

    # Remove control characters
    title = ''.join(char for char in title if ord(char) >= 32)

    # Limit length and strip whitespace
    title = title.strip()[:100]

    return title if title else 'Untitled'


def validate_choice(choice: str, valid_choices: List[str]) -> bool:
    """
    Validate a user choice against allowed values.

    Args:
        choice: User's choice
        valid_choices: List of valid choices

    Returns:
        True if choice is valid, False otherwise
    """
    return choice in valid_choices
