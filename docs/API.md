# Tea API Documentation

This document describes the public API for Tea YouTube Downloader.

## Table of Contents

- [Module Overview](#module-overview)
- [CLI Class](#cli-class)
- [DownloadService](#downloadservice)
- [ConfigManager](#configmanager)
- [HistoryManager](#historymanager)
- [Exceptions](#exceptions)
- [Constants](#constants)

## Module Overview

Tea is organized into service classes that can be used independently or together:

```
tea/
├── cli.py           # User interface
├── downloader.py      # Download orchestration
├── config.py         # Configuration management
├── history.py        # Download history
├── info.py          # Content information
├── progress.py       # Progress reporting
├── ffmpeg.py         # FFmpeg operations
├── timestamps.py     # Timestamp handling
├── search.py         # Search functionality
├── exceptions.py     # Custom exceptions
└── constants.py      # Application constants
```

## CLI Class

The `CLI` class provides the main user interface.

### Initialization

```python
from tea.cli import CLI
from tea.logger import setup_logger

logger = setup_logger('tea')
cli = CLI(logger=logger)
```

### Methods

#### `run() -> None`
Run the CLI application. Handles command-line arguments or enters interactive mode.

```python
cli.run()
```

#### `show_banner() -> None`
Display the application banner.

```python
cli.show_banner()
```

#### `show_help() -> None`
Display help information.

```python
cli.show_help()
```

#### `get_urls_interactive() -> str`
Prompt user for URLs interactively.

```python
url_input = cli.get_urls_interactive()
```

#### `parse_multiple_urls(input_string: str) -> List[str]`
Parse multiple URLs from comma/space/newline separated input.

```python
urls = cli.parse_multiple_urls("url1, url2")
```

## DownloadService

The `DownloadService` class handles all download operations.

### Initialization

```python
from tea.downloader import DownloadService
from tea.config import ConfigManager
from tea.history import HistoryManager

service = DownloadService(
    config_manager=ConfigManager(),
    history_manager=HistoryManager(),
)
```

### Methods

#### `download_single_video(url, output_path, thread_id=0, audio_only=False, cleaner=None) -> dict`
Download a single video with retry logic.

**Parameters:**
- `url` (str): YouTube URL
- `output_path` (str): Directory to save file
- `thread_id` (int): Thread identifier for logging
- `audio_only` (bool): Download audio only (MP3)
- `cleaner` (FilenameCleaner): Optional AI filename cleaner

**Returns:**
- `dict`: Result dictionary with keys:
  - `success` (bool): Whether download succeeded
  - `count` (int): Number of items downloaded
  - `url` (str): Downloaded URL
  - `title` (str): Content title
  - `message` (str): Status message

**Raises:**
- `DownloadError`: If download fails after max retries
- `ValidationError`: If URL or parameters are invalid

```python
result = service.download_single_video(
    url="https://youtube.com/watch?v=xxx",
    output_path="downloads",
    audio_only=True
)
```

#### `download(urls, output_path=None, list_formats=False, max_workers=3, audio_only=False, cleaner=None) -> None`
Download multiple URLs with concurrent workers.

**Parameters:**
- `urls` (List[str]): List of YouTube URLs
- `output_path` (str): Directory to save (default: "downloads")
- `list_formats` (bool): Only list formats for first URL
- `max_workers` (int): Concurrent download workers (1-5)
- `audio_only` (bool): Download audio only
- `cleaner` (FilenameCleaner): Optional AI filename cleaner

**Raises:**
- `ValidationError`: If max_workers is invalid

```python
service.download(
    urls=["url1", "url2"],
    output_path="downloads",
    max_workers=3,
    audio_only=False
)
```

## ConfigManager

The `ConfigManager` class handles configuration loading and saving.

### Initialization

```python
from tea.config import ConfigManager

config = ConfigManager()  # Uses default path
# or
config = ConfigManager(config_path="custom/config.json")
```

### Properties

#### `config_path -> str`
Get the configuration file path.

```python
path = config.config_path
```

### Methods

#### `load() -> Dict[str, Any]`
Load configuration from file.

**Returns:**
- `Dict[str, Any]`: Configuration dictionary

```python
config_data = config.load()
```

#### `save(config: Dict[str, Any]) -> bool`
Save configuration to file.

**Parameters:**
- `config` (Dict[str, Any]): Configuration to save

**Returns:**
- `bool`: True if saved successfully

```python
config.save({"default_quality": "5"})
```

#### `get(key: str, default=None) -> Any`
Get a configuration value.

**Parameters:**
- `key` (str): Configuration key
- `default` (Any): Default value if key not found

**Returns:**
- `Any`: Configuration value or default

```python
quality = config.get("default_quality", "5")
```

#### `set(key: str, value: Any) -> None`
Set a configuration value.

**Parameters:**
- `key` (str): Configuration key
- `value` (Any): Value to set

**Raises:**
- `ValidationError`: If value is invalid

```python
config.set("default_quality", "1")
```

## HistoryManager

The `HistoryManager` class tracks download history.

### Initialization

```python
from tea.history import HistoryManager

history = HistoryManager()  # Uses default path
# or
history = HistoryManager(history_path="custom/history.json")
```

### Methods

#### `load() -> Dict[str, List[Dict]]`
Load history from file.

**Returns:**
- `Dict[str, List[Dict]]`: History dictionary by date

```python
history_data = history.load()
```

#### `save() -> bool`
Save history to file.

**Returns:**
- `bool`: True if saved successfully

```python
history.save()
```

#### `add(url, title, output_path, content_type="video", quality="5") -> bool`
Add a download to history.

**Parameters:**
- `url` (str): YouTube URL
- `title` (str): Content title
- `output_path` (str): Where file was saved
- `content_type` (str): "video", "playlist", or "channel"
- `quality` (str): Quality preset used

**Returns:**
- `bool`: True if saved successfully

```python
history.add(
    url="https://youtube.com/watch?v=xxx",
    title="Video Title",
    output_path="downloads",
    content_type="video",
    quality="5"
)
```

#### `is_downloaded(url) -> bool`
Check if URL is in history.

**Parameters:**
- `url` (str): YouTube URL to check

**Returns:**
- `bool`: True if URL is already in history

```python
if history.is_downloaded(url):
    print("Already downloaded!")
```

#### `get_stats() -> Dict[str, Any]`
Get download statistics.

**Returns:**
- `Dict[str, Any]`: Statistics with keys:
  - `total_downloads` (int)
  - `unique_days` (int)

```python
stats = history.get_stats()
print(f"Total: {stats['total_downloads']}")
```

## Exceptions

Tea uses custom exception classes from `tea.exceptions`.

### Exception Hierarchy

```
TeaError
├── DownloadError
├── ValidationError
├── ConfigurationError
├── FFmpegError
├── HistoryError
├── TimestampError
└── SearchError
```

### Usage Examples

```python
from tea.exceptions import ValidationError, DownloadError

try:
    service.download_single_video(url, output_path)
except ValidationError as e:
    print(f"Invalid input: {e.message}")
    print(f"Field: {e.field}")
except DownloadError as e:
    print(f"Download failed: {e.message}")
    print(f"Retries: {e.retry_count}")
```

## Constants

Application constants are defined in `tea.constants`.

### Retry Configuration

```python
from tea.constants import (
    MAX_RETRIES,              # 3
    RETRY_DELAY,               # 2 (seconds)
    MAX_CONCURRENT_WORKERS,    # 5
    DEFAULT_CONCURRENT_WORKERS, # 3
)
```

### Quality Presets

```python
from tea.constants import QUALITY_PRESETS, VALID_QUALITIES

quality_format = QUALITY_PRESETS["5"]  # "bestaudio/best"
if "1080p" in VALID_QUALITIES:
    ...
```

### File Extensions

```python
from tea.constants import (
    VALID_VIDEO_EXTENSIONS,
    VALID_AUDIO_EXTENSIONS,
)

if ".mp4" in VALID_VIDEO_EXTENSIONS:
    ...
```

## Advanced Usage

### Custom Error Handling

```python
from tea.cli import CLI
from tea.exceptions import TeaError

cli = CLI()
try:
    cli.run()
except TeaError as e:
    print(f"Tea error: {e}")
    if e.details:
        print(f"Details: {e.details}")
```

### Programmatic Downloads

```python
from tea.downloader import DownloadService
from tea.config import ConfigManager
from tea.history import HistoryManager

# Create service
service = DownloadService(
    config_manager=ConfigManager(),
    history_manager=HistoryManager(),
)

# Download without UI
service.download(
    urls=["https://youtube.com/watch?v=xxx"],
    output_path="downloads",
    max_workers=1
)
```

### Configuration Management

```python
from tea.config import ConfigManager

config = ConfigManager()

# Get current value
current_quality = config.get("default_quality")

# Set new value
config.set("default_quality", "1")

# Reset to defaults
config.reset_to_defaults()
```

For more detailed documentation, see the inline docstrings or type hints in the source code.
