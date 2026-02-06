#!/usr/bin/env python3
"""
Tea - YouTube Downloader

A CLI-based YouTube downloader with a coffee/tea theme.
Downloads videos, playlists, channels, and audio-only MP3s with features like
timestamp splitting, concurrent downloads, and download history tracking.

Version: 1.0.0
"""

import sys

# Import tea CLI module
try:
    from tea.cli import CLI
    from tea.logger import setup_logger
except ImportError as e:
    print(f"[ERROR] Failed to import Tea modules: {e}")
    print("[ERROR] Make sure you're running from the correct directory")
    sys.exit(1)


def main():
    """Main entry point for Tea application."""
    logger = setup_logger('tea')
    cli = CLI(logger=logger)

    try:
        cli.run()
    except KeyboardInterrupt:
        logger.info("\nDownload cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
