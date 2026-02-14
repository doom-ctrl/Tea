"""
Centralized constants for Tea YouTube Downloader.

This module contains all application-wide constants to avoid magic numbers
and hardcoded values scattered across modules.
"""

from typing import Dict, List, Set

# =============================================================================
# Application Metadata
# =============================================================================

__version__ = "1.0.0"
__author__ = "Tea Contributors"
__license__ = "MIT"

# =============================================================================
# Retry Configuration
# =============================================================================

MAX_RETRIES = 3
"""Maximum number of retry attempts for failed downloads."""

RETRY_DELAY = 2
"""Base delay in seconds between retries (exponential backoff)."""

MAX_CONCURRENT_WORKERS = 5
"""Maximum number of concurrent download workers allowed."""

DEFAULT_CONCURRENT_WORKERS = 3
"""Default number of concurrent download workers."""

# =============================================================================
# File Extensions
# =============================================================================

VALID_VIDEO_EXTENSIONS: Set[str] = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv"}
"""Valid video file extensions."""

VALID_AUDIO_EXTENSIONS: Set[str] = {".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg"}
"""Valid audio file extensions."""

VALID_FORMAT_EXTENSIONS: Set[str] = VALID_VIDEO_EXTENSIONS | VALID_AUDIO_EXTENSIONS
"""All valid media file extensions."""

# =============================================================================
# Quality Presets
# =============================================================================

QUALITY_PRESETS: Dict[str, str] = {
    "best": "bestvideo+bestaudio/best",
    "1": "bestvideo+bestaudio/best",
    "2": "bestvideo[height<=1080]+bestaudio/best",
    "3": "bestvideo[height<=720]+bestaudio/best",
    "4": "bestvideo[height<=480]+bestaudio/best",
    "5": "bestaudio/best",  # Audio only
    "audio": "bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best",
    "720p": "bestvideo[height<=720]+bestaudio/best",
    "480p": "bestvideo[height<=480]+bestaudio/best",
    "360p": "bestvideo[height<=360]+bestaudio/best",
}
"""Mapping of quality preset names to yt-dlp format selectors."""

AUDIO_QUALITY_PRESETS: Dict[str, str] = {
    "low": "128",
    "medium": "192",
    "high": "256",
    "max": "320",
}
"""Audio quality presets in kbps."""

VALID_QUALITIES: Set[str] = {
    "1", "2", "3", "4", "5",
    "best", "audio",
    "1080p", "720p", "480p", "360p",
}
"""Valid quality preset names."""

VALID_MP3_QUALITIES: Set[str] = {"128", "192", "256", "320"}
"""Valid MP3 quality settings in kbps."""

# =============================================================================
# Configuration Validation
# =============================================================================

VALID_DUPLICATE_ACTIONS: Set[str] = {"ask", "download", "skip"}
"""Valid actions for handling duplicate downloads."""

DEFAULT_CONFIG: Dict[str, object] = {
    "default_quality": "5",
    "default_output": "downloads",
    "concurrent_downloads": DEFAULT_CONCURRENT_WORKERS,
    "thumbnail_embed": True,
    "split_enabled": False,
    "mp3_quality": "320",
    "duplicate_action": "ask",
    "use_ai_filename_cleaning": False,
    "openrouter_api_key": None,
    "search_max_results": 5,
    "search_min_duration": 30,
    "search_max_duration": 600,
    "search_use_ai": True,
    "search_fuzzy_threshold": 70,
    "_version": __version__,
}
"""Default configuration values."""

# =============================================================================
# Content Type Constants
# =============================================================================

CONTENT_TYPE_VIDEO = "video"
"""Content type identifier for single videos."""

CONTENT_TYPE_PLAYLIST = "playlist"
"""Content type identifier for playlists."""

CONTENT_TYPE_CHANNEL = "channel"
"""Content type identifier for channels."""

VALID_CONTENT_TYPES: Set[str] = {
    CONTENT_TYPE_VIDEO,
    CONTENT_TYPE_PLAYLIST,
    CONTENT_TYPE_CHANNEL,
}
"""All valid content type identifiers."""

# =============================================================================
# YouTube URL Patterns
# =============================================================================

YOUTUBE_DOMAINS: Set[str] = {
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "m.youtube.com",
    "music.youtube.com",
}
"""Valid YouTube domains for URL validation."""

YOUTUBE_URL_PATTERNS: List[str] = [
    r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"https?://youtu\.be/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/playlist\?list=[\w-]+",
    r"https?://(?:www\.)?youtube\.com/c/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/@[\w-]+",
    r"https?://(?:www\.)?youtube\.com/channel/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/user/[\w-]+",
]
"""Regex patterns for matching YouTube URLs."""

# =============================================================================
# Download Options
# =============================================================================

DEFAULT_DOWNLOAD_TEMPLATE = "%(title)s.%(ext)s"
"""Default output template for single video downloads."""

PLAYLIST_DOWNLOAD_TEMPLATE = "%(playlist_title)s/%(playlist_index)s-%(title)s.%(ext)s"
"""Default output template for playlist downloads."""

CHANNEL_DOWNLOAD_TEMPLATE = "%(uploader)s/%(upload_date)s-%(title)s.%(ext)s"
"""Default output template for channel downloads."""

YTDLP_OPTIONS: Dict[str, object] = {
    "ignoreerrors": True,
    "no_warnings": False,
    "noplaylist": False,
    "extract_flat": False,
    "writethumbnail": True,
    "embedthumbnail": True,
    "addmetadata": True,
    "merge_output_format": "mp4",
    "keepvideo": False,
    "clean_infojson": True,
    "compat_opts": ["no-youtube-unavailable-videos"],
    "youtube_include_dash_manifest": False,
    "nocheckcertificate": True,
    "prefer_ffmpeg": True,
}
"""Default yt-dlp options."""

# =============================================================================
# UI/Display Constants
# =============================================================================

BANNER_WIDTH = 60
"""Width for banner and separator lines in CLI output."""

PROGRESS_UPDATE_INTERVAL = 1
"""Minimum seconds between progress updates."""

MAX_DISPLAY_URL_LENGTH = 60
"""Maximum length of URL to display in output."""

# =============================================================================
# File Size Limits
# =============================================================================

MIN_VIDEO_SIZE_BYTES = 1024  # 1 KB
"""Minimum expected file size for a successful download."""

MAX_FILENAME_LENGTH = 200
"""Maximum safe filename length for cross-platform compatibility."""

# =============================================================================
# Security Constants
# =============================================================================

FORBIDDEN_PATH_COMPONENTS: Set[str] = {"..", "~", "."}
"""Path components that are forbidden for security reasons."""

FORBIDDEN_FILENAME_CHARS: Set[str] = {
    "<", ">", ":", "\"", "|", "?", "*", "\0",
    "\n", "\r", "\t",
}
"""Characters forbidden in filenames for security."""

SANITIZED_REPLACEMENT = "_"
"""Replacement character for sanitized filenames."""

# =============================================================================
# Search Constants
# =============================================================================

DEFAULT_SEARCH_MAX_RESULTS = 5
"""Default maximum number of search results to return."""

DEFAULT_SEARCH_MIN_DURATION = 30
"""Default minimum video duration in seconds for search."""

DEFAULT_SEARCH_MAX_DURATION = 600
"""Default maximum video duration in seconds for search (10 minutes)."""

DEFAULT_FUZZY_THRESHOLD = 70
"""Default threshold for fuzzy string matching (0-100)."""

# =============================================================================
# Timestamp/FFmpeg Constants
# =============================================================================

TIMESTAMP_FORMATS: List[str] = [
    "%M:%S",       # 3:45
    "%H:%M:%S",    # 1:03:45
    "%H:%M:%S.%f", # 1:03:45.123
]
"""Valid timestamp format strings for parsing."""

DEFAULT_TIMESTAMP_SPLIT_FORMAT = "{start}_{end}_{title}.{ext}"
"""Default format for timestamp-split filenames."""

FFMPEG_PRESETS: Dict[str, List[str]] = {
    "mp3": ["-codec:a", "libmp3lame", "-b:a", "320k"],
    "mp4": ["-c:v", "libx264", "-c:a", "aac", "-b:a", "192k"],
}
"""FFmpeg codec presets for different formats."""

# =============================================================================
# History Constants
# =============================================================================

HISTORY_DATE_FORMAT = "%Y-%m-%d"
"""Date format used in history file."""

HISTORY_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
"""DateTime format used in history file."""

MAX_HISTORY_DISPLAY_ENTRIES = 50
"""Maximum number of history entries to display."""

# =============================================================================
# Error Messages
# =============================================================================

ERROR_NETWORK = "Network error occurred. Please check your connection."
ERROR_FFMPEG_NOT_FOUND = "FFmpeg not found. Please install FFmpeg and add it to your PATH."
ERROR_INVALID_URL = "Invalid YouTube URL provided."
ERROR_DOWNLOAD_FAILED = "Download failed after maximum retries."
ERROR_FILE_NOT_FOUND = "The specified file was not found."
ERROR_PERMISSION_DENIED = "Permission denied when accessing the file or directory."
ERROR_DISK_FULL = "Disk full. Cannot save downloaded file."
