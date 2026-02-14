"""
Tests for security validation utilities.

Tests cover:
- URL validation
- File path validation
- Metadata sanitization
- Timestamp validation
- Choice validation
- Clip title sanitization
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from tea.utils.security import (
    validate_url,
    validate_file_path,
    sanitize_path,
    sanitize_metadata,
    validate_timestamp,
    sanitize_clip_title,
    validate_choice,
    validate_quality,
    validate_concurrent_workers,
)
from tea.exceptions import ValidationError


@pytest.mark.unit
class TestURLValidation:
    """Test URL validation functionality."""

    def test_validate_url_valid_youtube(self):
        """Test validation of valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/playlist?list=PLxxxxxxxx",
            "https://www.youtube.com/@channelname",
            "https://www.youtube.com/c/channelname",
            "https://www.youtube.com/user/username",
        ]

        for url in valid_urls:
            assert validate_url(url) is True

    def test_validate_url_invalid(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "https://example.com/video",
            "ftp://files.com/file",
            "javascript:alert('xss')",
            "../../../etc/passwd",
            "",
            None,
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                validate_url(url)

    def test_validate_url_with_null_bytes(self):
        """Test URL validation rejects null bytes."""
        with pytest.raises(ValidationError):
            validate_url("https://youtube.com/watch?v=\x00")


@pytest.mark.unit
class TestFilePathValidation:
    """Test file path validation functionality."""

    def test_validate_file_path_valid(self, tmp_path):
        """Test validation of valid file paths."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        result = validate_file_path(str(test_file))
        assert result is not None

    def test_validate_file_path_with_allowed_extensions(self, tmp_path):
        """Test validation with allowed extension filtering."""
        # Create allowed file
        allowed_file = tmp_path / "test.mp4"
        allowed_file.touch()

        result = validate_file_path(str(allowed_file), allowed_extensions=[".mp4", ".mkv"])
        assert result is not None

    def test_validate_file_path_disallowed_extension(self, tmp_path):
        """Test validation rejects disallowed extensions."""
        test_file = tmp_path / "test.exe"
        test_file.touch()

        with pytest.raises(ValidationError):
            validate_file_path(str(test_file), allowed_extensions=[".mp4", ".mkv"])

    def test_validate_file_path_path_traversal(self):
        """Test validation prevents path traversal attacks."""
        traversal_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in traversal_paths:
            with pytest.raises(ValidationError):
                validate_file_path(path, base_dir="safe_dir")

    def test_validate_file_path_nonexistent(self, tmp_path):
        """Test validation rejects nonexistent files."""
        nonexistent = tmp_path / "does_not_exist.txt"

        with pytest.raises(ValidationError):
            validate_file_path(str(nonexistent), must_exist=True)


@pytest.mark.unit
class TestPathSanitization:
    """Test path sanitization functionality."""

    def test_sanitize_path_removes_dangerous_chars(self):
        """Test sanitization removes dangerous characters."""
        dangerous = "../../test.mp4\x00"
        safe = sanitize_path(dangerous)
        assert "\x00" not in safe
        assert ".." not in safe or safe.count("..") <= 1

    def test_sanitize_path_preserves_safe_chars(self):
        """Test sanitization preserves safe characters."""
        safe_path = "downloads/music/song.mp3"
        result = sanitize_path(safe_path)
        assert "song.mp3" in result

    def test_sanitize_path_empty_input(self):
        """Test sanitization handles empty input."""
        assert sanitize_path("") == ""
        assert sanitize_path(None) == ""

    def test_sanitize_path_quotes(self):
        """Test sanitization removes quote characters."""
        quoted = '"test.mp4"'
        result = sanitize_path(quoted)
        assert '"' not in result


@pytest.mark.unit
class TestMetadataSanitization:
    """Test metadata sanitization functionality."""

    def test_sanitize_metadata_removes_command_injection(self):
        """Test sanitization prevents command injection."""
        malicious = "title'; rm -rf /; echo '"
        safe = sanitize_metadata(malicious)
        assert ";" not in safe
        assert "rm -rf" not in safe

    def test_sanitize_metadata_preserves_safe_text(self):
        """Test sanitization preserves safe metadata."""
        safe_metadata = "Never Gonna Give You Up - Rick Astley"
        result = sanitize_metadata(safe_metadata)
        assert "Rick Astley" in result

    def test_sanitize_metadata_null_bytes(self):
        """Test sanitization removes null bytes."""
        malicious = "title\x00injection"
        safe = sanitize_metadata(malicious)
        assert "\x00" not in safe


@pytest.mark.unit
class TestTimestampValidation:
    """Test timestamp validation functionality."""

    def test_validate_timestamp_valid_formats(self):
        """Test validation of valid timestamp formats."""
        valid_timestamps = [
            "0:00",
            "1:30",
            "10:45",
            "1:30:45",
            "0:00:00",
        ]

        for timestamp in valid_timestamps:
            assert validate_timestamp(timestamp) is True

    def test_validate_timestamp_invalid_formats(self):
        """Test validation of invalid timestamp formats."""
        invalid_timestamps = [
            "invalid",
            "1:60",  # Invalid seconds
            "25:00",  # Invalid minutes (depends on context)
            "",
            "1:30:45:60",  # Too many components
        ]

        for timestamp in invalid_timestamps:
            with pytest.raises(ValidationError):
                validate_timestamp(timestamp)

    def test_validate_timestamp_negative_values(self):
        """Test validation rejects negative values."""
        with pytest.raises(ValidationError):
            validate_timestamp("-1:30")


@pytest.mark.unit
class TestClipTitleSanitization:
    """Test clip title sanitization functionality."""

    def test_sanitize_clip_title_removes_dangerous_chars(self):
        """Test clip title sanitization removes dangerous characters."""
        dangerous = "Clip; rm -rf / #injection"
        safe = sanitize_clip_title(dangerous)
        assert ";" not in safe
        assert "#" not in safe

    def test_sanitize_clip_title_preserves_safe_content(self):
        """Test sanitization preserves safe title content."""
        safe_title = "Intro - Welcome to the Video"
        result = sanitize_clip_title(safe_title)
        assert "Welcome" in result

    def test_sanitize_clip_title_empty(self):
        """Test sanitization handles empty input."""
        result = sanitize_clip_title("")
        assert result == ""


@pytest.mark.unit
class TestChoiceValidation:
    """Test choice validation functionality."""

    def test_validate_choice_valid(self):
        """Test validation of valid choice."""
        choices = ["a", "b", "c"]
        assert validate_choice("b", choices) == "b"

    def test_validate_choice_invalid(self):
        """Test validation of invalid choice."""
        choices = ["a", "b", "c"]
        with pytest.raises(ValidationError):
            validate_choice("d", choices)

    def test_validate_choice_case_sensitive(self):
        """Test validation is case sensitive by default."""
        choices = ["a", "b", "c"]
        with pytest.raises(ValidationError):
            validate_choice("A", choices)

    def test_validate_choice_empty(self):
        """Test validation rejects empty choice."""
        with pytest.raises(ValidationError):
            validate_choice("", ["a", "b", "c"])


@pytest.mark.unit
class TestQualityValidation:
    """Test quality validation functionality."""

    def test_validate_quality_valid(self):
        """Test validation of valid quality presets."""
        valid_qualities = ["1", "2", "3", "4", "5", "best", "720p", "audio"]
        for quality in valid_qualities:
            assert validate_quality(quality) is True

    def test_validate_quality_invalid(self):
        """Test validation of invalid quality."""
        with pytest.raises(ValidationError):
            validate_quality("999")


@pytest.mark.unit
class TestConcurrentWorkersValidation:
    """Test concurrent workers validation functionality."""

    def test_validate_concurrent_workers_valid(self):
        """Test validation of valid worker counts."""
        assert validate_concurrent_workers(1) == 1
        assert validate_concurrent_workers(5) == 5

    def test_validate_concurrent_workers_invalid(self):
        """Test validation of invalid worker counts."""
        with pytest.raises(ValidationError):
            validate_concurrent_workers(0)

        with pytest.raises(ValidationError):
            validate_concurrent_workers(-1)

    def test_validate_concurrent_workers_too_high(self):
        """Test validation rejects excessive worker counts."""
        with pytest.raises(ValidationError):
            validate_concurrent_workers(1000)
