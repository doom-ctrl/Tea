"""
AI-powered filename cleaner for Tea YouTube Downloader.

Uses OpenRouter's free Qwen model to clean YouTube video titles,
with regex-based fallback for when AI is unavailable.
"""

import re
import json
import time
from typing import Optional, Dict
from datetime import datetime
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


class FilenameCleaner:
    """
    AI-powered filename cleaner with rate limiting and fallback.

    Uses OpenRouter's Qwen 2.5 Coder model (free tier) to intelligently
    clean YouTube video titles while preserving meaningful content.
    """

    # OpenRouter API configuration
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    MODEL = "qwen/qwen-2.5-coder-32b-instruct:free"

    # Rate limiting (free tier limits)
    MAX_DAILY_REQUESTS = 50
    MIN_REQUEST_INTERVAL = 3.0  # seconds between requests (20 req/min limit)

    # Dangerous patterns to validate against
    DANGEROUS_PATTERNS = [
        r'\.\./',  # Path traversal
        r'\.\.\\',
        r'<script',  # XSS attempts
        r'javascript:',
        r'data:',
        r'\x00',  # Null bytes
        r'\x1b',  # Escape sequences
    ]

    def __init__(self, api_key: str):
        """
        Initialize the filename cleaner.

        Args:
            api_key: OpenRouter API key (get free at https://openrouter.ai)
        """
        if not api_key or not isinstance(api_key, str):
            raise ValueError("API key must be a non-empty string")

        self.api_key = api_key.strip()
        self.request_history: Dict[str, int] = {}
        self.last_request_time: float = 0

    def _can_make_request(self) -> bool:
        """
        Check if we can make an API request based on rate limits.

        Returns:
            True if request can be made, False otherwise
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Check daily limit
        daily_count = self.request_history.get(today, 0)
        if daily_count >= self.MAX_DAILY_REQUESTS:
            return False

        # Check minimum interval between requests
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            return False

        return True

    def _record_request(self) -> None:
        """Record that a request was made."""
        today = datetime.now().strftime('%Y-%m-%d')
        self.request_history[today] = self.request_history.get(today, 0) + 1
        self.last_request_time = time.time()

    def get_remaining_requests(self) -> int:
        """
        Get the number of remaining API requests for today.

        Returns:
            Number of remaining requests (0-50)
        """
        today = datetime.now().strftime('%Y-%m-%d')
        return max(0, self.MAX_DAILY_REQUESTS - self.request_history.get(today, 0))

    def _ai_clean(self, title: str) -> Optional[str]:
        """
        Clean a title using the OpenRouter API.

        Args:
            title: The title to clean

        Returns:
            Cleaned title, or None if API call failed
        """
        # Check rate limits
        if not self._can_make_request():
            return None

        # Wait for minimum interval
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - time_since_last)

        # Prepare request
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/yourusername/tea',
            'X-Title': 'Tea YouTube Downloader',
        }

        prompt = f"""Clean this YouTube video title for use as a filename.

Rules:
1. Remove emojis, special characters, and excessive punctuation
2. Keep words meaningful and readable
3. Replace spaces with single spaces (no multiple spaces)
4. Remove phrases like "Official Video", "HD", "4K", etc.
5. Preserve the core meaning and important keywords
6. Output ONLY the cleaned title, nothing else

Original title: {title}

Cleaned title:"""

        data = {
            'model': self.MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful assistant that cleans video titles for filenames. Output only the cleaned title, no explanations.'
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
                self.API_URL,
                data=json.dumps(data).encode('utf-8'),
                headers=headers,
                method='POST'
            )

            with urlopen(req, timeout=10) as response:
                response_data = json.loads(response.read().decode('utf-8'))

                # Extract the cleaned title
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    cleaned = response_data['choices'][0]['message']['content'].strip()

                    # Validate the response
                    if self._validate_ai_output(cleaned):
                        self._record_request()
                        return cleaned

            return None

        except (URLError, HTTPError) as e:
            # Network or API error
            return None
        except (json.JSONDecodeError, KeyError, IndexError):
            # Malformed response
            return None
        except Exception:
            # Any other error
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
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, output, re.IGNORECASE):
                return False

        # Limit length
        if len(output) > 100:
            return False

        # Must contain at least one alphanumeric character
        if not re.search(r'[a-zA-Z0-9]', output):
            return False

        return True

    def _regex_clean(self, title: str) -> str:
        """
        Clean a title using regex patterns (fallback method).

        Args:
            title: The title to clean

        Returns:
            Regex-cleaned title
        """
        if not title or not isinstance(title, str):
            return 'Untitled'

        # Remove common junk phrases (more specific patterns to avoid over-matching)
        junk_phrases = [
            r'\s+\(Official Video\)',
            r'\s+\[Official Video\]',
            r'\s+Official Video\s*$',
            r'\s+\(Official Music Video\)',
            r'\s+\[Official Music Video\]',
            r'\s+Official Music Video\s*$',
            r'\s+\(MV\)\s*$',
            r'\s+\[MV\]\s*$',
            r'\s+MV\s*$',
            r'\s+\(HD\)\s*$',
            r'\s+\[HD\]\s*$',
            r'\s+HD\s*$',
            r'\s+\(4K\)\s*$',
            r'\s+\[4K\]\s*$',
            r'\s+4K\s*$',
            r'\s+\(Remastered\)\s*$',
            r'\s+\[Remastered\]\s*$',
            r'\s+Remastered\s*$',
            r'\s+\(Lyrics\)\s*$',
            r'\s+\[Lyrics\]\s*$',
            r'\s+Lyrics\s*$',
            r'\s+\(Audio\)\s*$',
            r'\s+\[Audio\]\s*$',
            r'\s+Audio\s*$',
            r'\s+\(Official\)\s*$',
            r'\s+\[Official\]\s*$',
            r'\s+Official\s*$',
        ]

        for phrase in junk_phrases:
            title = re.sub(phrase, '', title, flags=re.IGNORECASE)

        # Remove "feat." or "ft." from end
        title = re.sub(r'\s+[\[\(]?feat\.?\s.*?[\]\)]?$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+[\[\(]?ft\.?\s.*?[\]\)]?$', '', title, flags=re.IGNORECASE)

        # Remove emojis and special characters (keep basic punctuation)
        # Replace common unicode ranges with space
        title = re.sub(r'[\U0001F600-\U0001F64F]', '', title)  # Emoticons
        title = re.sub(r'[\U0001F300-\U0001F5FF]', '', title)  # Symbols & pictographs
        title = re.sub(r'[\U0001F680-\U0001F6FF]', '', title)  # Transport & map
        title = re.sub(r'[\U0001F1E0-\U0001F1FF]', '', title)  # Flags
        title = re.sub(r'[\U00002702-\U000027B0]', '', title)  # Dingbats
        title = re.sub(r'[\U000024C2-\U0001F251]', '', title)  # Enclosed characters

        # Remove special characters but keep letters, numbers, hyphens, and basic punctuation
        title = re.sub(r'[^\w\s\-]', ' ', title)

        # Replace multiple spaces with single space
        title = re.sub(r'\s+', ' ', title)

        # Remove leading/trailing whitespace and limit length
        title = title.strip()[:100]

        # Handle empty result
        if not title:
            return 'Untitled'

        return title

    def clean_title(self, title: str) -> str:
        """
        Clean a YouTube video title for use as a filename.

        Attempts AI cleaning first, falls back to regex if AI fails.

        Args:
            title: The title to clean

        Returns:
            Cleaned title safe for use as a filename
        """
        if not title or not isinstance(title, str):
            return 'Untitled'

        # Try AI cleaning first
        ai_cleaned = self._ai_clean(title)
        if ai_cleaned:
            return ai_cleaned

        # Fall back to regex cleaning
        return self._regex_clean(title)
