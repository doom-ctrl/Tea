"""
Pytest configuration and shared fixtures for Tea tests.

This module provides common fixtures used across all test suites.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock
from typing import Generator, Dict, Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tea.config import ConfigManager, DEFAULT_CONFIG
from tea.history import HistoryManager
from tea.downloader import DownloadService
from tea.info import InfoExtractor
from tea.progress import ProgressReporter
from tea.ffmpeg import FFmpegService
from tea.timestamps import TimestampProcessor


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files.

    Yields:
        Path to temporary directory that is cleaned up after test
    """
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path)


@pytest.fixture
def temp_config_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary config file with default values.

    Yields:
        Path to temporary config file
    """
    config_path = temp_dir / "test-config.json"
    config_data = DEFAULT_CONFIG.copy()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
    yield config_path


@pytest.fixture
def temp_history_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create a temporary history file.

    Yields:
        Path to temporary history file
    """
    history_path = temp_dir / "test-history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump({}, f)
    yield history_path


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger.

    Returns:
        Mock object with logger interface
    """
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


@pytest.fixture
def config_manager(temp_config_file: Path, mock_logger: Mock) -> ConfigManager:
    """Create a ConfigManager instance for testing.

    Args:
        temp_config_file: Path to temporary config file
        mock_logger: Mock logger instance

    Returns:
        ConfigManager instance
    """
    return ConfigManager(
        config_path=str(temp_config_file),
        logger=mock_logger
    )


@pytest.fixture
def history_manager(temp_history_file: Path, mock_logger: Mock) -> HistoryManager:
    """Create a HistoryManager instance for testing.

    Args:
        temp_history_file: Path to temporary history file
        mock_logger: Mock logger instance

    Returns:
        HistoryManager instance
    """
    return HistoryManager(
        history_path=str(temp_history_file),
        logger=mock_logger
    )


@pytest.fixture
def mock_info_extractor() -> MagicMock:
    """Create a mock InfoExtractor.

    Returns:
        Mock InfoExtractor instance
    """
    mock = MagicMock(spec=InfoExtractor)
    mock.get_url_info = MagicMock()
    mock.get_video_info = MagicMock()
    mock.get_playlist_info = MagicMock()
    mock.get_channel_info = MagicMock()
    return mock


@pytest.fixture
def mock_progress_reporter() -> MagicMock:
    """Create a mock ProgressReporter.

    Returns:
        Mock ProgressReporter instance
    """
    mock = MagicMock(spec=ProgressReporter)
    mock.report_progress = MagicMock()
    mock.report_error = MagicMock()
    mock.report_success = MagicMock()
    return mock


@pytest.fixture
def mock_ffmpeg_service() -> MagicMock:
    """Create a mock FFmpegService.

    Returns:
        Mock FFmpegService instance
    """
    mock = MagicMock(spec=FFmpegService)
    mock.split_video = MagicMock(return_value=True)
    mock.extract_audio = MagicMock(return_value=True)
    mock.embed_thumbnail = MagicMock(return_value=True)
    mock.check_ffmpeg_available = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_timestamp_processor() -> MagicMock:
    """Create a mock TimestampProcessor.

    Returns:
        Mock TimestampProcessor instance
    """
    mock = MagicMock(spec=TimestampProcessor)
    mock.parse_timestamp_list = MagicMock(return_value=[])
    mock.get_timestamps_interactive = MagicMock(return_value=[])
    mock.extract_youtube_chapters = MagicMock(return_value=[])
    return mock


@pytest.fixture
def download_service(
    config_manager: ConfigManager,
    history_manager: HistoryManager,
    mock_info_extractor: MagicMock,
    mock_progress_reporter: MagicMock,
    mock_ffmpeg_service: MagicMock,
    mock_timestamp_processor: MagicMock,
    mock_logger: Mock,
) -> DownloadService:
    """Create a DownloadService instance with mocked dependencies.

    Args:
        config_manager: ConfigManager instance
        history_manager: HistoryManager instance
        mock_info_extractor: Mock InfoExtractor
        mock_progress_reporter: Mock ProgressReporter
        mock_ffmpeg_service: Mock FFmpegService
        mock_timestamp_processor: Mock TimestampProcessor
        mock_logger: Mock logger

    Returns:
        DownloadService instance with all dependencies mocked
    """
    return DownloadService(
        config_manager=config_manager,
        history_manager=history_manager,
        info_extractor=mock_info_extractor,
        progress_reporter=mock_progress_reporter,
        ffmpeg_service=mock_ffmpeg_service,
        timestamp_processor=mock_timestamp_processor,
        logger=mock_logger,
    )


@pytest.fixture
def sample_video_info() -> Dict[str, Any]:
    """Sample video information for testing.

    Returns:
        Dictionary with sample video metadata
    """
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Never Gonna Give You Up",
        "uploader": "Rick Astley",
        "duration": 212,
        "uploader_id": "RickAstleyVEVO",
        "upload_date": "20091025",
        "description": "The official video",
        "thumbnail": "https://example.com/thumb.jpg",
    }


@pytest.fixture
def sample_playlist_info() -> Dict[str, Any]:
    """Sample playlist information for testing.

    Returns:
        Dictionary with sample playlist metadata
    """
    return {
        "id": "PLxxxxxxxxxxxxxxxx",
        "title": "Test Playlist",
        "uploader": "Test Channel",
        "uploader_id": "testchannel",
        "entry_count": 5,
    }


@pytest.fixture
def sample_channel_info() -> Dict[str, Any]:
    """Sample channel information for testing.

    Returns:
        Dictionary with sample channel metadata
    """
    return {
        "id": "UCxxxxxxxxxxxxxxxxxx",
        "name": "Test Channel",
        "uploader": "Test Channel Name",
        "uploader_id": "testchannel",
    }


@pytest.fixture
def valid_youtube_urls() -> Dict[str, str]:
    """Valid YouTube URLs for testing.

    Returns:
        Dictionary with URL type as key and URL as value
    """
    return {
        "video": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "short": "https://youtu.be/dQw4w9WgXcQ",
        "playlist": "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxx",
        "channel": "https://www.youtube.com/@testchannel",
        "channel_custom": "https://www.youtube.com/c/testchannel",
    }


@pytest.fixture
def invalid_urls() -> list[str]:
    """Invalid URLs for testing validation.

    Returns:
        List of invalid URLs
    """
    return [
        "not-a-url",
        "https://example.com/video",
        "ftp://files.com/file",
        "javascript:alert('xss')",
        "../../../etc/passwd",
    ]


@pytest.fixture
def sample_timestamps() -> list[Dict[str, Any]]:
    """Sample timestamps for testing.

    Returns:
        List of timestamp dictionaries
    """
    return [
        {"start": 0, "end": 30, "title": "Intro"},
        {"start": 30, "end": 120, "title": "Main Content"},
        {"start": 120, "end": 150, "title": "Outro"},
    ]


@pytest.fixture
def sample_history() -> Dict[str, list[Dict[str, Any]]]:
    """Sample download history for testing.

    Returns:
        Dictionary with dates as keys and download lists as values
    """
    return {
        "2024-01-15": [
            {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "title": "Never Gonna Give You Up",
                "type": "video",
                "quality": "5",
                "timestamp": "2024-01-15T10:30:00",
            }
        ],
        "2024-01-16": [
            {
                "url": "https://www.youtube.com/playlist?list=PLxxxxx",
                "title": "Test Playlist",
                "type": "playlist",
                "quality": "5",
                "count": 5,
                "timestamp": "2024-01-16T14:20:00",
            }
        ],
    }


# Integration test fixtures
@pytest.fixture
def mock_ytdlp() -> MagicMock:
    """Create a mock yt-dlp YoutubeDL instance.

    Returns:
        Mock YoutubeDL instance
    """
    mock = MagicMock()
    mock.download = MagicMock(return_value=None)
    mock.extract_info = MagicMock(return_value=None)
    return mock


@pytest.fixture
def isolated_env(temp_dir: Path) -> Generator[Dict[str, str], None, None]:
    """Provide isolated environment for integration tests.

    Yields:
        Dictionary with isolated environment variables
    """
    original_env = os.environ.copy()

    # Set isolated environment
    isolated = {
        "HOME": str(temp_dir),
        "USERPROFILE": str(temp_dir),
        "XDG_CONFIG_HOME": str(temp_dir / ".config"),
        "TEA_CONFIG_PATH": str(temp_dir / "config.json"),
        "TEA_HISTORY_PATH": str(temp_dir / "history.json"),
    }

    os.environ.update(isolated)
    try:
        yield isolated
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)
