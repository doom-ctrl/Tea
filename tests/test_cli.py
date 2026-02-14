"""
Tests for CLI module.

Tests cover:
- Menu display
- User input handling
- URL parsing
- Quality selection
- Output directory selection
- Batch file handling
"""

import pytest
from unittest.mock import MagicMock, patch, call
from io import StringIO
import sys

from tea.cli import CLI
from tea.exceptions import ValidationError


@pytest.mark.unit
class TestCLI:
    """Test CLI class functionality."""

    def test_init(self, mock_logger: MagicMock):
        """Test CLI initialization."""
        cli = CLI(logger=mock_logger)
        assert cli._logger is mock_logger

    def test_show_banner(self, cli: CLI, capsys):
        """Test banner display."""
        cli.show_banner()
        captured = capsys.readouterr()
        assert "Tea" in captured.out or "☕" in captured.out

    def test_show_help(self, cli: CLI, capsys):
        """Test help display."""
        cli.show_help()
        captured = capsys.readouterr()
        assert "help" in captured.out.lower()

    def test_parse_multiple_urls_comma_separated(self, cli: CLI):
        """Test parsing comma-separated URLs."""
        input_str = "https://youtu.be/video1,https://youtu.be/video2"
        urls = cli.parse_multiple_urls(input_str)
        assert len(urls) == 2

    def test_parse_multiple_urls_space_separated(self, cli: CLI):
        """Test parsing space-separated URLs."""
        input_str = "https://youtu.be/video1 https://youtu.be/video2"
        urls = cli.parse_multiple_urls(input_str)
        assert len(urls) == 2

    def test_parse_multiple_urls_newline_separated(self, cli: CLI):
        """Test parsing newline-separated URLs."""
        input_str = "https://youtu.be/video1\nhttps://youtu.be/video2"
        urls = cli.parse_multiple_urls(input_str)
        assert len(urls) == 2

    def test_parse_multiple_urls_empty(self, cli: CLI):
        """Test parsing empty input."""
        urls = cli.parse_multiple_urls("")
        assert urls == []

    def test_parse_multiple_urls_invalid(self, cli: CLI):
        """Test parsing with invalid URLs."""
        input_str = "https://youtu.be/video1 not-a-url https://youtu.be/video2"
        urls = cli.parse_multiple_urls(input_str)
        assert len(urls) == 2  # Only valid URLs returned

    @patch("builtins.input")
    def test_get_urls_interactive(self, mock_input, cli: CLI):
        """Test getting URLs interactively."""
        mock_input.return_value = "https://youtu.be/video1,https://youtu.be/video2"
        urls = cli.get_urls_interactive()
        assert len(urls) == 2

    def test_load_urls_from_file(self, cli: CLI, tmp_path):
        """Test loading URLs from batch file."""
        batch_file = tmp_path / "urls.txt"
        batch_file.write_text("https://youtu.be/video1\nhttps://youtu.be/video2\n")

        urls = cli.load_urls_from_file(str(batch_file))
        assert len(urls) == 2

    def test_load_urls_from_file_nonexistent(self, cli: CLI):
        """Test loading from nonexistent file."""
        with pytest.raises(ValidationError):
            cli.load_urls_from_file("nonexistent.txt")

    def test_load_urls_from_file_with_comments(self, cli: CLI, tmp_path):
        """Test loading URLs from file with comment lines."""
        batch_file = tmp_path / "urls.txt"
        batch_file.write_text("# This is a comment\nhttps://youtu.be/video1\n")

        urls = cli.load_urls_from_file(str(batch_file))
        assert len(urls) == 1

    @patch("builtins.input")
    def test_select_quality(self, mock_input, cli: CLI):
        """Test quality selection."""
        mock_input.return_value = "5"
        quality = cli.select_quality()
        assert quality == "5"

    @patch("builtins.input")
    def test_select_quality_with_retry(self, mock_input, cli: CLI):
        """Test quality selection with invalid then valid input."""
        mock_input.side_effect = ["invalid", "5"]
        quality = cli.select_quality()
        assert quality == "5"

    @patch("builtins.input")
    def test_select_output_directory(self, mock_input, cli: CLI, tmp_path):
        """Test output directory selection."""
        test_dir = tmp_path / "test_output"
        mock_input.return_value = str(test_dir)
        result = cli.select_output_directory()
        assert test_dir.name in result

    @patch("builtins.input")
    def test_select_concurrent(self, mock_input, cli: CLI):
        """Test concurrent worker count selection."""
        mock_input.return_value = "3"
        count = cli.select_concurrent()
        assert count == 3

    @patch("builtins.input")
    def test_select_concurrent_invalid_then_valid(self, mock_input, cli: CLI):
        """Test concurrent selection with invalid then valid input."""
        mock_input.side_effect = ["0", "3"]
        count = cli.select_concurrent()
        assert count == 3

    def test_show_supported_formats(self, cli: CLI, capsys):
        """Test display of supported formats."""
        cli.show_supported_formats()
        captured = capsys.readouterr()
        assert "format" in captured.out.lower()


@pytest.mark.unit
class TestCLIMenus:
    """Test CLI menu functionality."""

    @patch("builtins.input")
    def test_main_menu_exit(self, mock_input, cli: CLI):
        """Test main menu exit."""
        mock_input.return_value = "0"
        # Should not raise exception
        try:
            cli.show_main_menu()
        except SystemExit:
            pass

    @patch("builtins.input")
    def test_duplicate_action_menu(self, mock_input, cli: CLI):
        """Test duplicate action selection menu."""
        mock_input.return_value = "s"  # Skip
        action = cli.ask_duplicate_action("https://youtu.be/video1")
        assert action == "skip"

    @patch("builtins.input")
    def test_timestamp_choice_menu(self, mock_input, cli: CLI):
        """Test timestamp source choice menu."""
        mock_input.return_value = "1"  # Manual entry
        choice = cli.select_timestamp_source()
        assert choice == "manual"


@pytest.mark.unit
class TestCLIValidation:
    """Test CLI input validation."""

    def test_validate_url_valid(self, cli: CLI):
        """Test URL validation with valid URLs."""
        assert cli.validate_url("https://youtu.be/video1") is True

    def test_validate_url_invalid(self, cli: CLI):
        """Test URL validation with invalid URLs."""
        with pytest.raises(ValidationError):
            cli.validate_url("not-a-url")

    def test_validate_choice_valid(self, cli: CLI):
        """Test choice validation with valid choice."""
        result = cli.validate_choice("b", ["a", "b", "c"])
        assert result == "b"

    def test_validate_choice_invalid(self, cli: CLI):
        """Test choice validation with invalid choice."""
        with pytest.raises(ValidationError):
            cli.validate_choice("d", ["a", "b", "c"])


@pytest.fixture
def cli(mock_logger: MagicMock) -> CLI:
    """Create CLI instance for testing."""
    return CLI(logger=mock_logger)
