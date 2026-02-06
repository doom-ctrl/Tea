"""
Download orchestration for Tea YouTube Downloader.

This module handles the core download functionality for videos, playlists, and channels.
"""

import os
import time
from typing import List, Dict, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from yt_dlp import YoutubeDL

# Import from tea modules
try:
    from tea.config import ConfigManager
    from tea.history import HistoryManager
    from tea.info import InfoExtractor
    from tea.progress import ProgressReporter
    from tea.ffmpeg import FFmpegService
    from tea.timestamps import TimestampProcessor
    from tea.logger import setup_logger
except ImportError:
    # Fallback for development
    from tea.config import ConfigManager
    from tea.history import HistoryManager
    from tea.info import InfoExtractor
    from tea.progress import ProgressReporter
    from tea.ffmpeg import FFmpegService
    from tea.timestamps import TimestampProcessor
    from tea.logger import setup_logger

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_CONCURRENT_WORKERS = 5
DEFAULT_CONCURRENT_WORKERS = 3


class DownloadService:
    """Handles YouTube content downloads."""

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        history_manager: Optional[HistoryManager] = None,
        info_extractor: Optional[InfoExtractor] = None,
        progress_reporter: Optional[ProgressReporter] = None,
        ffmpeg_service: Optional[FFmpegService] = None,
        timestamp_processor: Optional[TimestampProcessor] = None,
        logger=None
    ):
        """
        Initialize DownloadService.

        Args:
            config_manager: Configuration manager instance
            history_manager: History manager instance
            info_extractor: Info extractor instance
            progress_reporter: Progress reporter instance
            ffmpeg_service: FFmpeg service instance
            timestamp_processor: Timestamp processor instance
            logger: Logger instance
        """
        self._config = config_manager or ConfigManager(logger=logger)
        self._history = history_manager or HistoryManager(logger=logger)
        self._info = info_extractor or InfoExtractor(logger=logger)
        self._progress = progress_reporter or ProgressReporter(logger=logger)
        self._ffmpeg = ffmpeg_service or FFmpegService(logger=logger)
        self._timestamps = timestamp_processor or TimestampProcessor(logger=logger)
        self._logger = logger

    def download_single_video(
        self,
        url: str,
        output_path: str,
        thread_id: int = 0,
        audio_only: bool = False,
        cleaner: Optional['FilenameCleaner'] = None
    ) -> dict:
        """
        Download a single YouTube video, playlist, or channel with retry mechanism.

        Args:
            url: YouTube URL to download
            output_path: Directory to save the download
            thread_id: Thread identifier for logging
            audio_only: If True, download audio only in MP3 format
            cleaner: Optional AI filename cleaner instance

        Returns:
            Result dict with success/failure info
        """
        # Get quality format selector
        if audio_only:
            format_selector = 'bestaudio/best'
            file_extension = 'mp3'
            postprocessors = [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                },
                {
                    'key': 'EmbedThumbnail',
                    'already_have_thumbnail': False
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True
                }
            ]
            print(f"[Thread {thread_id}] Audio-only mode: Downloading highest quality MP3 (320kbps) with album art...")
        else:
            format_selector = (
                'bestvideo[height<=1080]+bestaudio/best[height<=1080]/'
                'best'
            )
            file_extension = 'mp4'
            postprocessors = [
                {
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True
                }
            ]

        # Build downloader options
        downloader_options = {
            'format': format_selector,
            'ignoreerrors': True,
            'no_warnings': False,
            'noplaylist': False,
            'extract_flat': False,
            'progress_hooks': [self._progress.progress_hook],
            'writethumbnail': True,
            'embedthumbnail': True,
            'addmetadata': True,
            'postprocessors': postprocessors,
            'keepvideo': False,
            'clean_infojson': True,
            'retries': MAX_RETRIES,
            'fragment_retries': MAX_RETRIES,
            'compat_opts': ['no-youtube-unavailable-videos'],
            'youtube_include_dash_manifest': False,
            'nocheckcertificate': True,
        }

        if not audio_only:
            downloader_options['merge_output_format'] = 'mp4'

        # Detect content type
        content_type, _ = self._info.get_info(url)

        # Handle AI filename cleaning for single videos
        ai_template_set = False
        use_ai = self._config.use_ai_filename_cleaning and cleaner is not None

        if use_ai and content_type == 'video':
            try:
                metadata_opts = {
                    'quiet': True,
                    'skip_download': True,
                    'no_warnings': True,
                }
                with YoutubeDL(metadata_opts) as ydl:
                    metadata = ydl.extract_info(url, download=False)
                    if metadata and metadata.get('title'):
                        raw_title = metadata.get('title', 'Unknown')
                        cleaned_title = cleaner.clean_title(raw_title)
                        print(f"[Thread {thread_id}] AI cleaned: '{cleaned_title}'")
                        downloader_options['outtmpl'] = os.path.join(output_path, f'{cleaned_title}.{{ext}}')
                        ai_template_set = True
            except Exception as e:
                print(f"[Thread {thread_id}] [WARNING] AI cleaning failed: {e}")

        # Set output template based on content type
        if content_type == 'playlist':
            downloader_options['outtmpl'] = os.path.join(
                output_path, '%(playlist_title)s', f'%(playlist_index)s-%(title)s.{file_extension}')
            print(f"[Thread {thread_id}] Detected playlist URL. Downloading entire playlist...")
            print(f"[Thread {thread_id}] Files will be saved to: {output_path}/[playlist_name]/")
        elif content_type == 'channel':
            downloader_options['outtmpl'] = os.path.join(
                output_path, '%(uploader)s', f'%(upload_date)s-%(title)s.{file_extension}')
            print(f"[Thread {thread_id}] Detected channel URL. Downloading entire channel...")
            print(f"[Thread {thread_id}] Files will be saved to: {output_path}/[channel_name]/")
        elif not ai_template_set:
            downloader_options['outtmpl'] = os.path.join(
                output_path, '%(title)s.{ext}')
            print(f"[Thread {thread_id}] Detected single video URL. Downloading {'audio' if audio_only else 'video'}...")
            print(f"[Thread {thread_id}] File will be saved to: {output_path}/")

        # Download with retry logic
        last_exception = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with YoutubeDL(downloader_options) as ydl:
                    download_result = ydl.extract_info(url, download=True)

                    if download_result is None:
                        return {
                            'url': url,
                            'success': False,
                            'count': 0,
                            'message': f"[ERROR] [Thread {thread_id}] Failed to extract video information. Video may be private or unavailable."
                        }

                    if download_result.get('_type') == 'playlist':
                        title = download_result.get('title', 'Unknown Playlist')
                        video_count = len(download_result.get('entries', []))
                        print(f"[Thread {thread_id}] {content_type.title()}: '{title}' ({video_count} videos)")

                        if video_count == 0:
                            return {
                                'url': url,
                                'success': False,
                                'count': 0,
                                'message': f"[ERROR] [Thread {thread_id}] {content_type.title()} appears to be empty or private"
                            }

                        return {
                            'url': url,
                            'success': True,
                            'count': video_count,
                            'title': title,
                            'type': content_type,
                            'message': f"[OK] [Thread {thread_id}] {content_type.title()} '{title}' download completed! ({video_count} {'MP3s' if audio_only else 'videos'}) Location: {output_path}"
                        }
                    else:
                        title = download_result.get('title', 'Unknown')
                        return {
                            'url': url,
                            'success': True,
                            'count': 1,
                            'title': title,
                            'type': 'video',
                            'message': f"[OK] [Thread {thread_id}] {'Audio' if audio_only else 'Video'} '{title}' download completed! Location: {output_path}"
                        }

            except Exception as error:
                last_exception = error
                if attempt < MAX_RETRIES:
                    retry_delay = RETRY_DELAY * (2 ** (attempt - 1))
                    error_msg = f"[WARNING] [Thread {thread_id}] Attempt {attempt}/{MAX_RETRIES} failed: {str(error)[:100]}. Retrying in {retry_delay}s..."
                    print(error_msg)
                    time.sleep(retry_delay)
                else:
                    return {
                        'url': url,
                        'success': False,
                        'count': 0,
                        'message': f"[ERROR] [Thread {thread_id}] Failed after {MAX_RETRIES} attempts. Last error: {str(last_exception)}"
                    }

        return {
            'url': url,
            'success': False,
            'count': 0,
            'message': f"[ERROR] [Thread {thread_id}] Unexpected error: {str(last_exception)}"
        }

    def download(
        self,
        urls: List[str],
        output_path: Optional[str] = None,
        list_formats: bool = False,
        max_workers: int = DEFAULT_CONCURRENT_WORKERS,
        audio_only: bool = False,
        cleaner: Optional['FilenameCleaner'] = None
    ) -> None:
        """
        Download YouTube content with concurrent downloads.

        Args:
            urls: List of YouTube URLs to download
            output_path: Directory to save downloads
            list_formats: If True, only list available formats
            max_workers: Maximum number of concurrent downloads (1-5)
            audio_only: If True, download audio only in MP3 format
            cleaner: Optional AI filename cleaner instance
        """
        if output_path is None:
            output_path = os.path.join(os.getcwd(), 'downloads')

        if list_formats:
            print("Available formats for the first provided URL:")
            self._list_formats(urls[0])
            return

        os.makedirs(output_path, exist_ok=True)

        print(
            f"\nStarting download of {len(urls)} URL(s) with {max_workers} concurrent workers...")
        print(f"Output directory: {output_path}")
        print(f"Format: {'MP3 Audio Only' if audio_only else 'MP4 Video'}")

        # Count content types
        playlist_count = sum(1 for url in urls if self._info.get_content_type(url) == 'playlist')
        channel_count = sum(1 for url in urls if self._info.get_content_type(url) == 'channel')
        video_count = len(urls) - playlist_count - channel_count

        content_summary = []
        if playlist_count > 0:
            content_summary.append(f"{playlist_count} playlist(s)")
        if channel_count > 0:
            content_summary.append(f"{channel_count} channel(s)")
        if video_count > 0:
            content_summary.append(f"{video_count} video(s)")

        if content_summary:
            print(f"Content: {' + '.join(content_summary)}")
        else:
            print("Content: Unknown content type")

        print("-" * 60)

        # Download with thread pool
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(self.download_single_video, url, output_path, i+1, audio_only, cleaner): url
                for i, url in enumerate(urls)
            }

            for future in as_completed(future_to_url):
                result = future.result()
                results.append(result)
                print(result['message'])

                if result['success']:
                    title = result.get('title', 'Unknown')
                    self._history.add(result['url'], title, output_path)

        # Print summary
        self._print_summary(results, output_path)

    def _list_formats(self, url: str) -> None:
        """List available formats for a URL."""
        ydl_opts = {
            'listformats': True,
            'quiet': False
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
        except Exception as error:
            print(f"Error listing formats: {str(error)}")

    def _print_summary(self, results: List[Dict], output_path: str) -> None:
        """Print download summary."""
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)

        successful_downloads = [r for r in results if r['success']]
        failed_downloads = [r for r in results if not r['success']]

        total_successful_count = sum(r.get('count', 1) for r in successful_downloads)
        total_failed_count = sum(r.get('count', 1) for r in failed_downloads)

        print(f"[OK] Successful downloads: {total_successful_count} {'files' if total_successful_count != 1 else 'file'}")
        print(f"[ERROR] Failed downloads: {total_failed_count} {'files' if total_failed_count != 1 else 'file'}")

        if failed_downloads:
            print("\n[ERROR] Failed URLs:")
            for result in failed_downloads:
                print(f"   * {result['url']}")
                print(f"     Reason: {result['message']}")

        if successful_downloads:
            print(f"\nAll files saved to: {output_path}")


# Convenience functions for backward compatibility
def download_single_video(
    url: str,
    output_path: str,
    thread_id: int = 0,
    audio_only: bool = False,
    cleaner: Optional['FilenameCleaner'] = None
) -> dict:
    """Download single video (legacy function)."""
    service = DownloadService()
    return service.download_single_video(url, output_path, thread_id, audio_only, cleaner)


def download_youtube_content(
    urls: List[str],
    output_path: Optional[str] = None,
    list_formats: bool = False,
    max_workers: int = DEFAULT_CONCURRENT_WORKERS,
    audio_only: bool = False
) -> None:
    """Download YouTube content (legacy function)."""
    service = DownloadService()
    service.download(urls, output_path, list_formats, max_workers, audio_only)


def get_available_formats(url: str) -> None:
    """List available formats (legacy function)."""
    service = DownloadService()
    service._list_formats(url)
