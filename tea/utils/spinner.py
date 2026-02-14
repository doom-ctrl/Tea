"""
Spinner utility for Tea YouTube Downloader.

This module provides a simple terminal spinner for loading indicators.
"""

import threading
import time
from typing import Optional


class Spinner:
    """A simple terminal spinner for loading indicators."""

    FRAMES = ['-', '\\', '|', '/']

    def __init__(self, message: str = "Processing"):
        """
        Initialize the Spinner.

        Args:
            message: The message to display alongside the spinner
        """
        self.message = message
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the spinner in a background thread."""
        if self._running:
            return  # Already running

        self._running = True
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()

    def stop(self, final_message: Optional[str] = None) -> None:
        """
        Stop the spinner and optionally show final message.

        Args:
            final_message: Optional message to display after stopping
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.2)
            self._thread = None

        # Clear the spinner line
        print("\r" + " " * (len(self.message) + 3) + "\r", end='', flush=True)
        if final_message:
            print(final_message)

    def _spin(self) -> None:
        """Internal spinning loop."""
        while self._running:
            for frame in self.FRAMES:
                if not self._running:
                    break
                print(f"\r{self.message} {frame}", end='', flush=True)
                time.sleep(0.1)
