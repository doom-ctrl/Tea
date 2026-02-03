# ☕ Tea - YouTube Video & Audio Downloader

**Brew your favorite YouTube videos and playlists with ease**

![Tea Banner](https://img.shields.io/badge/Tea-v1.0.0-cyan?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

> 🎵 Download YouTube videos, playlists, and channels. Split them by timestamps. All with one command: `tea`

---

## ✨ Features

- ☕ **Simple CLI** - Just type `tea` and you're brewing
- 🎥 **High-Quality Downloads** - Up to 1080p video or 192kbps MP3 audio
- 📂 **Smart Organization** - Playlists get their own folders automatically
- ✂️ **Timestamp Splitting** - Split videos/audio by timestamps (JSON, manual, or paste)
- ⚡ **Concurrent Downloads** - Download multiple videos simultaneously
- 🎵 **Audio-Only Mode** - Extract MP3 from any video
- 📺 **Channel Support** - Download entire YouTube channels
- 🎯 **Zero Configuration** - Works out of the box

---

## 🚀 Quick Start

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/tea.git
cd tea

# 2. Install dependencies
pip install -r requirements.txt

# 3. Make sure FFmpeg is installed
ffmpeg -version
```

### Usage

```bash
# Run Tea
python tea.py

# Or add to PATH and use globally
tea
```

---

## 📖 Usage Examples

### Download a Single Video

```bash
tea
# Enter URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
# Select quality: 1 (Best)
# Output: downloads/
```

### Download as MP3

```bash
tea
# Enter URL: https://www.youtube.com/watch?v=I2LaN6BQj3E
# Select quality: 5 (Audio only)
# ✓ Downloads high-quality MP3
```

### Download and Split by Timestamps

```bash
tea
# Enter URL: https://www.youtube.com/watch?v=I2LaN6BQj3E
# Select quality: 5 (Audio only)
# Split? y
# Load from JSON: timestamps.json
# ✓ Downloads full video + creates individual clips
```

### Download Entire Playlist

```bash
tea
# Enter URL: https://www.youtube.com/playlist?list=PLxxxxxx
# ✓ Downloads all videos in organized folder
```

### Multiple Videos at Once

```bash
tea
# Enter URLs: url1, url2, url3
# Concurrent downloads: 3
# ✓ Downloads 3 videos simultaneously
```

---

## ✂️ Timestamp Splitting

Tea supports **3 ways** to provide timestamps:

### 1. Manual Entry
```
Choose method: 1
Clip 1 - Start: 0:00
Clip 1 - End: 5:30
Clip 1 - Title: Intro
```

### 2. Paste YouTube Comments
```
Choose method: 2
Paste timestamps:
0:00 Intro
5:30 Main Content
10:00 Outro
```

### 3. JSON File (Recommended!)
```
Choose method: 3
File path: timestamps.json
```

**JSON Format:**
```json
{
  "video_title": "My Video",
  "clips": [
    {
      "start": "0:00",
      "end": "5:30",
      "title": "Intro"
    },
    {
      "start": "5:30",
      "end": "10:00",
      "title": "Main Content"
    }
  ]
}
```

---

## ⚙️ Requirements

- **Python 3.10+** - [Download Python](https://www.python.org/downloads/)
- **FFmpeg** - [Download FFmpeg](https://ffmpeg.org/download.html)
- **yt-dlp** - Installed via `pip install -r requirements.txt`

### Installing FFmpeg

**Windows:**
```bash
choco install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

---

## 📁 Project Structure

```
tea/
├── tea.py                          # Main application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── LICENSE                         # MIT License
└── examples/
    └── bossa-nova-timestamps.json  # Example timestamp file
```

---

## 🛠️ Configuration

Modify these variables in `tea.py`:

```python
MAX_RETRIES = 3                      # Download retry attempts
RETRY_DELAY = 2                      # Delay between retries (seconds)
MAX_CONCURRENT_WORKERS = 5           # Max simultaneous downloads
DEFAULT_CONCURRENT_WORKERS = 3       # Default concurrent downloads
```

---

## 🎯 Supported Content

| Type | Example URL | Supported |
|------|------------|-----------|
| Single Video | `youtube.com/watch?v=...` | ✅ |
| Playlist | `youtube.com/playlist?list=...` | ✅ |
| Channel | `youtube.com/@channelname` | ✅ |
| Shorts | `youtube.com/shorts/...` | ✅ |
| Live Streams | `youtube.com/watch?v=...` | ✅ |

---

## 🐛 Troubleshooting

### "FFmpeg not found"
Install FFmpeg using the instructions above.

### "No module named 'yt_dlp'"
```bash
pip install yt-dlp
```

### "Permission denied"
```bash
pip install --user -r requirements.txt
```

### Splitting doesn't work
Make sure:
1. FFmpeg is installed
2. You selected a single video (not playlist)
3. Timestamps are in correct format (MM:SS or HH:MM:SS)

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **yt-dlp** - Powerful YouTube downloader library
- **FFmpeg** - Multimedia processing framework
- **Bossa Nova lovers** - For the inspiration ☕🎵

---

## 📞 Support

Having issues? Please:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/yourusername/tea/issues)
3. Create a [new issue](https://github.com/yourusername/tea/issues/new)

---

## ☕ Made with Tea

Brew your favorite content, one cup at a time.

**Star ⭐ this repo if Tea helped you!**

---

<p align="center">
  <img src="https://img.shields.io/github/stars/yourusername/tea?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/github/forks/yourusername/tea?style=social" alt="GitHub forks">
</p>
