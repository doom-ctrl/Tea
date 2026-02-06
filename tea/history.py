"""
Download history management for Tea YouTube Downloader.

This module handles tracking, displaying, and managing download history.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


def get_history_path() -> str:
    """Get path to download history file."""
    # Look in the same directory as the parent module
    module_dir = Path(__file__).parent.parent
    return str(module_dir / 'tea-history.json')


class HistoryManager:
    """Manages download history tracking."""

    def __init__(self, history_path: Optional[str] = None, logger=None):
        """
        Initialize HistoryManager.

        Args:
            history_path: Path to history file (default: auto-detect)
            logger: Logger instance for logging
        """
        self._history_path = history_path or get_history_path()
        self._logger = logger
        self._history: Dict[str, List[Dict]] = {}

    def load(self) -> Dict[str, List[Dict]]:
        """
        Load download history from file.

        Returns:
            Dictionary mapping dates to download lists
        """
        if os.path.exists(self._history_path):
            try:
                with open(self._history_path, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except json.JSONDecodeError:
                self._history = {}
            except Exception as e:
                if self._logger:
                    self._logger.warning(f"Error loading history: {e}")
                self._history = {}
        else:
            self._history = {}

        return self._history

    def save(self) -> bool:
        """
        Save history to file.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self._history_path, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            if self._logger:
                self._logger.warning(f"Could not save to history: {e}")
            return False

    def add(self, url: str, title: str, output_path: str) -> bool:
        """
        Add a download to history.

        Args:
            url: YouTube URL
            title: Video/playlist title
            output_path: Where the file was saved

        Returns:
            True if saved successfully
        """
        self.load()  # Ensure history is loaded

        today = datetime.now().strftime('%Y-%m-%d')

        if today not in self._history:
            self._history[today] = []

        self._history[today].append({
            'url': url,
            'title': title,
            'output_path': output_path,
            'timestamp': datetime.now().isoformat()
        })

        return self.save()

    def is_downloaded(self, url: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if URL was already downloaded.

        Args:
            url: YouTube URL to check

        Returns:
            Tuple of (is_downloaded, download_info)
        """
        self.load()

        for date, downloads in self._history.items():
            for download in downloads:
                if download.get('url') == url:
                    return True, download
        return False, None

    def remove(self, url: str) -> bool:
        """
        Remove a URL from download history.

        Args:
            url: URL to remove

        Returns:
            True if removed, False if not found
        """
        self.load()
        found = False

        for date, downloads in self._history.items():
            original_length = len(downloads)
            self._history[date] = [d for d in downloads if d.get('url') != url]

            if len(self._history[date]) < original_length:
                found = True

        # Remove empty date entries
        self._history = {
            date: downloads
            for date, downloads in self._history.items()
            if downloads
        }

        if found:
            return self.save()

        return False

    def clear(self) -> bool:
        """
        Clear all download history.

        Returns:
            True if cleared successfully
        """
        self._history = {}
        return self.save()

    def show(self, limit: Optional[int] = None) -> None:
        """
        Display download history.

        Args:
            limit: Maximum number of recent downloads to show (None for all)
        """
        self.load()

        if not self._history:
            if self._logger:
                self._logger.info("No download history yet")
            print("\n[INFO] No download history yet")
            return

        print("\n[OK] Download History")
        print("-" * 60)

        count = 0
        for date in sorted(self._history.keys(), reverse=True):
            if limit and count >= limit:
                break

            downloads = self._history[date]
            print(f"\n[OK] {date} ({len(downloads)} downloads)")

            for i, dl in enumerate(downloads, 1):
                if limit and count >= limit:
                    break
                count += 1

                title = dl.get('title', 'Unknown')
                url = dl.get('url', 'N/A')
                print(f"  {i}. {title[:60]}")
                print(f"     URL: {url}")

    def get_all_urls(self) -> List[str]:
        """
        Get list of all downloaded URLs.

        Returns:
            List of unique URLs
        """
        self.load()
        urls = []
        for downloads in self._history.values():
            for download in downloads:
                url = download.get('url')
                if url and url not in urls:
                    urls.append(url)
        return urls

    def get_stats(self) -> Dict[str, int]:
        """
        Get download statistics.

        Returns:
            Dictionary with stats (total_downloads, unique_days, etc.)
        """
        self.load()
        total = sum(len(downloads) for downloads in self._history.values())
        return {
            'total_downloads': total,
            'unique_days': len(self._history),
            'urls_today': len(self._history.get(datetime.now().strftime('%Y-%m-%d'), []))
        }

    def to_dict(self) -> Dict[str, List[Dict]]:
        """Return history as dictionary."""
        self.load()
        return self._history.copy()


# Convenience functions for backward compatibility
def load_history() -> Dict[str, List[Dict]]:
    """Load download history (legacy function)."""
    manager = HistoryManager()
    return manager.load()


def save_to_history(url: str, title: str, output_path: str) -> None:
    """Save download to history (legacy function)."""
    manager = HistoryManager()
    manager.add(url, title, output_path)


def is_already_downloaded(url: str) -> Tuple[bool, Optional[Dict]]:
    """Check if URL was already downloaded (legacy function)."""
    manager = HistoryManager()
    return manager.is_downloaded(url)


def show_history() -> None:
    """Display download history (legacy function)."""
    manager = HistoryManager()
    manager.show()


def remove_from_history(url: str) -> bool:
    """Remove a URL from download history (legacy function)."""
    manager = HistoryManager()
    return manager.remove(url)


def clear_history() -> bool:
    """Clear all download history (legacy function)."""
    manager = HistoryManager()
    return manager.clear()
