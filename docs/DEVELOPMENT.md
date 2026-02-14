# Development Environment Setup

This guide helps you set up a development environment for contributing to Tea.

## Prerequisites

### Required Software

- **Python 3.10 or higher**
  - Download from [python.org](https://www.python.org/downloads/)
  - On macOS: `brew install python`
  - On Windows: Use [python.org installer](https://www.python.org/downloads/windows/)
  - On Linux: `sudo apt install python3.10`

- **Git**
  - Download from [git-scm.com](https://git-scm.com/)
  - On macOS: `brew install git`
  - On Windows: Use [Git for Windows](https://gitforwindows.org/)
  - On Linux: `sudo apt install git`

- **FFmpeg** (required for media processing)
  - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - On macOS: `brew install ffmpeg`
  - On Windows: Use [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
  - On Linux: `sudo apt install ffmpeg`

- **Code Editor** (recommended)
  - [VS Code](https://code.visualstudio.com/)
  - [PyCharm](https://www.jetbrains.com/pycharm/)
  - [Sublime Text](https://www.sublimetext.com/)

### Verify Prerequisites

Open a terminal and verify installations:

```bash
python --version    # Should be 3.10+
git --version      # Should be 1.8+
ffmpeg -version     # Should be 4.0+
```

## Repository Setup

### 1. Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/tea.git
cd tea
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
# Install editable mode with dev dependencies
pip install -e ".[dev]"
```

This installs:
- Production dependencies (yt-dlp, requests, etc.)
- Testing tools (pytest, pytest-cov, pytest-mock)
- Code quality tools (black, isort, ruff, mypy)

### 4. Verify Installation

```bash
# Run tests
pytest -v

# Run imports
python -c "import tea; print('OK')"

# Check tools
black --version
isort --version
ruff --version
```

## Development Workflow

### Git Workflow

```bash
# 1. Update your fork
git fetch upstream
git rebase upstream/main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and commit
git add .
git commit -m "feat: Add my feature"

# 4. Push to your fork
git push origin feature/my-feature

# 5. Create pull request on GitHub
```

### Running Tests

**Run all tests:**
```bash
pytest -v
```

**Run with coverage:**
```bash
pytest --cov=tea --cov-report=html
open htmlcov/index.html  # macOS
# View htmlcov/index.html in browser
```

**Run specific test file:**
```bash
pytest tests/test_downloader.py -v
```

**Run with verbose output:**
```bash
pytest -vv -s
```

**Skip slow tests:**
```bash
pytest -m "not slow" -v
```

### Code Formatting

**Format code:**
```bash
black tea/ tests/
```

**Sort imports:**
```bash
isort tea/ tests/
```

**Check formatting:**
```bash
black --check tea/ tests/
isort --check-only tea/ tests/
```

### Linting

**Run linter:**
```bash
ruff check tea/
```

**Auto-fix issues:**
```bash
ruff check --fix tea/
```

### Type Checking

**Run mypy:**
```bash
mypy tea/
```

## IDE Setup

### Visual Studio Code

1. Install extensions:
   - Python
   - Pylance
   - Python Test Explorer
   - Black Formatter
   - isort

2. Configure workspace (`.vscode/settings.json`):
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": false,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### PyCharm

1. Open Settings → Project → Python Interpreter
2. Add your virtual environment
3. Enable Black: Settings → Tools → External Tools → Black
4. Configure pytest: Settings → Tools → Python Integrated Tools → pytest

## Project Structure

```
tea/
├── tea/                    # Main package
│   ├── __init__.py
│   ├── cli.py              # Command-line interface
│   ├── downloader.py        # Download orchestration
│   ├── config.py           # Configuration management
│   ├── history.py          # Download history
│   ├── info.py            # Content information
│   ├── progress.py         # Progress reporting
│   ├── ffmpeg.py           # FFmpeg operations
│   ├── timestamps.py       # Timestamp handling
│   ├── search.py           # Search functionality
│   ├── logger.py           # Logging setup
│   ├── exceptions.py       # Custom exceptions
│   ├── constants.py        # Application constants
│   ├── ai/                # AI features
│   │   └── filename_cleaner.py
│   └── utils/             # Utilities
│       ├── security.py       # Security utilities
│       └── spinner.py       # CLI spinner
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures
│   ├── test_*.py           # Unit tests
│   └── integration/         # Integration tests
├── docs/                    # Documentation
│   ├── API.md
│   └── DEVELOPMENT.md        # This file
├── tea.py                   # Entry point
├── pyproject.toml            # Project config
├── requirements.txt           # Production dependencies
├── CLAUDE.md               # AI assistant instructions
├── CONTRIBUTING.md           # Contribution guidelines
├── README.md                # Project readme
└── .github/                 # GitHub configs
    └── workflows/             # CI/CD workflows
```

## Common Tasks

### Adding a New Feature

1. Create feature branch
2. Implement feature with tests
3. Run formatter and linter
4. Run tests
5. Update documentation
6. Commit and push
7. Create pull request

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Use ipdb for better debugging
pip install ipdb
pytest --pdbcls=IPython.terminal.debugger:TerminalPdb --pdb
```

### Testing CLI Interactions

Use `pytest` fixtures to mock user input:

```python
from unittest.mock import patch

def test_get_urls_interactive(mock_input):
    mock_input.return_value = "https://youtube.com/watch?v=xxx"
    cli = CLI()
    urls = cli.get_urls_interactive()
    assert len(urls) == 1
```

### Mocking External Services

```python
from unittest.mock import MagicMock

def test_download_with_mock():
    mock_ytdlp = MagicMock()
    mock_ytdlp.download.return_value = None

    with patch("tea.downloader.YoutubeDL", return_value=mock_ytdlp):
        result = service.download_single_video(url, output)
        assert result["success"] is True
```

## Troubleshooting

### Import Errors

**Problem:** `ImportError: No module named 'tea'`

**Solution:**
```bash
pip install -e .
```

### Tests Failing

**Problem:** Tests fail with `FileNotFoundError`

**Solution:** Ensure you're in project root:
```bash
cd /path/to/tea
pytest
```

### FFmpeg Not Found

**Problem:** `FFmpegError: FFmpeg not found`

**Solution:** Install FFmpeg and verify:
```bash
ffmpeg -version
```

### Type Checking Errors

**Problem:** Mypy reports many errors

**Solution:** Focus on new code, ignore existing issues:
```bash
mypy tea/ --ignore-missing-imports
```

## Resources

- [Testing Best Practices](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [PEP 8](https://peps.python.org/pep-0008/)

## Getting Help

- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas
- **Contributing Guide:** See [CONTRIBUTING.md](../CONTRIBUTING.md)

Happy hacking!
