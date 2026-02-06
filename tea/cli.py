"""
CLI interaction and menus for Tea YouTube Downloader.

This module handles all user interface interactions, menus, and input handling.
"""

import sys
import os
import re
from typing import List, Optional, Dict, Any

# Import from tea modules
try:
    from tea.logger import setup_logger
    from tea.config import ConfigManager
    from tea.history import HistoryManager
    from tea.info import InfoExtractor
    from tea.downloader import DownloadService, DEFAULT_CONCURRENT_WORKERS
    from tea.timestamps import TimestampProcessor, time_to_seconds
    from tea.ffmpeg import FFmpegService
except ImportError:
    # Fallback for development
    from tea.logger import setup_logger
    from tea.config import ConfigManager
    from tea.history import HistoryManager
    from tea.info import InfoExtractor
    from tea.downloader import DownloadService, DEFAULT_CONCURRENT_WORKERS
    from tea.timestamps import TimestampProcessor, time_to_seconds
    from tea.ffmpeg import FFmpegService

# Import security utilities
try:
    from tea.utils.security import (
        validate_file_path,
        sanitize_path,
        validate_url,
        validate_choice,
        validate_concurrent_workers
    )
except ImportError:
    # Fallback definitions
    def validate_file_path(filepath, allowed_extensions=None, base_dir=None):
        return os.path.abspath(filepath) if filepath else filepath

    def sanitize_path(path):
        if not path or not isinstance(path, str):
            return ''
        return path.strip().strip('"').strip("'")

    def validate_url(url):
        if not url or not isinstance(url, str):
            return False
        return 'youtube.com' in url or 'youtu.be' in url

    def validate_choice(choice, valid_choices):
        return choice in valid_choices

    def validate_concurrent_workers(value):
        try:
            num = int(value)
            return 1 <= num <= 5
        except (ValueError, TypeError):
            return False

# Try to import AI filename cleaner
FilenameCleaner = None
try:
    from tea.ai.filename_cleaner import FilenameCleaner
except (ImportError, ValueError):
    FilenameCleaner = None


class CLI:
    """Command-line interface for Tea YouTube Downloader."""

    def __init__(self, logger=None):
        """
        Initialize CLI.

        Args:
            logger: Logger instance
        """
        self._logger = logger or setup_logger()
        self._config = ConfigManager(logger=self._logger)
        self._history = HistoryManager(logger=self._logger)
        self._info = InfoExtractor(logger=self._logger)
        self._timestamps = TimestampProcessor(logger=self._logger)
        self._ffmpeg = FFmpegService(logger=self._logger)
        self._downloader = DownloadService(
            config_manager=self._config,
            history_manager=self._history,
            info_extractor=self._info,
            logger=self._logger
        )

    def run(self) -> None:
        """Run the CLI application."""
        if len(sys.argv) > 1:
            self._handle_args()
        else:
            self._interactive_mode()

    def _handle_args(self) -> None:
        """Handle command-line arguments."""
        arg = sys.argv[1]

        if arg == '--help':
            self.show_help()
        elif arg == '--list-formats':
            self._list_formats()
        elif arg == '--batch':
            self._batch_mode()
        elif arg == '--config':
            self._config_mode()
        elif arg == '--history':
            self._history_mode()
        else:
            print(f"[ERROR] Unknown argument: {arg}")
            print("Use 'tea --help' for usage information")

    def _interactive_mode(self) -> None:
        """Run interactive mode."""
        self.show_banner()

        # Get URLs
        url_input = self.get_urls_interactive()

        if not url_input or not url_input.strip():
            print("Multi-line mode")
            print("Enter one URL per line, press Enter twice when finished:")
            urls_list = []
            line_count = 1
            while True:
                line = input(f"   URL {line_count}: ")
                if line.strip() == "":
                    break
                urls_list.append(line)
                line_count += 1
            url_input = '\n'.join(urls_list)

        if not url_input.strip():
            print("No URLs entered. Exiting...")
            return

        urls = self.parse_multiple_urls(url_input)

        if not urls:
            print("No valid YouTube URLs found. Please try again.")
            return

        print()
        print(f"[OK] Found {len(urls)} valid URL(s)")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")

        # Handle duplicates
        urls = self._handle_duplicates(urls)

        if not urls:
            print("\n[ERROR] No videos to download (all were skipped)")
            return

        # Get quality
        audio_only = self._select_quality_audio_only()

        # Get output directory
        output_dir = self._select_output_directory()

        # Get concurrent workers
        max_workers = 1
        if len(urls) > 1:
            max_workers = self._select_concurrent()

        # Handle timestamps for single video
        timestamps = []
        split_enabled = False

        if len(urls) == 1:
            print()
            split_prompt = "Split this video" + (" (audio)" if audio_only else "") + "? (y/n, default=n): "
            split_choice = input(split_prompt).strip().lower()

            if split_choice == 'y':
                timestamps = self._timestamps.get_interactive_timestamps(url=urls[0])

                if timestamps:
                    split_enabled = True
                    print(f"\n[OK] {len(timestamps)} clips will be created after download")
                    for i, ts in enumerate(timestamps[:5], 1):
                        duration_sec = time_to_seconds(ts['end']) - time_to_seconds(ts['start'])
                        print(f"  {i}. {ts['start']} -> {ts['end']} ({duration_sec}s): {ts['title'][:60]}")

                    if len(timestamps) > 5:
                        print(f"  ... and {len(timestamps) - 5} more")

        print()
        print(f"[OK] Brewing {len(urls)} video(s)...")
        print()

        # Initialize AI cleaner if enabled
        cleaner = self._init_ai_cleaner()

        # Download
        final_output_dir = output_dir if output_dir else 'downloads'
        self._downloader.download(
            urls=urls,
            output_path=final_output_dir,
            max_workers=max_workers,
            audio_only=audio_only,
            cleaner=cleaner
        )

        # Handle splitting
        if split_enabled and timestamps:
            self._handle_splitting(final_output_dir, timestamps, audio_only)

    def _handle_duplicates(self, urls: List[str]) -> List[str]:
        """Handle duplicate URL detection."""
        duplicate_action = self._config.duplicate_action
        urls_to_download = []
        skipped_urls = []

        for url in urls:
            already_downloaded, download_info = self._history.is_downloaded(url)

            if already_downloaded and download_info:
                if duplicate_action == 'download':
                    print(f"[INFO] Duplicate: {download_info['title'][:60]} (downloading again)")
                    urls_to_download.append(url)
                elif duplicate_action == 'skip':
                    print(f"[INFO] Duplicate: {download_info['title'][:60]} (skipped)")
                    skipped_urls.append(url)
                else:
                    print(f"\n[WARNING] Duplicate detected!")
                    print(f"   Title: {download_info['title'][:60]}")
                    print(f"   Downloaded: {download_info['timestamp'][:10]}")
                    print(f"   Location: {download_info['output_path']}")
                    print()
                    print("   Choose action:")
                    print("     1. Download again (create new copy)")
                    print("     2. Skip this video")
                    print("     3. Remove from history and download")
                    print("     4. Always download duplicates")
                    print("     5. Always skip duplicates")

                    choice = input("   Enter choice (1-5, default=2): ").strip()

                    if choice == '1':
                        print("   [OK] Downloading again")
                        urls_to_download.append(url)
                    elif choice == '3':
                        print("   [OK] Removing from history...")
                        self._history.remove(url)
                        urls_to_download.append(url)
                    elif choice == '4':
                        self._config.set('duplicate_action', 'download')
                        print("   [OK] Config updated: always download duplicates")
                        urls_to_download.append(url)
                    elif choice == '5':
                        self._config.set('duplicate_action', 'skip')
                        print("   [OK] Config updated: always skip duplicates")
                        skipped_urls.append(url)
                    else:
                        print("   [INFO] Skipped")
                        skipped_urls.append(url)
            else:
                urls_to_download.append(url)

        if skipped_urls:
            print(f"\n[OK] Summary: {len(urls_to_download)} to download, {len(skipped_urls)} skipped")

        return urls_to_download

    def _init_ai_cleaner(self):
        """Initialize AI filename cleaner if enabled."""
        if not self._config.use_ai_filename_cleaning or not FilenameCleaner:
            return None

        api_key = self._config.openrouter_api_key
        if not api_key:
            return None

        try:
            cleaner = FilenameCleaner(api_key=api_key)
            remaining = cleaner.get_remaining_requests()
            print(f"[INFO] AI filename cleaning enabled ({remaining}/50 requests remaining today)")
            return cleaner
        except Exception as e:
            print(f"[WARNING] Failed to initialize AI cleaner: {e}")
            return None

    def _handle_splitting(self, output_dir: str, timestamps: List[Dict], audio_only: bool) -> None:
        """Handle video/audio splitting after download."""
        content_type = "audio" if audio_only else "video"
        print(f"\n{'=' * 60}")
        print(f"[OK] Starting {content_type} splitting...")
        print("-" * 60)

        media_file = self._ffmpeg.find_downloaded_video(output_dir, "")

        if media_file:
            print(f"[OK] Found {content_type}: {os.path.basename(media_file)}")

            clips_dir = os.path.join(os.path.dirname(media_file), 'clips')

            split_results = self._ffmpeg.split_video_by_timestamps(
                media_file, timestamps, clips_dir, audio_only
            )

            successful_clips = [r for r in split_results if r['success']]
            failed_clips = [r for r in split_results if not r['success']]

            print("\n" + "-" * 60)
            print("SPLIT SUMMARY")
            print("-" * 60)
            print(f"[OK] Successful clips: {len(successful_clips)}")
            print(f"[ERROR] Failed clips: {len(failed_clips)}")

            if successful_clips:
                print(f"\n[OK] Clips saved to: {clips_dir}")

            if failed_clips:
                print("\n[ERROR] Failed clips:")
                for clip in failed_clips:
                    print(f"  {clip['clip']}. {clip['title']}")
        else:
            print(f"[ERROR] Could not find downloaded {content_type} for splitting")

    # Banner and help methods

    def show_banner(self) -> None:
        """Display beautiful Tea banner."""
        print()
        print("   +-------------------------------+")
        print("   |                               |")
        print("   |       Tea v1.0.0              |")
        print("   |       YouTube Downloader      |")
        print("   |                               |")
        print("   +-------------------------------+")
        print()
        print("-" * 60)
        print("  Tea - Brew your favorite videos")
        print("-" * 60)
        print()

    def show_help(self) -> None:
        """Show Tea help menu."""
        print("\n[OK] Tea - YouTube Downloader")
        print("-" * 60)
        print("\nUsage:")
        print("  tea                    # Interactive mode")
        print("  tea --batch <file>     # Batch download from file")
        print("  tea --config           # Update configuration")
        print("  tea --history          # Show download history")
        print("  tea --list-formats     # List available video formats")
        print("  tea --help             # Show this help")
        print("\nExamples:")
        print("  tea")
        print("  tea --batch urls.txt")
        print("  tea --config")
        print()

    def show_supported_formats(self) -> None:
        """Show supported URL formats."""
        print("SUPPORTED INPUT FORMATS:")
        print("   - Single URL: Just paste one YouTube URL")
        print("   - Comma-separated: url1, url2, url3")
        print("   - Space-separated: url1 url2 url3")
        print("   - Multi-line: Press Enter without typing, then one URL per line")
        print()
        print("SUPPORTED CONTENT TYPES:")
        print("   Videos: https://www.youtube.com/watch?v=...")
        print("   Shorts: https://www.youtube.com/shorts/...")
        print("   Playlists: https://www.youtube.com/playlist?list=...")
        print("   Channels: https://www.youtube.com/@channelname")
        print("   Channels: https://www.youtube.com/channel/UC...")
        print("   Channels: https://www.youtube.com/c/channelname")
        print("   Channels: https://www.youtube.com/user/username")
        print()

    # Input methods

    def get_urls_interactive(self) -> str:
        """Get YouTube URLs with interactive prompt."""
        print("Example URLs:")
        print("   * https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        print("   * https://youtu.be/dQw4w9WgXcQ")
        print("   * https://www.youtube.com/playlist?list=PLxxxxxx")
        print()

        url_input = input("Enter YouTube URL(s): ")
        return url_input

    def parse_multiple_urls(self, input_string: str) -> List[str]:
        """Parse multiple URLs from input string."""
        if not input_string or not isinstance(input_string, str):
            return []

        urls = re.split(r'[,\s\n\t]+', input_string.strip())
        urls = [url.strip() for url in urls if url.strip()]

        valid_urls = []
        invalid_count = 0
        for url in urls:
            if validate_url(url):
                valid_urls.append(url)
            elif url:
                print(f"[WARNING] Skipping invalid or non-YouTube URL")
                invalid_count += 1

        if invalid_count > 0:
            print(f"Found {len(valid_urls)} valid YouTube URLs, skipped {invalid_count} invalid entries")

        return valid_urls

    # Selection methods

    def _select_quality_audio_only(self) -> bool:
        """Select quality and return whether audio-only was chosen."""
        print("Select video quality:")
        print("   1. Best available (1080p)")
        print("   2. High (720p)")
        print("   3. Medium (480p)")
        print("   4. Low (360p)")
        print("   5. Audio only (MP3)")

        while True:
            choice = input("Enter choice (1-5, default=1): ").strip()

            if not choice:
                return False

            if validate_choice(choice, ['1', '2', '3', '4', '5']):
                if choice == '5':
                    print("Selected: Audio only (MP3)")
                    return True
                else:
                    quality_labels = {
                        '1': 'Best available (1080p)',
                        '2': 'High (720p)',
                        '3': 'Medium (480p)',
                        '4': 'Low (360p)'
                    }
                    print(f"Selected: {quality_labels.get(choice, 'Best')}")
                    return False
            else:
                print("[WARNING] Invalid choice. Please enter 1-5")

        return False

    def select_quality(self) -> str:
        """Interactive quality selection."""
        print("Select video quality:")
        print("   1. Best available (1080p)")
        print("   2. High (720p)")
        print("   3. Medium (480p)")
        print("   4. Low (360p)")
        print("   5. Audio only (MP3)")

        while True:
            choice = input("Enter choice (1-5, default=1): ").strip()

            if not choice:
                return 'best'

            if validate_choice(choice, ['1', '2', '3', '4', '5']):
                quality_map = {
                    '1': 'best',
                    '2': '720p',
                    '3': '480p',
                    '4': '360p',
                    '5': 'audio'
                }
                return quality_map.get(choice, 'best')
            else:
                print("[WARNING] Invalid choice. Please enter 1-5")

        return 'best'

    def _select_output_directory(self) -> str:
        """Select output directory."""
        output = input("Output directory (press Enter for default): ").strip()
        safe_output = sanitize_path(output)
        return safe_output if safe_output else 'downloads'

    def select_output_directory(self) -> str:
        """Select output directory."""
        return self._select_output_directory()

    def _select_concurrent(self) -> int:
        """Select number of concurrent downloads."""
        while True:
            workers = input("Concurrent downloads (1-5, default=3): ").strip()

            if not workers:
                return 3

            if validate_concurrent_workers(workers):
                return int(workers)
            else:
                print("[WARNING] Please enter a number between 1 and 5")

        return 3

    def select_concurrent(self) -> int:
        """Select number of concurrent downloads."""
        return self._select_concurrent()

    # File loading

    def load_urls_from_file(self, filepath: str) -> List[str]:
        """Load URLs from a text file."""
        try:
            validated_path = validate_file_path(filepath, allowed_extensions=['.txt', '.list'])

            if not os.path.exists(validated_path):
                print("[ERROR] File not found")
                return []

            if not os.path.isfile(validated_path):
                print("[ERROR] Path is not a file")
                return []

            with open(validated_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            urls = []
            for line in lines:
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                if validate_url(line):
                    urls.append(line)
                else:
                    print(f"[WARNING] Skipping invalid URL: {line[:50]}...")

            print(f"[OK] Loaded {len(urls)} valid URLs from file")
            return urls

        except Exception as e:
            print(f"[ERROR] Error reading file")
            return []

    # Command handlers

    def _batch_mode(self) -> None:
        """Handle batch download mode."""
        if len(sys.argv) < 3:
            print("[ERROR] Usage: tea --batch <file.txt>")
            return

        batch_file = sys.argv[2]
        self.show_banner()

        urls = self.load_urls_from_file(batch_file)

        if not urls:
            print("[ERROR] No valid URLs found in file")
            return

        print(f"\n[OK] Batch mode: {len(urls)} URLs loaded")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")

        audio_only = self._select_quality_audio_only()
        output_dir = self._select_output_directory()

        max_workers = 1
        if len(urls) > 1:
            max_workers = self._select_concurrent()

        print(f"\n[OK] Brewing {len(urls)} video(s)...")

        cleaner = self._init_ai_cleaner()

        if output_dir:
            self._downloader.download(urls, output_dir, max_workers=max_workers, audio_only=audio_only, cleaner=cleaner)
        else:
            self._downloader.download(urls, max_workers=max_workers, audio_only=audio_only, cleaner=cleaner)

    def _config_mode(self) -> None:
        """Handle configuration mode."""
        print("\n[OK] Tea Configuration")
        print("-" * 60)
        print(f"Current settings:")
        print(f"  1. Default quality: {self._config.default_quality}")
        print(f"  2. Default output: {self._config.default_output}")
        print(f"  3. Concurrent downloads: {self._config.concurrent_downloads}")
        print(f"  4. MP3 quality: {self._config.mp3_quality}kbps")
        print(f"  5. AI filename cleaning: {self._config.use_ai_filename_cleaning}")
        if self._config.use_ai_filename_cleaning:
            api_key_status = 'Set' if self._config.openrouter_api_key else 'Not set'
            print(f"  6. OpenRouter API key: {api_key_status}")

        update = input("\nUpdate settings? (y/n, default=n): ").strip().lower()

        if update == 'y':
            quality = input(f"Default quality (1-5, current={self._config.default_quality}): ").strip()
            if quality:
                self._config.set('default_quality', quality, auto_save=False)

            output = input(f"Default output directory (current={self._config.default_output}): ").strip()
            if output:
                self._config.set('default_output', output, auto_save=False)

            concurrent = input(f"Concurrent downloads (1-5, current={self._config.concurrent_downloads}): ").strip()
            if concurrent:
                self._config.set('concurrent_downloads', int(concurrent), auto_save=False)

            ai_cleaning = input("Enable AI filename cleaning (y/n): ").strip().lower()
            if ai_cleaning == 'y':
                self._config.set('use_ai_filename_cleaning', True, auto_save=False)
                if not self._config.openrouter_api_key:
                    api_key = input("Enter OpenRouter API key (free at https://openrouter.ai): ").strip()
                    if api_key:
                        self._config.set('openrouter_api_key', api_key, auto_save=False)
            else:
                self._config.set('use_ai_filename_cleaning', False, auto_save=False)

            self._config.save()

    def _history_mode(self) -> None:
        """Handle history mode."""
        self._history.show()

    def _list_formats(self) -> None:
        """Handle list formats mode."""
        url = input("Enter the YouTube URL to list formats: ")
        self._downloader._list_formats(url)


# Convenience functions for backward compatibility
def show_banner():
    """Show banner (legacy function)."""
    cli = CLI()
    cli.show_banner()


def show_help():
    """Show help (legacy function)."""
    cli = CLI()
    cli.show_help()


def show_supported_formats():
    """Show supported formats (legacy function)."""
    cli = CLI()
    cli.show_supported_formats()


def get_urls_interactive() -> str:
    """Get URLs interactively (legacy function)."""
    cli = CLI()
    return cli.get_urls_interactive()


def select_quality() -> str:
    """Select quality (legacy function)."""
    cli = CLI()
    return cli.select_quality()


def select_output_directory() -> str:
    """Select output directory (legacy function)."""
    cli = CLI()
    return cli.select_output_directory()


def select_concurrent() -> int:
    """Select concurrent workers (legacy function)."""
    cli = CLI()
    return cli.select_concurrent()


def load_urls_from_file(filepath: str) -> List[str]:
    """Load URLs from file (legacy function)."""
    cli = CLI()
    return cli.load_urls_from_file(filepath)


def parse_multiple_urls(input_string: str) -> List[str]:
    """Parse multiple URLs (legacy function)."""
    cli = CLI()
    return cli.parse_multiple_urls(input_string)
