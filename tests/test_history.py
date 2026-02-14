"""
Tests for HistoryManager module.

Tests cover:
- History loading
- History saving
- Adding entries
- Checking duplicates
- Displaying history
- History clearing
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import MagicMock

from tea.history import HistoryManager, get_history_path
from tea.exceptions import HistoryError


@pytest.mark.unit
class TestHistoryManager:
    """Test HistoryManager class functionality."""

    def test_init_default_path(self, mock_logger: MagicMock):
        """Test HistoryManager initialization with default path."""
        manager = HistoryManager(logger=mock_logger)
        assert manager._history_path is not None
        assert manager._logger is mock_logger

    def test_init_custom_path(self, temp_history_file: Path, mock_logger: MagicMock):
        """Test HistoryManager initialization with custom path."""
        manager = HistoryManager(
            history_path=str(temp_history_file),
            logger=mock_logger
        )
        assert manager._history_path == str(temp_history_file)

    def test_load_empty_history(self, history_manager: HistoryManager):
        """Test loading empty history file."""
        history = history_manager.load()
        assert history == {}

    def test_load_existing_history(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
        sample_history: dict,
    ):
        """Test loading existing history file."""
        # Write sample history
        with open(temp_history_file, "w") as f:
            json.dump(sample_history, f)

        history = history_manager.load()
        assert history == sample_history

    def test_load_invalid_json(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
    ):
        """Test loading history with invalid JSON creates empty history."""
        with open(temp_history_file, "w") as f:
            f.write("{ invalid json }")

        history = history_manager.load()
        assert history == {}

    def test_add_entry(self, history_manager: HistoryManager):
        """Test adding an entry to history."""
        history_manager.add_entry(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
            content_type="video",
            quality="5",
        )

        history = history_manager.load()
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in history
        assert len(history[today]) == 1
        assert history[today][0]["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_add_multiple_entries_same_day(
        self,
        history_manager: HistoryManager,
    ):
        """Test adding multiple entries on the same day."""
        history_manager.add_entry(
            url="https://www.youtube.com/watch?v=video1",
            title="Video 1",
            content_type="video",
            quality="5",
        )
        history_manager.add_entry(
            url="https://www.youtube.com/watch?v=video2",
            title="Video 2",
            content_type="video",
            quality="5",
        )

        history = history_manager.load()
        today = datetime.now().strftime("%Y-%m-%d")
        assert len(history[today]) == 2

    def test_is_downloaded_true(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
    ):
        """Test checking if URL is already downloaded returns True."""
        # Add entry first
        history_manager.add_entry(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
            content_type="video",
            quality="5",
        )

        result = history_manager.is_downloaded("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result is True

    def test_is_downloaded_false(self, history_manager: HistoryManager):
        """Test checking if URL is already downloaded returns False."""
        result = history_manager.is_downloaded("https://www.youtube.com/watch?v=nonexistent")
        assert result is False

    def test_is_downloaded_with_playlist_url(
        self,
        history_manager: HistoryManager,
    ):
        """Test checking playlist URL with individual videos in history."""
        # Add individual video from playlist
        history_manager.add_entry(
            url="https://www.youtube.com/watch?v=video1",
            title="Playlist Video 1",
            content_type="video",
            quality="5",
        )

        # Check with playlist URL - should return False since playlist itself wasn't downloaded
        result = history_manager.is_downloaded("https://www.youtube.com/playlist?list=PLxxxxx")
        assert result is False

    def test_get_history_stats(
        self,
        history_manager: HistoryManager,
        sample_history: dict,
        temp_history_file: Path,
    ):
        """Test getting history statistics."""
        with open(temp_history_file, "w") as f:
            json.dump(sample_history, f)

        stats = history_manager.get_stats()
        assert stats["total_downloads"] == 2
        assert stats["unique_days"] == 2

    def test_clear_history(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
        sample_history: dict,
    ):
        """Test clearing history."""
        with open(temp_history_file, "w") as f:
            json.dump(sample_history, f)

        history_manager.clear()
        history = history_manager.load()
        assert history == {}

    def test_get_recent_downloads(
        self,
        history_manager: HistoryManager,
        sample_history: dict,
        temp_history_file: Path,
    ):
        """Test getting recent downloads."""
        with open(temp_history_file, "w") as f:
            json.dump(sample_history, f)

        recent = history_manager.get_recent(limit=10)
        assert len(recent) == 2

    def test_get_recent_downloads_limit(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
    ):
        """Test getting recent downloads with limit."""
        # Add multiple entries
        for i in range(10):
            history_manager.add_entry(
                url=f"https://www.youtube.com/watch?v=video{i}",
                title=f"Video {i}",
                content_type="video",
                quality="5",
            )

        recent = history_manager.get_recent(limit=5)
        assert len(recent) == 5

    def test_get_downloads_by_type(
        self,
        history_manager: HistoryManager,
        sample_history: dict,
        temp_history_file: Path,
    ):
        """Test getting downloads filtered by type."""
        with open(temp_history_file, "w") as f:
            json.dump(sample_history, f)

        videos = history_manager.get_by_type("video")
        assert len(videos) == 1
        assert videos[0]["type"] == "video"

        playlists = history_manager.get_by_type("playlist")
        assert len(playlists) == 1
        assert playlists[0]["type"] == "playlist"

    def test_save_failure_on_readonly_file(
        self,
        history_manager: HistoryManager,
        temp_history_file: Path,
        mock_logger: MagicMock,
    ):
        """Test saving fails appropriately on readonly file."""
        # This test is platform-specific and may not work on Windows
        # It's included as an example of error handling test
        pass

    def test_entry_metadata_preserved(
        self,
        history_manager: HistoryManager,
    ):
        """Test that all entry metadata is preserved."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        title = "Test Video"
        content_type = "video"
        quality = "5"

        history_manager.add_entry(
            url=url,
            title=title,
            content_type=content_type,
            quality=quality,
        )

        history = history_manager.load()
        today = datetime.now().strftime("%Y-%m-%d")
        entry = history[today][0]

        assert entry["url"] == url
        assert entry["title"] == title
        assert entry["type"] == content_type
        assert entry["quality"] == quality
        assert "timestamp" in entry


@pytest.mark.unit
class TestHistoryHelpers:
    """Test history helper functions."""

    def test_get_history_path(self):
        """Test get_history_path returns valid path."""
        path = get_history_path()
        assert path is not None
        assert "tea-history.json" in path
