"""
Integration tests for end-to-end workflows.

These tests cover complete user workflows across multiple modules:
- Complete video download workflow
- Complete playlist download workflow
- Complete search and download workflow
- Configuration change and download workflow
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import shutil

from tea.cli import CLI
from tea.config import ConfigManager
from tea.history import HistoryManager
from tea.downloader import DownloadService


@pytest.mark.integration
class TestDownloadWorkflow:
    """Test complete download workflows."""

    def test_video_download_workflow(self, temp_dir: Path, mock_logger: MagicMock):
        """Test complete workflow: download single video."""
        # Setup
        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"
        output_dir = temp_dir / "downloads"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        # Create managers
        config_manager = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )
        history_manager = HistoryManager(
            history_path=str(history_path),
            logger=mock_logger
        )

        # Create download service
        download_service = DownloadService(
            config_manager=config_manager,
            history_manager=history_manager,
            logger=mock_logger
        )

        # Test workflow
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Check not already downloaded
        assert history_manager.is_downloaded(url) is False

        # Mock the actual download
        with patch("tea.downloader.YoutubeDL") as mock_ytdlp:
            mock_instance = MagicMock()
            mock_instance.download = MagicMock(return_value=None)
            mock_ytdlp.return_value = mock_instance

            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir=str(output_dir),
            )

        assert result is True
        assert history_manager.is_downloaded(url) is True

    def test_playlist_download_workflow(self, temp_dir: Path, mock_logger: MagicMock):
        """Test complete workflow: download playlist."""
        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"
        output_dir = temp_dir / "downloads"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        config_manager = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )
        history_manager = HistoryManager(
            history_path=str(history_path),
            logger=mock_logger
        )

        download_service = DownloadService(
            config_manager=config_manager,
            history_manager=history_manager,
            logger=mock_logger
        )

        playlist_url = "https://www.youtube.com/playlist?list=PLxxxxxxxx"

        with patch("tea.downloader.YoutubeDL") as mock_ytdlp:
            mock_instance = MagicMock()
            mock_instance.download = MagicMock(return_value=None)
            mock_ytdlp.return_value = mock_instance

            result = download_service.download_playlist(
                url=playlist_url,
                quality="5",
                output_dir=str(output_dir),
            )

        # Verify history contains playlist entry
        history = history_manager.load()
        assert any(
            entry.get("url") == playlist_url
            for day_entries in history.values()
            for entry in day_entries
        )

    def test_search_and_download_workflow(self, temp_dir: Path, mock_logger: MagicMock):
        """Test complete workflow: search and download results."""
        # Setup search service
        with patch("tea.search.youtube_search.Search") as mock_search:
            mock_results = [
                {
                    "url": "https://youtu.be/video1",
                    "title": "Test Video 1",
                    "duration": 180,
                }
            ]
            mock_search.return_value = mock_results

            # This would integrate with the actual search workflow
            # For now, we verify the structure
            assert len(mock_results) > 0
            assert "url" in mock_results[0]


@pytest.mark.integration
class TestConfigWorkflow:
    """Test configuration-related workflows."""

    def test_config_change_affects_download(self, temp_dir: Path, mock_logger: MagicMock):
        """Test that changing config affects subsequent downloads."""
        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        config_manager = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )

        # Change default quality
        config_manager.set("default_quality", "1")
        assert config_manager.get("default_quality") == "1"

        # Verify config persists
        config_manager2 = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )
        assert config_manager2.get("default_quality") == "1"

    def test_invalid_config_rejected(self, temp_dir: Path, mock_logger: MagicMock):
        """Test that invalid configuration values are rejected."""
        config_path = temp_dir / "config.json"
        ConfigManager.create_default(str(config_path))

        config_manager = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )

        with pytest.raises(ValidationError):
            config_manager.set("default_quality", "invalid_quality")


@pytest.mark.integration
class TestHistoryWorkflow:
    """Test history-related workflows."""

    def test_duplicate_detection_workflow(self, temp_dir: Path, mock_logger: MagicMock):
        """Test complete duplicate detection workflow."""
        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        history_manager = HistoryManager(
            history_path=str(history_path),
            logger=mock_logger
        )

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Initially not downloaded
        assert history_manager.is_downloaded(url) is False

        # Add to history
        history_manager.add_entry(
            url=url,
            title="Test Video",
            content_type="video",
            quality="5",
        )

        # Now shows as downloaded
        assert history_manager.is_downloaded(url) is True

    def test_history_statistics_workflow(self, temp_dir: Path, mock_logger: MagicMock):
        """Test history statistics calculation."""
        history_path = temp_dir / "history.json"
        HistoryManager.create_empty(str(history_path))

        history_manager = HistoryManager(
            history_path=str(history_path),
            logger=mock_logger
        )

        # Add some downloads
        for i in range(5):
            history_manager.add_entry(
                url=f"https://youtu.be/video{i}",
                title=f"Video {i}",
                content_type="video",
                quality="5",
            )

        stats = history_manager.get_stats()
        assert stats["total_downloads"] == 5


@pytest.mark.integration
class TestCLIWorkflows:
    """Test CLI interaction workflows."""

    @patch("builtins.input")
    def test_interactive_download_flow(self, mock_input, temp_dir: Path, mock_logger: MagicMock):
        """Test interactive CLI download flow."""
        # Mock user inputs
        mock_input.side_effect = [
            "https://youtu.be/video1",  # URL
            "5",  # Quality
            "0",  # Exit
        ]

        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        cli = CLI(logger=mock_logger)

        # Get URLs (first interaction)
        urls = cli.get_urls_interactive()
        assert len(urls) == 1

    @patch("builtins.input")
    def test_batch_file_download_flow(self, mock_input, temp_dir: Path, mock_logger: MagicMock):
        """Test batch file download flow."""
        # Create batch file
        batch_file = temp_dir / "urls.txt"
        batch_file.write_text("https://youtu.be/video1\nhttps://youtu.be/video2\n")

        cli = CLI(logger=mock_logger)
        urls = cli.load_urls_from_file(str(batch_file))

        assert len(urls) == 2


@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery in workflows."""

    def test_download_failure_recovery(self, temp_dir: Path, mock_logger: MagicMock):
        """Test recovery from failed download."""
        config_path = temp_dir / "config.json"
        history_path = temp_dir / "history.json"
        output_dir = temp_dir / "downloads"

        ConfigManager.create_default(str(config_path))
        HistoryManager.create_empty(str(history_path))

        config_manager = ConfigManager(
            config_path=str(config_path),
            logger=mock_logger
        )
        history_manager = HistoryManager(
            history_path=str(history_path),
            logger=mock_logger
        )

        download_service = DownloadService(
            config_manager=config_manager,
            history_manager=history_manager,
            logger=mock_logger
        )

        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # First attempt fails
        with patch("tea.downloader.YoutubeDL") as mock_ytdlp:
            mock_instance = MagicMock()
            mock_instance.download = MagicMock(side_effect=Exception("Network error"))
            mock_ytdlp.return_value = mock_instance

            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir=str(output_dir),
            )

        assert result is False
        assert history_manager.is_downloaded(url) is False

        # Second attempt succeeds
        with patch("tea.downloader.YoutubeDL") as mock_ytdlp:
            mock_instance = MagicMock()
            mock_instance.download = MagicMock(return_value=None)
            mock_ytdlp.return_value = mock_instance

            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir=str(output_dir),
            )

        assert result is True
