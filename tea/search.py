"""
YouTube search service for Tea YouTube Downloader.

This module provides AI-enhanced YouTube search functionality to help users
find the correct videos when they only know song names or partial information.
"""

import json
import os
import re
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from yt_dlp import YoutubeDL

# Import from tea modules
try:
    from tea.logger import setup_logger
    from tea.config import ConfigManager
    from tea.utils.security import (
        validate_file_path,
        sanitize_path,
        validate_url
    )
except ImportError:
    # Fallback for development
    from tea.logger import setup_logger
    from tea.config import ConfigManager
    from tea.utils.security import (
        validate_file_path,
        sanitize_path,
        validate_url
    )

# Try to import fuzzywuzzy for result ranking
try:
    from fuzzywuzzy import fuzz
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Constants
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-coder-32b-instruct:free"
MIN_REQUEST_INTERVAL = 3.0  # seconds between requests

# Dangerous patterns for AI output validation
DANGEROUS_PATTERNS = [
    r'\.\./',  # Path traversal
    r'\.\.\\',
    r'<script',  # XSS attempts
    r'javascript:',
    r'data:',
    r'\x00',  # Null bytes
    r'\x1b',  # Escape sequences
]


class YouTubeSearchService:
    """
    AI-enhanced YouTube search service.

    Provides intelligent search capabilities with query enhancement,
    result ranking, and user-friendly selection interface.
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        logger=None
    ):
        """
        Initialize YouTubeSearchService.

        Args:
            config_manager: Configuration manager instance
            logger: Logger instance
        """
        self._config = config_manager or ConfigManager(logger=logger)
        self._logger = logger or setup_logger()
        self._last_request_time: float = 0
        self._api_key = self._config.openrouter_api_key

    # Search methods

    def search_songs(
        self,
        query: str,
        max_results: int = 5,
        use_ai: bool = True
    ) -> List[Dict]:
        """
        Search YouTube for songs matching the query.

        Args:
            query: Search query (song name, artist, etc.)
            max_results: Maximum number of results to return
            use_ai: Whether to use AI for query enhancement

        Returns:
            List of search results with url, title, duration, views, etc.
        """
        if not query or not query.strip():
            return []

        # Enhance query with AI if enabled and API key is available
        enhanced_query = query
        if use_ai and self._config.get('search_use_ai', True) and self._api_key:
            enhanced_query = self._enhance_query_with_ai(query)
            if enhanced_query and enhanced_query != query:
                self._logger.info(f"AI enhanced query: '{query}' -> '{enhanced_query}'")

        # Use enhanced query or fall back to original
        search_query = enhanced_query if enhanced_query else query

        # Perform YouTube search using yt-dlp
        results = self._youtube_search(search_query, max_results)

        # Rank and filter results
        if results:
            results = self._rank_results(query, results)

        return results

    def _enhance_query_with_ai(self, query: str) -> Optional[str]:
        """
        Enhance search query using AI for better YouTube search results.

        Args:
            query: Original search query

        Returns:
            Enhanced query or None if AI enhancement failed
        """
        if not self._api_key:
            return None

        # Wait for minimum interval between requests
        time_since_last = time.time() - self._last_request_time
        if time_since_last < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - time_since_last)

        # Prepare request
        headers = {
            'Authorization': f'Bearer {self._api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/yourusername/tea',
            'X-Title': 'Tea YouTube Downloader',
        }

        prompt = f"""Extract the artist and song title from this user input and create an optimized YouTube search query.

Rules:
1. Identify the artist name and song title
2. Remove common junk words like "download", "mp3", "free", etc.
3. Format as "Artist - Title" or "Title Artist" if artist is unclear
4. Add "official audio" or "official video" if it seems like a music search
5. Output ONLY the search query, nothing else
6. If the input is already a good search query, improve it slightly

User input: {query}

Optimized YouTube search query:"""

        data = {
            'model': MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant that creates optimized YouTube search queries. Output only the search query, no explanations.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'max_tokens': 100,
            'temperature': 0.3,
        }

        try:
            # Make request with timeout
            req = Request(
                API_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urlopen(req, timeout=10) as response:
                response_data = json.loads(response.read().decode('utf-8'))

                # Extract the enhanced query
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    enhanced = response_data['choices'][0]['message']['content'].strip()

                    # Validate the response
                    if self._validate_ai_output(enhanced):
                        self._last_request_time = time.time()
                        return enhanced

            return None

        except (URLError, HTTPError) as e:
            self._logger.warning(f"AI API error: {e}")
            return None
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            self._logger.warning(f"AI response parsing error: {e}")
            return None
        except Exception as e:
            self._logger.warning(f"AI enhancement failed: {e}")
            return None

    def _validate_ai_output(self, output: str) -> bool:
        """
        Validate AI output for security issues.

        Args:
            output: The AI-generated output

        Returns:
            True if output is safe, False otherwise
        """
        if not output or not isinstance(output, str):
            return False

        # Check for dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return False

        # Limit length
        if len(output) > 200:
            return False

        # Must contain at least one alphanumeric character
        if not re.search(r'[a-zA-Z0-9]', output):
            return False

        return True

    def _youtube_search(self, query: str, max_results: int) -> List[Dict]:
        """
        Perform YouTube search using yt-dlp.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of search results
        """
        search_url = f"ytsearch{max_results}:{query}"

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(search_url, download=False)

                if not search_results:
                    return []

                results = []
                entries = search_results.get('entries', [])

                for entry in entries:
                    if not entry:
                        continue

                    # Extract relevant information
                    result = {
                        'url': entry.get('url', entry.get('webpage_url', '')),
                        'title': entry.get('title', 'Unknown'),
                        'duration': entry.get('duration', 0),
                        'view_count': entry.get('view_count', 0),
                        'uploader': entry.get('uploader', entry.get('channel', 'Unknown')),
                        'id': entry.get('id', ''),
                    }

                    # Validate URL
                    if result['url'] and validate_url(result['url']):
                        # Filter by duration if configured
                        min_duration = self._config.get('search_min_duration', 30)
                        max_duration = self._config.get('search_max_duration', 600)

                        if result['duration'] == 0:
                            # Duration not available, include it anyway
                            results.append(result)
                        elif min_duration <= result['duration'] <= max_duration:
                            results.append(result)

                return results

        except Exception as e:
            self._logger.error(f"YouTube search error: {e}")
            return []

    def _rank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Rank search results by relevance using fuzzy matching and heuristics.

        Args:
            query: Original search query
            results: List of search results

        Returns:
            Ranked list of search results
        """
        if not results:
            return results

        # Calculate relevance scores
        for result in results:
            score = 0

            # Fuzzy matching on title
            if FUZZY_AVAILABLE:
                fuzzy_threshold = self._config.get('search_fuzzy_threshold', 70)
                title_score = fuzz.partial_ratio(
                    query.lower(),
                    result['title'].lower()
                )
                if title_score >= fuzzy_threshold:
                    score += title_score

                # Bonus for uploader/channel matching
                uploader_score = fuzz.partial_ratio(
                    query.lower(),
                    result['uploader'].lower()
                )
                if uploader_score >= fuzzy_threshold:
                    score += uploader_score // 2
            else:
                # Simple string matching fallback
                query_lower = query.lower()
                title_lower = result['title'].lower()

                # Exact phrase match
                if query_lower in title_lower:
                    score += 80

                # Word-by-word matching
                query_words = set(query_lower.split())
                title_words = set(title_lower.split())
                matching_words = query_words & title_words
                if matching_words:
                    score += len(matching_words) * 20

            # Bonus for common music keywords in title
            music_keywords = ['official', 'audio', 'video', 'lyrics', 'hd', 'remastered']
            title_lower = result['title'].lower()
            for keyword in music_keywords:
                if keyword in title_lower:
                    score += 5

            # Logarithmic bonus for view count (diminishing returns)
            if result['view_count'] > 0:
                import math
                score += min(20, int(math.log10(result['view_count'] + 1) * 2))

            result['_relevance_score'] = score

        # Sort by relevance score
        ranked = sorted(results, key=lambda x: x.get('_relevance_score', 0), reverse=True)

        # Remove temporary score field
        for result in ranked:
            result.pop('_relevance_score', None)

        return ranked

    # Display methods

    def display_search_results(
        self,
        results: List[Dict],
        query: str,
        show_indices: bool = True
    ) -> Optional[str]:
        """
        Display search results and get user selection.

        Args:
            results: List of search results
            query: Original search query
            show_indices: Whether to show numeric indices for selection

        Returns:
            Selected URL or None if user skipped
        """
        if not results:
            print(f"\n[ERROR] No results found for: {query}")
            retry = input("Try a different search query? (y/n, default=y): ").strip().lower()
            if retry == 'n':
                return None
            new_query = input("Enter new search query: ").strip()
            if new_query:
                return self.search_and_select(new_query)
            return None

        print(f"\n{'=' * 70}")
        print(f"Search results for: {query}")
        print(f"{'=' * 70}")

        for i, result in enumerate(results, 1):
            duration_str = self._format_duration(result['duration'])
            views_str = self._format_views(result['view_count'])

            print(f"\n  [{i}] {result['title'][:70]}")
            print(f"       Channel: {result['uploader']}")
            print(f"       Duration: {duration_str} | Views: {views_str}")
            print(f"       URL: {result['url']}")

        print(f"\n{'=' * 70}")

        if not show_indices:
            return None

        while True:
            choice = input(
                f"Select result (1-{len(results)}, 0 to skip, s to search again): "
            ).strip().lower()

            if choice == '0':
                print("[INFO] Skipped")
                return None
            elif choice == 's':
                new_query = input("Enter new search query: ").strip()
                if new_query:
                    return self.search_and_select(new_query)
                return None

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(results):
                    selected = results[choice_num - 1]
                    print(f"\n[OK] Selected: {selected['title'][:60]}")
                    return selected['url']
                else:
                    print(f"[WARNING] Please enter a number between 0 and {len(results)}")
            except ValueError:
                print("[WARNING] Invalid input. Please enter a number")

    def search_and_select(self, query: str) -> Optional[str]:
        """
        Search and select a video in one step.

        Args:
            query: Search query

        Returns:
            Selected URL or None if user skipped
        """
        max_results = self._config.get('search_max_results', 5)
        use_ai = self._config.get('search_use_ai', True)

        results = self.search_songs(query, max_results, use_ai)
        return self.display_search_results(results, query)

    # File loading methods

    def load_songs_from_file(self, filepath: str) -> List[str]:
        """
        Load song names from a text file.

        Args:
            filepath: Path to the text file

        Returns:
            List of song names
        """
        try:
            validated_path = validate_file_path(
                filepath,
                allowed_extensions=['.txt', '.list'],
                base_dir=None
            )

            if not os.path.exists(validated_path):
                print(f"[ERROR] File not found: {filepath}")
                return []

            if not os.path.isfile(validated_path):
                print(f"[ERROR] Path is not a file: {filepath}")
                return []

            with open(validated_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            songs = []
            for line in lines:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                songs.append(line)

            print(f"[OK] Loaded {len(songs)} song(s) from file")
            return songs

        except Exception as e:
            self._logger.error(f"Error reading file: {e}")
            print(f"[ERROR] Error reading file")
            return []

    # Utility methods

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to MM:SS or HH:MM:SS."""
        if seconds == 0:
            return "Unknown"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"

    def _format_views(self, view_count: int) -> str:
        """Format view count to human-readable string."""
        if view_count == 0:
            return "Unknown"

        if view_count >= 1_000_000:
            return f"{view_count / 1_000_000:.1f}M"
        elif view_count >= 1_000:
            return f"{view_count / 1_000:.1f}K"
        return str(view_count)


# Convenience functions for backward compatibility
def search_songs(query: str, max_results: int = 5) -> List[Dict]:
    """Search for songs (legacy function)."""
    service = YouTubeSearchService()
    return service.search_songs(query, max_results)


def search_and_select(query: str) -> Optional[str]:
    """Search and select a video (legacy function)."""
    service = YouTubeSearchService()
    return service.search_and_select(query)
