"""
Logging configuration for Tea YouTube Downloader.

This module provides centralized logging configuration to replace
print statements throughout the application.
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str = 'tea', level: int = logging.INFO, verbose: bool = False) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: Logger name (default: 'tea')
        level: Logging level (default: logging.INFO)
        verbose: Enable verbose/debug output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers if already configured
    if logger.handlers:
        if verbose:
            logger.setLevel(logging.DEBUG)
        return logger

    logger.setLevel(level if not verbose else logging.DEBUG)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level if not verbose else logging.DEBUG)

    # Format: [LEVEL] message
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def get_logger(name: str = 'tea') -> logging.Logger:
    """
    Get an existing logger or create a new one with defaults.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
