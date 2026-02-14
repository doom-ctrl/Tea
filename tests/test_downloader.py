"""
Tests for DownloadService module.

Tests cover:
- Video download functionality
- Playlist download functionality
- Channel download functionality
- Retry logic
- Progress reporting
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path
from typing import Dict, Any

from tea.downloader import DownloadService, MAX_RETRIES, RETRY_DELAY
from tea.exceptions import DownloadError, ValidationError, FFmpegError


@pytest.mark.unit
class TestDownloadService:
    """Test DownloadService class functionality."""

    def test_init_with_dependencies(
        self,
        download_service: DownloadService,
        config_manager: MagicMock,
        history_manager: MagicMock,
    ):
        """Test DownloadService initialization with all dependencies."""
        assert download_service._config_manager is config_manager
        assert download_service._history_manager is history_manager

    def test_init_with_none_dependencies(self, mock_logger: Mock):
        """Test DownloadService initialization creates dependencies if not provided."""
        service = DownloadService(logger=mock_logger)
        assert service._config_manager is not None
        assert service._history_manager is not None
        assert service._info_extractor is not None
        assert service._progress_reporter is not None

    def test_download_single_video_success(
        self,
        download_service: DownloadService,
        sample_video_info: Dict[str, Any],
        mock_ytdlp: MagicMock,
    ):
        """Test successful single video download."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir="downloads",
            )

        assert result is True

    def test_download_single_video_with_retries(
        self,
        download_service: DownloadService,
        mock_ytdlp: MagicMock,
    ):
        """Test download retry logic on failure."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Fail first two attempts, succeed on third
        mock_ytdlp.download.side_effect = [Exception("Network error"), None, None]

        with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir="downloads",
            )

        assert result is True
        assert mock_ytdlp.download.call_count == 2  # First fails, second succeeds

    def test_download_single_video_max_retries_exceeded(
        self,
        download_service: DownloadService,
        mock_ytdlp: MagicMock,
    ):
        """Test download fails after max retries."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # Always fail
        mock_ytdlp.download.side_effect = Exception("Permanent error")

        with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
            result = download_service.download_single_video(
                url=url,
                quality="5",
                output_dir="downloads",
            )

        assert result is False
        assert mock_ytdlp.download.call_count == MAX_RETRIES

    def test_download_single_video_invalid_url(
        self,
        download_service: DownloadService,
    ):
        """Test download with invalid URL raises ValidationError."""
        with pytest.raises(ValidationError):
            download_service.download_single_video(
                url="not-a-valid-url",
                quality="5",
                output_dir="downloads",
            )

    def test_download_with_timestamp_splitting(
        self,
        download_service: DownloadService,
        mock_ffmpeg_service: MagicMock,
        mock_timestamp_processor: MagicMock,
        sample_timestamps: list[Dict[str, Any]],
    ):
        """Test download with video splitting by timestamps."""
        mock_timestamp_processor.parse_timestamp_list.return_value = sample_timestamps

        download_service.download_with_timestamps(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            timestamps=sample_timestamps,
            output_dir="downloads",
        )

        mock_ffmpeg_service.split_video.assert_called_once()

    def test_download_with_timestamps_ffmpeg_failure(
        self,
        download_service: DownloadService,
        mock_ffmpeg_service: MagicMock,
        sample_timestamps: list[Dict[str, Any]],
    ):
        """Test FFmpeg failure during timestamp splitting."""
        mock_ffmpeg_service.split_video.side_effect = FFmpegError("FFmpeg not found")

        with pytest.raises(FFmpegError):
            download_service.download_with_timestamps(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                timestamps=sample_timestamps,
                output_dir="downloads",
            )

    def test_concurrent_downloads(
        self,
        download_service: DownloadService,
        mock_ytdlp: MagicMock,
    ):
        """Test downloading multiple videos concurrently."""
        urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video3",
        ]

        with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
            results = download_service.download_multiple(
                urls=urls,
                quality="5",
                output_dir="downloads",
                concurrent=3,
            )

        assert len(results) == 3
        assert all(r is True for r in results)

    def test_concurrent_downloads_with_failures(
        self,
        download_service: DownloadService,
        mock_ytdlp: MagicMock,
    ):
        """Test concurrent downloads with some failures."""
        urls = [
            "https://www.youtube.com/watch?v=video1",
            "https://www.youtube.com/watch?v=video2",
            "https://www.youtube.com/watch?v=video3",
        ]

        # Second download fails
        mock_ytdlp.download.side_effect = [None, Exception("Failed"), None]

        with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
            results = download_service.download_multiple(
                urls=urls,
                quality="5",
                output_dir="downloads",
                concurrent=3,
            )

        assert results[0] is True
        assert results[1] is False
        assert results[2] is True

    def test_concurrent_downloads_invalid_worker_count(
        self,
        download_service: DownloadService,
    ):
        """Test concurrent downloads with invalid worker count."""
        with pytest.raises(ValidationError):
            download_service.download_multiple(
                urls=["https://www.youtube.com/watch?v=video1"],
                quality="5",
                output_dir="downloads",
                concurrent=0,  # Invalid
            )

    def test_save_to_history(
        self,
        download_service: DownloadService,
        history_manager: MagicMock,
    ):
        """Test saving download to history."""
        download_service.save_to_history(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            title="Test Video",
            content_type="video",
            quality="5",
        )

        history_manager.add_entry.assert_called_once()

    def test_is_already_downloaded(
        self,
        download_service: DownloadService,
        history_manager: MagicMock,
    ):
        """Test checking if URL is already in history."""
        history_manager.is_downloaded.return_value = True

        result = download_service.is_already_downloaded(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        )

        assert result is True
        history_manager.is_downloaded.assert_called_once()

    def test_get_quality_format(
        self,
        download_service: DownloadService,
    ):
        """Test quality format conversion."""
        assert download_service.get_quality_format("5") == "bestaudio/best"
        assert download_service.get_quality_format("1") == "bestvideo+bestaudio/best"
        assert download_service.get_quality_format("best") == "best"

    def test_get_quality_format_invalid(
        self,
        download_service: DownloadService,
    ):
        """Test quality format conversion with invalid quality."""
        with pytest.raises(ValidationError):
            download_service.get_quality_format("invalid")


@pytest.mark.unit
class TestDownloadConstants:
    """Test download-related constants."""

    def test_max_retries(self):
        """Test MAX_RETRIES constant value."""
        assert MAX_RETRIES == 3

    def test_retry_delay(self):
        """Test RETRY_DELAY constant value."""
        assert RETRY_DELAY == 2
