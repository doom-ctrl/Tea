# Contributing to Tea

Thank you for your interest in contributing to Tea! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style Guidelines](#code-style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Commit Message Conventions](#commit-message-conventions)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Development Setup

### Prerequisites

- Python 3.10 or higher
- FFmpeg (must be in system PATH)
- Git

### Setup Steps

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tea.git
   cd tea
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

5. Verify your setup:
   ```bash
   pytest -v
   ```

## Running Tests

### Run All Tests

```bash
pytest -v
```

### Run Specific Test File

```bash
pytest tests/test_downloader.py -v
```

### Run with Coverage

```bash
pytest --cov=tea --cov-report=html
```

### Run Only Unit Tests

```bash
pytest -m "not integration" -v
```

### Run Only Integration Tests

```bash
pytest -m integration -v
```

## Code Style Guidelines

### Python Style

- Use **Black** for code formatting (line length: 100)
- Use **isort** for import sorting
- Follow **PEP 8** conventions where not overridden by Black
- Use **Google style docstrings** for all functions and classes

### Type Hints

- All functions must have type hints for parameters and return values
- Import types from `typing` module
- Use `Optional[T]` for nullable types

Example:
```python
from typing import Optional, List

def download_video(url: str, quality: str = "5") -> Optional[str]:
    """Download a video with specified quality.

    Args:
        url: The YouTube video URL.
        quality: The quality preset (default: "5" for audio).

    Returns:
        Path to downloaded file, or None if failed.
    """
    ...
```

### Import Order

1. Standard library imports
2. Third-party imports
3. Local imports (from tea.*)

Use isort to maintain this automatically.

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `DownloadService`)
- **Functions/variables**: `snake_case` (e.g., `download_video`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private members**: `_leading_underscore` (e.g., `_config`)

### Error Handling

- Use custom exceptions from `tea.exceptions`
- Always include helpful error messages
- Validate inputs at module boundaries
- Use specific exception types, not generic `Exception`

Example:
```python
from tea.exceptions import ValidationError, DownloadError

def download_video(url: str) -> str:
    if not validate_url(url):
        raise ValidationError(
            message="Invalid YouTube URL",
            field="url",
            value=url,
        )
    ...
```

### Logging

- Use the `_logger` instance for all logging
- Use appropriate log levels:
  - `logger.debug()` - Detailed debugging info
  - `logger.info()` - General informational messages
  - `logger.warning()` - Warning messages
  - `logger.error()` - Error messages

## Pull Request Process

### Before Submitting

1. **Update tests** - Add tests for new functionality
2. **Run tests** - Ensure all tests pass
3. **Format code** - Run `black .` and `isort .`
4. **Lint code** - Run `ruff check .`
5. **Update docs** - Update relevant documentation

### PR Description

Your pull request should include:

- **Clear title** describing the change
- **Description** of what was changed and why
- **Related issues** (e.g., "Fixes #123")
- **Testing** description of how you tested
- **Screenshots** for UI changes (if applicable)

### PR Review Process

1. Automated checks must pass (CI/CD)
2. At least one maintainer approval required
3. Address all review feedback
4. Squash commits if requested
5. Maintain clean commit history

## Commit Message Conventions

Follow these guidelines for commit messages:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```
feat(downloader): Add support for YouTube Shorts

fix(cli): Handle empty URL input gracefully

docs(contributing): Add PR review guidelines

test(history): Add tests for duplicate detection

refactor(config): Simplify validation logic
```

### Subject Line

- Use present tense ("add" not "added")
- Use imperative mood ("move" not "moves")
- Capitalize first letter
- Don't end with period
- Limit to 50 characters

### Body

- Wrap at 72 characters
- Explain what and why, not how
- Use bullet points for multiple items

### Footer

- Reference issues: "Closes #123"
- Add breaking changes: "BREAKING CHANGE: ..."
- Sign-off for commits: "Signed-off-by: ..."

## Development Tips

### Debugging

- Use `pytest --pdb` to drop into debugger on failure
- Use `logger.debug()` messages with verbose logging
- Run with `TEA_DEBUG=1` environment variable

### Testing Tips

- Use fixtures in `tests/conftest.py` for common setup
- Mock external dependencies (YouTube API, filesystem)
- Keep tests fast - mock when possible
- Use descriptive test names

### Adding Features

1. Create feature branch: `git checkout -b feature/my-feature`
2. Implement with tests
3. Update documentation
4. Submit PR

### Reporting Bugs

1. Check existing issues first
2. Use bug report template
3. Include:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/tracebacks

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and ideas
- **Documentation**: See `docs/` directory

Thank you for contributing to Tea!
