"""
Timestamp processing for Tea YouTube Downloader.

This module handles parsing, loading, and processing timestamps for video splitting.
"""

import re
import json
import os
from typing import List, Dict, Optional
from yt_dlp import YoutubeDL

# Import security utilities
try:
    from tea.utils.security import (
        validate_file_path,
        sanitize_clip_title,
        validate_timestamp,
        validate_choice,
        SecurityValidationError
    )
except ImportError:
    # Fallback definitions
    def validate_file_path(filepath, allowed_extensions=None, base_dir=None):
        return os.path.abspath(filepath) if filepath else filepath

    def sanitize_clip_title(title):
        if not title or not isinstance(title, str):
            return 'Untitled'
        return re.sub(r'[<>:"/\\|?*&]', '_', title.strip())[:100]

    def validate_timestamp(timestamp):
        if not timestamp or not isinstance(timestamp, str):
            return False
        return bool(re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', timestamp.strip()))

    def validate_choice(choice, valid_choices):
        return choice in valid_choices

    class SecurityValidationError(Exception):
        pass


class TimestampProcessor:
    """Processes timestamps for video splitting."""

    def __init__(self, logger=None):
        """
        Initialize TimestampProcessor.

        Args:
            logger: Logger instance for logging
        """
        self._logger = logger

    def time_to_seconds(self, timestamp: str) -> int:
        """
        Convert MM:SS or HH:MM:SS to seconds.

        Args:
            timestamp: Timestamp string

        Returns:
            Time in seconds
        """
        parts = timestamp.strip().split(':')
        try:
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            return 0
        return 0

    def format_time(self, seconds: float) -> str:
        """
        Format seconds to MM:SS or HH:MM:SS.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
        if seconds < 0:
            seconds = 0

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def parse_timestamp_list(self, text: str, video_duration: Optional[str] = None) -> List[Dict]:
        """
        Parse timestamps from various formats.

        Args:
            text: Text containing timestamps
            video_duration: Optional video duration for end times

        Returns:
            List of timestamp dicts with 'start', 'end', 'title'
        """
        timestamps = []

        if '-' in text and (',' in text or '\n' not in text):
            # Range format: 0:00-5:30, 5:30-10:00
            parts = re.split(r',|\n', text)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                match = re.search(r'(\d+:\d+(?::\d+)?)\s*-\s*(\d+:\d+(?::\d+)?)\s*(.*)?', part)
                if match:
                    timestamps.append({
                        'start': match.group(1),
                        'end': match.group(2),
                        'title': match.group(3).strip() if match.group(3) else f"Clip {len(timestamps)+1}"
                    })
        else:
            # YouTube style: One timestamp per line (0:00 Intro)
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

            for i, line in enumerate(lines):
                match = re.search(r'(\d+:\d+(?::\d+)?)\s+(.+)', line)
                if match:
                    start = match.group(1)
                    title = match.group(2).strip()

                    end = None
                    if i + 1 < len(lines):
                        next_match = re.search(r'(\d+:\d+(?::\d+)?)', lines[i + 1])
                        if next_match:
                            end = next_match.group(1)
                    elif video_duration:
                        end = video_duration

                    if end:
                        timestamps.append({
                            'start': start,
                            'end': end,
                            'title': title
                        })

        return timestamps

    def load_from_json(self, filepath: str) -> List[Dict]:
        """
        Load timestamps from a JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            List of timestamp dicts
        """
        try:
            validated_path = validate_file_path(
                filepath,
                allowed_extensions=['.json']
            )

            if not os.path.exists(validated_path):
                print("[ERROR] File not found")
                return []

            if not os.path.isfile(validated_path):
                print("[ERROR] Path is not a file")
                return []

            with open(validated_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, dict) and 'clips' in data:
                clips = data['clips']
            elif isinstance(data, list):
                clips = data
            else:
                print("[ERROR] Invalid JSON format")
                return []

            timestamps = []
            for i, clip in enumerate(clips, 1):
                if 'start' in clip and 'end' in clip:
                    start = str(clip['start']).strip()
                    end = str(clip['end']).strip()

                    if not validate_timestamp(start) or not validate_timestamp(end):
                        print(f"[WARNING] Skipping clip {i}: Invalid timestamp format")
                        continue

                    raw_title = clip.get('title', f'Clip {i}')
                    title = sanitize_clip_title(str(raw_title))

                    timestamps.append({
                        'start': start,
                        'end': end,
                        'title': title
                    })
                else:
                    print(f"[WARNING] Skipping clip {i}: Missing 'start' or 'end'")

            print(f"[OK] Loaded {len(timestamps)} clips from JSON file")
            return timestamps

        except SecurityValidationError as e:
            print(f"[ERROR] Security validation failed: {e}")
            return []
        except FileNotFoundError:
            print("[ERROR] File not found")
            return []
        except json.JSONDecodeError:
            print("[ERROR] Invalid JSON format")
            return []
        except Exception as e:
            print(f"[ERROR] Error loading file: {e}")
            return []

    def extract_youtube_chapters(self, url: str) -> List[Dict]:
        """
        Extract timestamps from YouTube's auto-chapters or description.

        Args:
            url: YouTube video URL

        Returns:
            List of timestamp dicts
        """
        print("\n[OK] Checking for YouTube chapters...")

        ydl_opts = {
            'quiet': True,
            'extract_flat': False,
            'skip_download': True,
            'no_warnings': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if not info:
                    print("[ERROR] Could not fetch video information")
                    return []

                chapters = info.get('chapters') or []
                if chapters:
                    print(f"[OK] Found {len(chapters)} YouTube chapters!")

                    timestamps = []
                    for chapter in chapters:
                        timestamps.append({
                            'start': self.format_time(chapter['start_time']),
                            'end': self.format_time(chapter['end_time']),
                            'title': chapter['title']
                        })

                    return timestamps

                description = info.get('description', '')
                duration = info.get('duration', 0)

                if description and duration:
                    print("[INFO] Searching video description for timestamps...")
                    parsed = self.parse_description_timestamps(description, duration)

                    if parsed:
                        print(f"[OK] Found {len(parsed)} timestamps in description!")
                        return parsed

                print("[INFO] No chapters or timestamps found in this video")
                return []

        except Exception as e:
            print(f"[ERROR] Error extracting chapters: {e}")
            return []

    def parse_description_timestamps(self, description: str, video_duration: float) -> List[Dict]:
        """
        Parse timestamps from video description.

        Args:
            description: Video description text
            video_duration: Total video duration in seconds

        Returns:
            List of timestamp dicts
        """
        timestamps = []
        lines = description.split('\n')

        patterns = [
            r'(\d+:\d+(?::\d+)?)\s*[-–—]\s*(.+)',
            r'\[(\d+:\d+(?::\d+)?)\]\s*(.+)',
            r'\((\d+:\d+(?::\d+)?)\)\s*(.+)',
            r'(\d+:\d+(?::\d+)?)\s+(.+)',
        ]

        for line in lines:
            line = line.strip()

            if not line or len(line) < 5:
                continue

            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    time_str = match.group(1).strip()
                    title = match.group(2).strip()

                    if len(title) < 2 or title.lower().startswith(('http', 'www', 'channel')):
                        continue

                    time_parts = time_str.split(':')
                    try:
                        if len(time_parts) == 2:
                            seconds = int(time_parts[0]) * 60 + int(time_parts[1])
                        elif len(time_parts) == 3:
                            seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
                        else:
                            continue

                        if seconds > video_duration:
                            continue

                        timestamps.append({
                            'time': seconds,
                            'time_str': time_str,
                            'title': title[:100]
                        })
                        break

                    except (ValueError, IndexError):
                        continue

        if not timestamps:
            return []

        timestamps.sort(key=lambda x: x['time'])

        seen_times = set()
        unique_timestamps = []
        for ts in timestamps:
            if ts['time'] not in seen_times:
                seen_times.add(ts['time'])
                unique_timestamps.append(ts)

        result = []
        for i, ts in enumerate(unique_timestamps):
            if i + 1 < len(unique_timestamps):
                end_time = unique_timestamps[i + 1]['time']
            else:
                end_time = video_duration

            result.append({
                'start': ts['time_str'],
                'end': self.format_time(end_time),
                'title': ts['title']
            })

        return result

    def get_interactive_timestamps(self, url: str = "") -> List[Dict]:
        """
        Get timestamps interactively from user with auto-detection support.

        Args:
            url: YouTube URL for auto-detection (optional)

        Returns:
            List of timestamp dicts
        """
        print("\n=== Enter timestamps to split the video")
        print("-" * 60)
        print("Supported formats:")
        print("   * Range: 0:00-5:30, 5:30-10:00")
        print("   * YouTube style: One timestamp per line (0:00 Intro)")
        print("   * JSON file: Load from timestamps.json")
        print("   * YouTube Auto-Chapters: Extract from video")
        print()
        print("Choose input method:")
        print("   1. Manual entry (one by one)")
        print("   2. Paste timestamp list")
        print("   3. Load from JSON file")

        if url:
            print("   4. Auto-detect from YouTube")
            print("   5. Skip splitting")
            valid_choices = ['1', '2', '3', '4', '5']
            default = "5"
        else:
            print("   4. Skip splitting")
            valid_choices = ['1', '2', '3', '4']
            default = "4"

        print()

        choice = input(f"Enter choice (1-{'5' if url else '4'}, default={default}): ").strip()

        if not choice:
            choice = default

        if not validate_choice(choice, valid_choices):
            print("[WARNING] Invalid choice. Skipping timestamp splitting.")
            return []

        if url and choice == '4':
            timestamps = self.extract_youtube_chapters(url)

            if timestamps:
                print("\n[OK] Preview of detected timestamps:")
                print("-" * 60)

                for i, ts in enumerate(timestamps[:10], 1):
                    duration_sec = self.time_to_seconds(ts['end']) - self.time_to_seconds(ts['start'])
                    print(f"  {i}. {ts['start']} -> {ts['end']} ({duration_sec}s): {ts['title'][:50]}")

                if len(timestamps) > 10:
                    print(f"  ... and {len(timestamps) - 10} more")

                print("-" * 60)
                print(f"[OK] Total: {len(timestamps)} chapters detected")
                print()

                use_these = input("Use these timestamps? (y/n, default=y): ").strip().lower()
                if use_these != 'n':
                    return timestamps
                else:
                    print("[INFO] Auto-detection cancelled")
                    return []
            else:
                print("\n[INFO] Tip: Try manual entry or paste timestamps")
                return []

        if (choice == '5' and url) or (choice == '4' and not url) or choice not in ['1', '2', '3']:
            return []

        timestamps = []

        if choice == '1':
            timestamps = self._get_manual_timestamps()
        elif choice == '2':
            timestamps = self._get_pasted_timestamps()
        elif choice == '3':
            timestamps = self._get_json_timestamps()

        return timestamps

    def _get_manual_timestamps(self) -> List[Dict]:
        """Get timestamps through manual entry."""
        print("\nEnter timestamps (press Enter without typing to finish)")
        print("-" * 60)
        timestamps = []
        clip_num = 1

        while True:
            print(f"\nClip {clip_num}:")
            start = input("  Start time (MM:SS or HH:MM:SS): ").strip()
            if not start:
                break

            if not validate_timestamp(start):
                print("  [ERROR] Invalid timestamp format. Use MM:SS or HH:MM:SS")
                continue

            end = input("  End time: ").strip()
            if not end:
                print("  End time required. Clip skipped.")
                continue

            if not validate_timestamp(end):
                print("  [ERROR] Invalid timestamp format. Use MM:SS or HH:MM:SS")
                continue

            title = input("  Title (optional, press Enter to skip): ").strip()
            if not title:
                title = f"Clip {clip_num}"

            title = sanitize_clip_title(title)

            timestamps.append({
                'start': start,
                'end': end,
                'title': title
            })

            print(f"  Added: {start} - {end} | {title}")
            clip_num += 1

        return timestamps

    def _get_pasted_timestamps(self) -> List[Dict]:
        """Get timestamps by pasting a list."""
        print("\nPaste your timestamps below")
        print("Examples:")
        print("   * 0:00-1:54, 1:54-5:46, 5:46-8:33")
        print("   * 0:00 Intro")
        print("     1:54 Main Content")
        print("     5:46 Conclusion")
        print()
        print("Press Enter twice when finished:")
        print("-" * 60)

        lines = []
        empty_count = 0
        while True:
            line = input()
            if not line.strip():
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)

        if lines:
            return self.parse_timestamp_list('\n'.join(lines))

        return []

    def _get_json_timestamps(self) -> List[Dict]:
        """Get timestamps from JSON file."""
        print("\nEnter path to JSON file:")
        print("   Example: timestamps.json or C:\\path\\to\\timestamps.json")
        print()
        filepath = input("File path: ").strip()
        filepath = filepath.strip('"').strip("'")

        return self.load_from_json(filepath)


# Convenience functions for backward compatibility
def time_to_seconds(timestamp: str) -> int:
    """Convert timestamp to seconds (legacy function)."""
    processor = TimestampProcessor()
    return processor.time_to_seconds(timestamp)


def format_time(seconds: float) -> str:
    """Format seconds to timestamp (legacy function)."""
    processor = TimestampProcessor()
    return processor.format_time(seconds)


def parse_timestamp_list(text: str, video_duration: Optional[str] = None) -> List[Dict]:
    """Parse timestamp list (legacy function)."""
    processor = TimestampProcessor()
    return processor.parse_timestamp_list(text, video_duration)


def load_timestamps_from_json(filepath: str) -> List[Dict]:
    """Load timestamps from JSON (legacy function)."""
    processor = TimestampProcessor()
    return processor.load_from_json(filepath)


def extract_youtube_chapters(url: str) -> List[Dict]:
    """Extract YouTube chapters (legacy function)."""
    processor = TimestampProcessor()
    return processor.extract_youtube_chapters(url)


def parse_description_timestamps(description: str, video_duration: float) -> List[Dict]:
    """Parse description timestamps (legacy function)."""
    processor = TimestampProcessor()
    return processor.parse_description_timestamps(description, video_duration)


def get_timestamps_interactive(url: str = "") -> List[Dict]:
    """Get timestamps interactively (legacy function)."""
    processor = TimestampProcessor()
    return processor.get_interactive_timestamps(url)
