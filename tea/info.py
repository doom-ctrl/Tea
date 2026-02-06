"""
URL and content type detection for Tea YouTube Downloader.

This module handles URL validation and content type detection (video/playlist/channel).
"""

import re
from typing import Dict, Tuple, Optional
from urllib.parse import urlparse, parse_qs
from functools import lru_cache

from yt_dlp import YoutubeDL


# YouTube URL patterns
YOUTUBE_PATTERNS = {
    'video': [
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
    ],
    'playlist': [
        r'youtube\.com/playlist\?list=',
    ],
    'channel': [
        r'youtube\.com/@',
        r'youtube\.com/channel/',
        r'youtube\.com/c/',
        r'youtube\.com/user/',
    ]
}


class InfoExtractor:
    """Extracts information from YouTube URLs."""

    def __init__(self, logger=None):
        """
        Initialize InfoExtractor.

        Args:
            logger: Logger instance for logging
        """
        self._logger = logger
        self._cache: Dict[str, Tuple[str, Dict]] = {}

    def _extract_with_ytdlp(self, url: str) -> Tuple[str, Dict]:
        """
        Extract URL info using yt-dlp.

        Args:
            url: YouTube URL

        Returns:
            Tuple of (content_type, info_dict)
        """
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'no_warnings': True,
                'skip_download': True,
                'playlist_items': '1',
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return self._guess_from_url(url)

                content_type = info.get('_type', 'video')

                # Distinguish between playlist and channel
                if content_type == 'playlist':
                    if self._is_channel_url(url):
                        return 'channel', info
                    else:
                        return 'playlist', info

                return content_type, info

        except Exception as e:
            if self._logger:
                self._logger.debug(f"Error extracting info: {e}")
            return self._guess_from_url(url)

    def _guess_from_url(self, url: str) -> Tuple[str, Dict]:
        """
        Guess content type from URL pattern.

        Args:
            url: YouTube URL

        Returns:
            Tuple of (content_type, empty_dict)
        """
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # Check for channel patterns first
        if self._is_channel_url(url):
            return 'channel', {}

        # Check for playlist
        if 'list' in query_params:
            return 'playlist', {}

        # Default to video
        return 'video', {}

    def _is_channel_url(self, url: str) -> bool:
        """Check if URL matches channel patterns."""
        patterns = [
            '/@' in url,
            '/channel/' in url,
            '/c/' in url,
            '/user/' in url
        ]
        return any(patterns)

    def get_info(self, url: str, use_cache: bool = True) -> Tuple[str, Dict]:
        """
        Get URL information with optional caching.

        Args:
            url: YouTube URL to analyze
            use_cache: Use cached results if available

        Returns:
            Tuple of (content_type, info_dict) where content_type is 'video', 'playlist', or 'channel'
        """
        if use_cache and url in self._cache:
            return self._cache[url]

        result = self._extract_with_ytdlp(url)

        if use_cache:
            self._cache[url] = result

        return result

    def get_content_type(self, url: str) -> str:
        """
        Get the content type of a YouTube URL.

        Args:
            url: YouTube URL to analyze

        Returns:
            'video', 'playlist', or 'channel'
        """
        content_type, _ = self.get_info(url)
        return content_type

    def clear_cache(self) -> None:
        """Clear the URL info cache."""
        self._cache.clear()


# Global instance with LRU cache for backward compatibility
@lru_cache(maxsize=128)
def get_url_info(url: str) -> Tuple[str, Dict]:
    """
    Get URL information with caching (legacy function).

    Args:
        url: YouTube URL to analyze

    Returns:
        Tuple of (content_type, info_dict)
    """
    extractor = InfoExtractor()
    return extractor.get_info(url, use_cache=False)


def get_content_type(url: str) -> str:
    """
    Get the content type of a YouTube URL (legacy function).

    Args:
        url: YouTube URL to analyze

    Returns:
        'video', 'playlist', or 'channel'
    """
    content_type, _ = get_url_info(url)
    return content_type


def is_youtube_url(url: str) -> bool:
    """
    Check if a URL is a valid YouTube URL.

    Args:
        url: URL to check

    Returns:
        True if valid YouTube URL
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        domain = parsed.netloc.lower()
        return domain in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be')
    except Exception:
        return False
