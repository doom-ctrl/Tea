"""
FFmpeg operations for Tea YouTube Downloader.

This module handles video/audio splitting and file operations using FFmpeg.
"""

import os
import subprocess
from typing import List, Dict, Optional
from datetime import datetime

# Import security utilities
try:
    from tea.utils.security import (
        validate_file_path,
        sanitize_path,
        sanitize_metadata,
        sanitize_clip_title,
        validate_timestamp,
        SecurityValidationError
    )
except ImportError:
    # Fallback definitions
    def validate_file_path(filepath, allowed_extensions=None, base_dir=None):
        return os.path.abspath(filepath) if filepath else filepath

    def sanitize_path(path):
        if not path or not isinstance(path, str):
            return ''
        return path.strip().strip('"').strip("'")

    def sanitize_metadata(value):
        if not value or not isinstance(value, str):
            return ''
        return value[:200]

    def sanitize_clip_title(title):
        if not title or not isinstance(title, str):
            return 'Untitled'
        import re
        return re.sub(r'[<>:"/\\|?*&]', '_', title.strip())[:100]

    def validate_timestamp(timestamp):
        if not timestamp or not isinstance(timestamp, str):
            return False
        import re
        return bool(re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', timestamp.strip()))

    class SecurityValidationError(Exception):
        pass


class FFmpegService:
    """Handles FFmpeg operations for video/audio processing."""

    def __init__(self, logger=None):
        """
        Initialize FFmpegService.

        Args:
            logger: Logger instance for logging
        """
        self._logger = logger

    def _check_ffmpeg(self) -> bool:
        """
        Check if FFmpeg is available.

        Returns:
            True if FFmpeg is found
        """
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def split_video_by_timestamps(
        self,
        video_path: str,
        timestamps: List[Dict],
        output_dir: str,
        audio_only: bool = False,
        video_title: str = ""
    ) -> List[Dict]:
        """
        Split a video file into multiple clips based on timestamps.

        Args:
            video_path: Path to source video/audio file
            timestamps: List of timestamp dicts with 'start', 'end', 'title'
            output_dir: Directory for output clips
            audio_only: True for audio-only splitting (MP3)
            video_title: Original video title for metadata

        Returns:
            List of results dicts with 'success', 'clip', 'title', 'path' or 'error'
        """
        results = []

        # Check FFmpeg availability
        if not self._check_ffmpeg():
            print("[ERROR] FFmpeg not found. Install from: https://ffmpeg.org/")
            return []

        # Sanitize output directory path
        safe_output_dir = sanitize_path(output_dir)
        if not safe_output_dir:
            safe_output_dir = 'downloads'

        try:
            os.makedirs(safe_output_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            if self._logger:
                self._logger.error(f"Cannot create output directory: {e}")
            print(f"[ERROR] Cannot create output directory: {e}")
            return []

        total_clips = len(timestamps)
        print(f"\n[OK] Splitting into {total_clips} clips...")
        print("-" * 60)

        for i, timestamp in enumerate(timestamps, 1):
            start = timestamp['start']
            end = timestamp['end']
            raw_title = timestamp.get('title', f'Clip {i}')

            # Validate timestamps
            if not validate_timestamp(start) or not validate_timestamp(end):
                print(f"[WARNING] Clip {i}: Invalid timestamp format, skipping")
                results.append({
                    'success': False,
                    'clip': i,
                    'title': raw_title,
                    'error': 'Invalid timestamp format'
                })
                continue

            # Sanitize title for safe use in filenames and metadata
            safe_title = sanitize_clip_title(raw_title)
            safe_metadata_title = sanitize_metadata(raw_title)
            safe_video_title = sanitize_metadata(video_title) if video_title else "Tea Playlist"

            # Build safe output path
            if audio_only:
                output_path = os.path.join(safe_output_dir, f"{i:02d}-{safe_title}.mp3")
            else:
                _, ext = os.path.splitext(video_path)
                output_path = os.path.join(safe_output_dir, f"{i:02d}-{safe_title}{ext}")

            print(f"[OK] Clip {i}/{total_clips}: {safe_title}")
            print(f"   Time: {start} -> {end}")

            try:
                result = self._execute_split(
                    video_path=video_path,
                    output_path=output_path,
                    start=start,
                    end=end,
                    audio_only=audio_only,
                    metadata_title=safe_metadata_title,
                    video_title=safe_video_title,
                    clip_num=i,
                    total_clips=total_clips
                )

                results.append({
                    'success': True,
                    'clip': i,
                    'title': safe_title,
                    'path': output_path
                })
                print(f"   [OK] Saved to: {os.path.basename(output_path)}")

            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if e.stderr else str(e)
                safe_error = error_msg[:100] if error_msg else "Unknown error"
                results.append({
                    'success': False,
                    'clip': i,
                    'title': safe_title,
                    'error': safe_error
                })
                print(f"   [ERROR] Failed to process clip")

            except Exception as e:
                results.append({
                    'success': False,
                    'clip': i,
                    'title': safe_title,
                    'error': 'Processing error'
                })
                print(f"   [ERROR] Failed to process clip")

        return results

    def _execute_split(
        self,
        video_path: str,
        output_path: str,
        start: str,
        end: str,
        audio_only: bool,
        metadata_title: str,
        video_title: str,
        clip_num: int,
        total_clips: int
    ) -> subprocess.CompletedProcess:
        """Execute the FFmpeg split command."""
        if audio_only:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', start,
                '-to', end,
                '-vn',
                '-acodec', 'libmp3lame',
                '-q:a', '2',
                '-avoid_negative_ts', '1',
                '-metadata', f'title={metadata_title}',
                '-metadata', f'track={clip_num}/{total_clips}',
                '-metadata', f'album={video_title}',
                '-metadata', f'date={datetime.now().year}',
                '-y',
                output_path
            ]
        else:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', start,
                '-to', end,
                '-c', 'copy',
                '-avoid_negative_ts', '1',
                '-metadata', f'title={metadata_title}',
                '-metadata', f'track={clip_num}/{total_clips}',
                '-y',
                output_path
            ]

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

    def find_downloaded_video(
        self,
        output_path: str,
        title: str = ""
    ) -> Optional[str]:
        """
        Find the downloaded video or audio file by title.

        Args:
            output_path: Directory to search
            title: Video title to match (optional)

        Returns:
            Path to found file or None
        """
        extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mp3']

        # Sanitize the output path
        safe_output_path = sanitize_path(output_path)
        if not safe_output_path:
            return None

        try:
            # Check directory exists and is accessible
            if not os.path.exists(safe_output_path):
                return None

            if not os.path.isdir(safe_output_path):
                return None

            # First pass: try to match by title
            if title:
                title_words = [
                    sanitize_path(word).lower()
                    for word in str(title).split()[:3]
                    if word
                ]
                title_words = [w for w in title_words if w]

                if title_words:
                    for ext in extensions:
                        for filename in os.listdir(safe_output_path):
                            if filename.endswith(ext):
                                if any(word in filename.lower() for word in title_words):
                                    return os.path.join(safe_output_path, filename)

            # Second pass: return any matching file
            for ext in extensions:
                for filename in os.listdir(safe_output_path):
                    if filename.endswith(ext):
                        return os.path.join(safe_output_path, filename)

        except (PermissionError, OSError, Exception):
            # Silently handle errors
            pass

        return None


# Convenience functions for backward compatibility
def split_video_by_timestamps(
    video_path: str,
    timestamps: List[Dict],
    output_dir: str,
    audio_only: bool = False,
    video_title: str = ""
) -> List[Dict]:
    """Split video by timestamps (legacy function)."""
    service = FFmpegService()
    return service.split_video_by_timestamps(
        video_path, timestamps, output_dir, audio_only, video_title
    )


def find_downloaded_video(output_path: str, title: str = "") -> Optional[str]:
    """Find downloaded video file (legacy function)."""
    service = FFmpegService()
    return service.find_downloaded_video(output_path, title)
