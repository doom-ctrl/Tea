# Agent Guidelines for Tea - YouTube Downloader

This document provides guidelines for agentic coding assistants working in this repository.

## Project Overview

**Tea** (☕) - A beautiful, user-friendly YouTube video downloader with a coffee-themed branding. Supports videos, playlists, and channels with concurrent downloading and MP3 audio extraction. Uses yt-dlp and FFmpeg.

## Branding

- **Name**: Tea
- **Tagline**: "Tea - Brew your favorite videos"
- **Theme**: Coffee/tea themed with ASCII art banner
- **Status indicators**: Use [OK], [ERROR], [WARNING] instead of emojis for Windows compatibility

## Build, Install, and Test Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main downloader (interactive)
python tea.py
python3 tea.py
tea  # If tea.bat is in PATH (Windows)

# List available formats for a video (debugging)
python tea.py --list-formats

# Clean up incomplete downloads
python cleanup_downloads.py

# No test suite exists - test manually by running the script
```

**Note**: This project has no automated tests. Manual testing is required:
1. Test single video download
2. Test multiple concurrent downloads
3. Test playlist download (auto-numbered files)
4. Test channel download (date-organized files)
5. Test MP3 audio-only mode
6. Test various URL formats

## Code Style Guidelines

### Imports

Organize imports in this order:
1. Standard library imports (sys, os, re, time, etc.)
2. Third-party imports (yt_dlp, urllib.parse, concurrent.futures)
3. Local imports (none in this project)

Example from tea.py:1-9:
```python
import sys
from yt_dlp import YoutubeDL
import os
import re
import time
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
```

### Type Hints

Always use type hints for function parameters and return values:
```python
def download_single_video(url: str, output_path: str, thread_id: int = 0, audio_only: bool = False) -> dict:
```

Import from typing module: `from typing import Optional, List, Dict, Tuple`

### Naming Conventions

- **Constants**: UPPER_SNAKE_CASE (e.g., MAX_RETRIES, DEFAULT_CONCURRENT_WORKERS)
- **Functions**: snake_case (e.g., get_url_info, parse_multiple_urls)
- **Variables**: snake_case (e.g., content_type, video_count)
- **Classes**: PascalCase (none currently, but follow convention if added)

### Docstrings

Use Google-style docstrings with Args and Returns sections:

```python
def parse_multiple_urls(input_string: str) -> List[str]:
    """
    Parse multiple URLs from input string separated by commas, spaces, newlines, or mixed formats.

    Args:
        input_string (str): String containing one or more URLs

    Returns:
        List[str]: List of cleaned URLs
    """
```

### Error Handling

- Use try/except blocks for operations that may fail
- Retry with exponential backoff for network operations (see tea.py:266-272)
- Return error dictionaries with meaningful messages
- Log errors with thread/context info: `print(f"[ERROR] [Thread {thread_id}] Failed: {error}")`
- Never crash the entire program on single URL failure - use error resilience

### Constants and Configuration

All magic numbers should be constants at module level:
```python
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_CONCURRENT_WORKERS = 5
DEFAULT_CONCURRENT_WORKERS = 3
```

### String Formatting

Use f-strings for all string formatting (tea.py:20):
```python
print(f"🎵 [Thread {thread_id}] Audio-only mode: Downloading MP3...")
```

### File Organization

- Main script: tea.py (480+ lines)
- Utility script: cleanup_downloads.py (61 lines)
- Windows launcher: tea.bat
- Downloads directory: downloads/ (auto-created)
- Configuration: requirements.txt

### Function Design Patterns

- Single responsibility: Each function does one thing well
- Use decorators: @lru_cache for memoization when appropriate (tea.py:17)
- Use context managers: `with YoutubeDL(ydl_opts) as ydl:`
- ThreadPoolExecutor for concurrent operations (tea.py:340)

### yt-dlp Options Pattern

When configuring yt-dlp, use dictionary structure matching tea.py:177-201:
```python
downloader_options = {
    'format': format_selector,
    'ignoreerrors': True,
    'postprocessors': postprocessors,
    'outtmpl': os.path.join(output_path, '%(title)s.{ext}'),
    'retries': MAX_RETRIES,
    'fragment_retries': MAX_RETRIES,
}
```

### Content Detection

Support all YouTube URL formats in validation logic:
- Single videos: youtube.com/watch?v=... or youtu.be/...
- Playlists: youtube.com/playlist?list=...
- Channels: youtube.com/@handle, /channel/ID, /c/name, /user/name

See get_url_info() and parse_multiple_urls() for implementation examples.

### Output Templates

Use yt-dlp output templates with %(variable)s placeholders:
- Single video: `%(title)s.{ext}`
- Playlist: `%(playlist_title)s/%(playlist_index)s-%(title)s.{ext}`
- Channel: `%(uploader)s/%(upload_date)s-%(title)s.{ext}`

### Retry Logic

Implement exponential backoff for retries (tea.py:266-272):
```python
for attempt in range(1, MAX_RETRIES + 1):
    try:
        # operation
    except Exception as error:
        if attempt < MAX_RETRIES:
            retry_delay = RETRY_DELAY * (2 ** (attempt - 1))
            time.sleep(retry_delay)
```

### Status Indicators in User Output

Use consistent status indicators for user-facing messages (Windows-compatible, no emojis):
- Success: [OK]
- Errors: [ERROR]
- Warnings: [WARNING]
- Info: Use descriptive text

## When Making Changes

1. Test with single videos, playlists, channels
2. Verify concurrent downloads work
3. Test both MP4 video and MP3 audio modes
4. Check error resilience (one failed download shouldn't stop others)
5. Ensure all URL formats are supported
6. Verify file organization (playlist folders, channel date prefixes)
