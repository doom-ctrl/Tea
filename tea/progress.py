"""
Progress reporting for Tea YouTube Downloader.

This module handles progress reporting for downloads.
"""

from typing import Dict, Any, Optional


class ProgressReporter:
    """Reports download progress."""

    def __init__(self, logger=None):
        """
        Initialize ProgressReporter.

        Args:
            logger: Logger instance for logging
        """
        self._logger = logger
        self._last_percent = -1

    def progress_hook(self, d: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Progress hook for yt-dlp with beautiful formatting.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Structured progress data or None
        """
        if d['status'] == 'downloading':
            return self._report_downloading(d)
        elif d['status'] == 'finished':
            return self._report_finished(d)
        elif d['status'] == 'postprocessing':
            return self._report_postprocessing(d)
        elif d['status'] == 'error':
            return self._report_error(d)

        return None

    def _report_downloading(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report downloading progress.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Structured progress data
        """
        try:
            percent = d.get('_percent_str', 'N/A').strip()
            downloaded = d.get('_downloaded_bytes_str', '?')
            total = d.get('_total_bytes_str', '?')
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()

            # Build progress bar
            bar_length = 30
            if '_percent_str' in d:
                try:
                    percent_num = float(d['_percent_str'].strip('%'))
                    filled = int(bar_length * percent_num / 100)
                    bar = '#' * filled + '-' * (bar_length - filled)
                except (ValueError, TypeError):
                    bar = '-' * bar_length
            else:
                bar = '-' * bar_length

            # Print progress bar inline
            print(f"\r  [{bar}] {percent} | {downloaded}/{total} | {speed} | ETA: {eta}", end='', flush=True)

            return {
                'status': 'downloading',
                'percent': percent,
                'downloaded': downloaded,
                'total': total,
                'speed': speed,
                'eta': eta,
                'bar': bar
            }

        except Exception:
            pass

        return {'status': 'downloading'}

    def _report_postprocessing(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Show spinner during postprocessing.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Structured progress data
        """
        postprocessor = d.get('postprocessor', 'Processing')

        if not hasattr(self, '_spinner'):
            from tea.utils.spinner import Spinner
            self._spinner = Spinner(f"[{postprocessor}]")
            self._spinner.start()

        return {'status': 'postprocessing', 'postprocessor': postprocessor}

    def _report_finished(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report download finished.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Structured progress data
        """
        # Print newline to finish the progress bar
        print()

        # Stop postprocessing spinner if running
        if hasattr(self, '_spinner') and self._spinner:
            self._spinner.stop("[OK] Post-processing complete")
            self._spinner = None

        return {
            'status': 'finished',
            'filename': d.get('filename'),
            'total_bytes': d.get('total_bytes')
        }

    def _report_error(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """
        Report download error.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Structured progress data
        """
        error = d.get('error', 'Unknown error')

        # Stop postprocessing spinner if running
        if hasattr(self, '_spinner') and self._spinner:
            self._spinner.stop()
            self._spinner = None

        if self._logger:
            self._logger.error(f"Download error: {error}")

        return {
            'status': 'error',
            'error': error
        }

    def reset(self) -> None:
        """Reset progress tracking state."""
        self._last_percent = -1
        # Clean up spinner if exists
        if hasattr(self, '_spinner') and self._spinner:
            self._spinner.stop()
            self._spinner = None


# Convenience function for backward compatibility
def create_progress_hook(logger=None):
    """
    Create a progress hook function for yt-dlp.

    Args:
        logger: Logger instance for logging

    Returns:
        Progress hook function
    """
    reporter = ProgressReporter(logger)
    return reporter.progress_hook
