"""
Tea - YouTube Downloader Package

A CLI-based YouTube downloader with a coffee/tea theme.
"""

__version__ = '1.0.0'
__author__ = 'Tea Contributors'
__description__ = 'YouTube Downloader with timestamp splitting and concurrent downloads'

# Import key classes for easy access
from tea.logger import setup_logger, get_logger

__all__ = [
    'setup_logger',
    'get_logger',
]
