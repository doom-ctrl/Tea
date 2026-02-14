# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MCP Tools Usage

**IMPORTANT**: Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

- Use `mcp__context7__query-docs` for yt-dlp, requests, fuzzywuzzy, or other library documentation
- Use `mcp__context7__resolve-library-id` first to get the correct library ID
- Example: "Use Context7 to find how to configure yt-dlp for audio-only downloads"

## Project Overview

**Tea** is a CLI-based YouTube downloader with a coffee/tea theme. It downloads videos, playlists, channels, and audio-only MP3s with features like timestamp splitting, concurrent downloads, and download history tracking.

## Current Architecture (Post-Refactoring)

The project has been refactored from a monolithic 1600-line `tea.py` into a modular service-oriented architecture:

### Module Structure
```
tea/
├── cli.py              # Main CLI interface and user interaction
├── downloader.py        # Download orchestration with retry logic
├── config.py           # Configuration management (tea-config.json)
├── history.py          # Download history tracking (tea-history.json)
├── info.py            # Content info extraction
├── progress.py         # Progress reporting
├── ffmpeg.py           # FFmpeg operations (split, extract audio)
├── timestamps.py       # Timestamp parsing and processing
├── search.py           # YouTube search functionality
├── logger.py           # Logging setup
├── exceptions.py       # Custom exception hierarchy
├── constants.py        # Centralized constants
├── ai/
│   └── filename_cleaner.py  # AI-powered filename cleaning
└── utils/
    ├── security.py       # Security validation and sanitization
    └── spinner.py       # CLI spinners
```

### Entry Points
- **Main**: `tea.py` - Creates CLI instance and calls `run()`
- **Services**: All core functionality is in service classes with dependency injection
- **Tests**: Comprehensive test suite in `tests/` directory

## Development Commands

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (includes testing, linting, formatting)
pip install -e ".[dev]"

# Run Tea (interactive mode)
python tea.py

# Run with arguments
python tea.py --help
python tea.py --batch urls.txt
python tea.py --config
python tea.py --history

# Run tests
pytest -v                    # Run all tests
pytest tests/test_downloader.py -v  # Run specific test file
pytest --cov=tea              # Run with coverage
pytest -m "not slow"           # Skip slow tests

# Code formatting and linting
black tea/ tests/              # Format code
isort tea/ tests/             # Sort imports
ruff check tea/                # Check linting
mypy tea/                      # Type checking
```

## System Requirements

- **Python 3.10+**
- **FFmpeg** (required for post-processing, MP3 extraction, and video splitting)
- **yt-dlp** (installed via requirements.txt)
- **Optional for development**:
  - pytest (testing framework)
  - black, isort, ruff (code quality)
  - mypy (type checking)

## Testing

The project now has comprehensive test coverage:
- **Unit tests**: Individual module testing
- **Integration tests**: End-to-end workflow testing
- **Fixtures**: Shared test setup in `tests/conftest.py`
- **Coverage**: Tracked via pytest-cov

All tests use pytest and can be run with `pytest -v`.

## Continuous Integration

GitHub Actions CI/CD configured in `.github/workflows/`:
- **test.yml** - Multi-platform testing (Windows, macOS, Linux) with Python 3.10-3.12
- **lint.yml** - Code quality checks (black, isort, ruff, mypy)
- **security.yml** - Dependency security scanning

## Architecture

### Main Components

- **`tea/cli.py`** - Command-line interface, menus, and user interaction
- **`tea/downloader.py`** - Download orchestration with concurrent workers and retry logic
- **`tea/config.py`** - Configuration management (loads/saves tea-config.json)
- **`tea/history.py`** - Download history tracking (tea-history.json)
- **`tea/exceptions.py`** - Custom exception hierarchy (TeaError, DownloadError, etc.)
- **`tea/constants.py`** - Centralized application constants
- **`tea/utils/security.py`** - Security validation and sanitization utilities
- **`tests/`** - Comprehensive test suite with pytest
- **`tea.py`** - Main entry point (~40 lines)
- **`tea-config.json`** - User configuration (auto-created on first run)
- **`tea-history.json`** - Download history tracking (auto-created)

### Key Classes and Methods

| Module | Class/Function | Purpose | Location |
|---------|---------------|---------|
| `tea/cli.py` | `CLI.run()` | Main entry point, handles args or interactive mode |
| `tea/downloader.py` | `DownloadService.download_single_video()` | Core download with retry logic |
| `tea/downloader.py` | `DownloadService.download()` | Concurrent downloads via ThreadPoolExecutor |
| `tea/config.py` | `ConfigManager.get()/set()` | Configuration value access |
| `tea/history.py` | `HistoryManager.add()/is_downloaded()` | History tracking |
| `tea/info.py` | `InfoExtractor.get_info()` | Content type detection (video/playlist/channel) |
| `tea/ffmpeg.py` | `FFmpegService.split_video()` | FFmpeg video/audio splitting |
| `tea/timestamps.py` | `TimestampProcessor.parse_timestamp_list()` | Parse timestamps from various formats |
| `tea/exceptions.py` | `DownloadError/ValidationError` | Custom exception types |

### URL Processing Flow

1. **Input parsing**: `parse_multiple_urls()` handles comma/space/newline separated URLs (tea.py:938)
2. **Content detection**: `get_url_info()` determines if URL is video/playlist/channel (tea.py:869)
3. **Duplicate check**: `is_already_downloaded()` checks history (tea.py:135)
4. **Download**: `download_single_video()` processes each URL (tea.py:995)
5. **History tracking**: `save_to_history()` records successful downloads (tea.py:112)

### Output Template Patterns

- **Single video**: `%(title)s.{ext}`
- **Playlist**: `%(playlist_title)s/%(playlist_index)s-%(title)s.{ext}`
- **Channel**: `%(uploader)s/%(upload_date)s-%(title)s.{ext}`

### Configuration System

The `load_config()` function (tea.py:55) manages settings with these defaults:
- `default_quality`: '5' (audio only)
- `default_output`: 'downloads'
- `concurrent_downloads`: 3
- `thumbnail_embed`: true
- `mp3_quality`: '320'
- `duplicate_action`: 'ask'

## Constants

All application constants are centralized in `tea/constants.py`:

```python
# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_CONCURRENT_WORKERS = 5
DEFAULT_CONCURRENT_WORKERS = 3

# Quality Presets
QUALITY_PRESETS = {
    "1": "bestvideo+bestaudio/best",
    "5": "bestaudio/best",  # Audio only
    # ... more presets
}

# File Extensions
VALID_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ...}
VALID_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ...}

# Security
FORBIDDEN_FILENAME_CHARS = {"<", ">", ":", ...}
SANITIZED_REPLACEMENT = "_"
```

Always import from constants rather than hardcoding values.

## Code Style

- **Type hints**: Required for all function parameters/returns (import from `typing`)
- **Import order**: Standard library → Third-party → Local (enforced by isort)
- **Naming**:
  - UPPER_SNAKE_CASE for constants
  - PascalCase for classes
  - snake_case for functions/variables
- **Error handling**: Use custom exceptions from `tea.exceptions`
- **Status indicators**: Use `[OK]`, `[ERROR]`, `[WARNING]` text (no emojis for Windows compatibility)
- **Docstrings**: Google style with Args/Returns/Raises sections
- **Formatting**: Enforced by black (100 char line length)
- **Linting**: Enforced by ruff

### Exception Handling

Always use specific exception types from `tea.exceptions`:
```python
from tea.exceptions import ValidationError, DownloadError

# Instead of generic ValueError
raise ValidationError(
    message="Invalid URL format",
    field="url",
    value=url
)

# Instead of generic Exception
raise DownloadError(
    message="Download failed after retries",
    url=url,
    retry_count=3
)
```

## Timestamp Splitting

Supports 3 input methods:
1. **Manual entry**: Individual clip entry with start/end/times
2. **Paste**: Multi-line format like `0:00 Intro\n5:30 Content`
3. **JSON file**: Structured format with `clips` array (see `examples/bossa-nova-timestamps.json`)
4. **Auto-detect**: Extracts from YouTube chapters or video description

FFmpeg commands are constructed in `split_video_by_timestamps()` (tea.py:745).

## Thread Safety

Downloads use `ThreadPoolExecutor` with thread-safe logging via `progress_hook()` (tea.py:20). Each thread gets a unique ID for tracking.

## Important Notes

- Single video splitting only works with single URLs (not playlists/channels)
- FFmpeg must be in system PATH for splitting and MP3 conversion
- yt-dlp options are carefully tuned for reliability - modify with caution
- The application maintains download history to avoid duplicates
- Windows compatibility is prioritized (no emojis in output, `.bat` launcher)

## Documentation

- **CLAUDE.md** - This file (instructions for Claude Code)
- **CONTRIBUTING.md** - Contribution guidelines, development setup, commit conventions
- **README.md** - User-facing documentation
- **docs/API.md** - Complete API reference for all modules
- **docs/DEVELOPMENT.md** - Development environment setup guide

## Security Features

The application includes security hardening measures to protect against common vulnerabilities:

### Input Validation
- **URL validation**: All URLs are validated to ensure they are legitimate YouTube URLs
- **File path validation**: User-provided file paths are validated against path traversal attacks
- **Timestamp format validation**: Timestamps are validated to ensure proper format (MM:SS or HH:MM:SS)
- **Choice validation**: User menu choices are validated against allowed values

### Sanitization
- **Path sanitization**: File paths are sanitized to remove dangerous characters
- **Metadata sanitization**: Metadata values for FFmpeg are sanitized to prevent command injection
- **Title sanitization**: Clip titles are sanitized for safe use in filenames and metadata

### Security Utilities Module
The `tea/utils/security.py` module provides:
- `validate_file_path()` - Prevents path traversal attacks
- `sanitize_path()` - Removes dangerous characters from paths
- `validate_url()` - Validates YouTube URLs
- `sanitize_metadata()` - Sanitizes metadata for FFmpeg
- `validate_timestamp()` - Validates timestamp formats
- `sanitize_clip_title()` - Sanitizes clip titles
- `validate_choice()` - Validates user choices
- `validate_quality()` - Validates quality selections
- `validate_concurrent_workers()` - Validates worker count

### Error Handling
- Generic error messages to avoid leaking system information
- Graceful degradation when security module is unavailable
- Proper exception handling for file operations
