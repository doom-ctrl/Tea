import sys
from yt_dlp import YoutubeDL
import os
import re
import time
import subprocess
import json
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_CONCURRENT_WORKERS = 5
DEFAULT_CONCURRENT_WORKERS = 3


def show_banner():
    """Display beautiful Tea banner"""
    print()
    print("   +-------------------------------+")
    print("   |                               |")
    print("   |       Tea v1.0.0              |")
    print("   |       YouTube Downloader      |")
    print("   |                               |")
    print("   +-------------------------------+")
    print()
    print("-" * 60)
    print("  Tea - Brew your favorite videos")
    print("-" * 60)
    print()


def show_supported_formats():
    """Show supported URL formats"""
    print("SUPPORTED INPUT FORMATS:")
    print("   - Single URL: Just paste one YouTube URL")
    print("   - Comma-separated: url1, url2, url3")
    print("   - Space-separated: url1 url2 url3")
    print("   - Multi-line: Press Enter without typing, then one URL per line")
    print()
    print("SUPPORTED CONTENT TYPES:")
    print("   Videos: https://www.youtube.com/watch?v=...")
    print("   Shorts: https://www.youtube.com/shorts/...")
    print("   Playlists: https://www.youtube.com/playlist?list=...")
    print("   Channels: https://www.youtube.com/@channelname")
    print("   Channels: https://www.youtube.com/channel/UC...")
    print("   Channels: https://www.youtube.com/c/channelname")
    print("   Channels: https://www.youtube.com/user/username")
    print()


def get_urls_interactive():
    """Get YouTube URLs with interactive prompt"""

    print("Example URLs:")
    print("   * https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print("   * https://youtu.be/dQw4w9WgXcQ")
    print("   * https://www.youtube.com/playlist?list=PLxxxxxx")
    print()

    url_input = input("Enter YouTube URL(s): ")
    return url_input


def select_quality():
    """Interactive quality selection"""

    print("Select video quality:")
    print("   1. Best available (1080p)")
    print("   2. High (720p)")
    print("   3. Medium (480p)")
    print("   4. Low (360p)")
    print("   5. Audio only (MP3)")

    choice = input("Enter choice (1-5, default=1): ").strip()

    quality_map = {
        '1': 'best',
        '2': '720p',
        '3': '480p',
        '4': '360p',
        '5': 'audio'
    }

    return quality_map.get(choice, 'best')


def select_output_directory():
    """Select output directory"""
    output = input("Output directory (press Enter for default): ").strip()
    return output if output else 'downloads'


def select_concurrent():
    """Select number of concurrent downloads"""
    workers = input("Concurrent downloads (1-5, default=3): ").strip()
    try:
        return max(1, min(5, int(workers) if workers else 3))
    except ValueError:
        return 3


def show_download_summary(successful, failed, output_path):
    """Show download summary"""

    print()

    if successful:
        print("[OK] Successful Downloads:")
        print("-" * 50)
        for item in successful:
            content_type = item.get('type', 'video')
            if content_type == 'playlist':
                title = item.get('title', 'Unknown Playlist')
                count = item.get('count', 0)
                print(f"   Playlist: {title} ({count} videos)")
            elif content_type == 'channel':
                title = item.get('title', 'Unknown Channel')
                count = item.get('count', 0)
                print(f"   Channel: {title} ({count} videos)")
            else:
                title = item.get('title', 'Unknown')
                print(f"   Video: {title}")
        print()

    if failed:
        print("[ERROR] Failed Downloads:")
        print("-" * 50)
        for item in failed:
            print(f"   * {item.get('url', 'Unknown')}: {item.get('message', 'Error')}")
        print()

    print("Tea is ready! {} download(s) completed successfully!".format(len(successful)))
    print("Files saved to: {}".format(output_path))


def time_to_seconds(timestamp: str) -> int:
    """Convert MM:SS or HH:MM:SS to seconds"""
    parts = timestamp.strip().split(':')
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return 0
    return 0


def parse_timestamp_list(text: str, video_duration: Optional[str] = None) -> List[Dict]:
    """Parse timestamps from various formats"""
    timestamps = []
    
    if '-' in text and (',' in text or '\n' not in text):
        parts = re.split(r',|\n', text)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            match = re.search(r'(\d+:\d+(?::\d+)?)\s*-\s*(\d+:\d+(?::\d+)?)\s*(.*)?', part)
            if match:
                timestamps.append({
                    'start': match.group(1),
                    'end': match.group(2),
                    'title': match.group(3).strip() if match.group(3) else f"Clip {len(timestamps)+1}"
                })
    else:
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        
        for i, line in enumerate(lines):
            match = re.search(r'(\d+:\d+(?::\d+)?)\s+(.+)', line)
            if match:
                start = match.group(1)
                title = match.group(2).strip()
                
                end = None
                if i + 1 < len(lines):
                    next_match = re.search(r'(\d+:\d+(?::\d+)?)', lines[i + 1])
                    if next_match:
                        end = next_match.group(1)
                elif video_duration:
                    end = video_duration
                
                if end:
                    timestamps.append({
                        'start': start,
                        'end': end,
                        'title': title
                    })
    
    return timestamps


def load_timestamps_from_json(filepath: str) -> List[Dict]:
    """Load timestamps from a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, dict) and 'clips' in data:
            clips = data['clips']
        elif isinstance(data, list):
            clips = data
        else:
            print("Invalid JSON format")
            return []
        
        timestamps = []
        for i, clip in enumerate(clips, 1):
            if 'start' in clip and 'end' in clip:
                timestamps.append({
                    'start': clip['start'],
                    'end': clip['end'],
                    'title': clip.get('title', f'Clip {i}')
                })
            else:
                print(f"Skipping clip {i}: Missing 'start' or 'end'")
        
        print(f"Loaded {len(timestamps)} clips from {filepath}")
        return timestamps
        
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return []
    except Exception as e:
        print(f"Error loading file: {e}")
        return []


def get_timestamps_interactive() -> List[Dict]:
    """Get timestamps interactively from user"""
    print("\n=== Enter timestamps to split the video")
    print("-" * 60)
    print("Supported formats:")
    print("   * Range: 0:00-5:30, 5:30-10:00")
    print("   * YouTube style: One timestamp per line (0:00 Intro)")
    print("   * JSON file: Load from timestamps.json")
    print()
    print("Choose input method:")
    print("   1. Manual entry (one by one)")
    print("   2. Paste timestamp list")
    print("   3. Load from JSON file")
    print("   4. Skip splitting")
    print()
    
    choice = input("Enter choice (1-4, default=4): ").strip()
    
    if choice not in ['1', '2', '3']:
        return []
    
    timestamps = []
    
    if choice == '1':
        print("\nEnter timestamps (press Enter without typing to finish)")
        print("-" * 60)
        clip_num = 1
        while True:
            print(f"\nClip {clip_num}:")
            start = input("  Start time (MM:SS or HH:MM:SS): ").strip()
            if not start:
                break
            
            end = input("  End time: ").strip()
            if not end:
                print("  End time required. Clip skipped.")
                continue
            
            title = input("  Title (optional, press Enter to skip): ").strip()
            if not title:
                title = f"Clip {clip_num}"
            
            timestamps.append({
                'start': start,
                'end': end,
                'title': title
            })
            
            print(f"  Added: {start} - {end} | {title}")
            clip_num += 1
    
    elif choice == '2':
        print("\nPaste your timestamps below")
        print("Examples:")
        print("   * 0:00-1:54, 1:54-5:46, 5:46-8:33")
        print("   * 0:00 Intro")
        print("     1:54 Main Content")
        print("     5:46 Conclusion")
        print()
        print("Press Enter twice when finished:")
        print("-" * 60)
        
        lines = []
        empty_count = 0
        while True:
            line = input()
            if not line.strip():
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                lines.append(line)
        
        if lines:
            timestamps = parse_timestamp_list('\n'.join(lines))
    
    elif choice == '3':
        print("\nEnter path to JSON file:")
        print("   Example: timestamps.json or C:\\path\\to\\timestamps.json")
        print()
        filepath = input("File path: ").strip()
        filepath = filepath.strip('"').strip("'")
        
        timestamps = load_timestamps_from_json(filepath)
    
    return timestamps
    
    return timestamps


def split_video_by_timestamps(video_path: str, timestamps: List[Dict], output_dir: str, audio_only: bool = False) -> List[Dict]:
    """Split a video file into multiple clips based on timestamps"""
    results = []
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[OK] Splitting into {len(timestamps)} clips...")
    print("-" * 60)

    for i, timestamp in enumerate(timestamps, 1):
        start = timestamp['start']
        end = timestamp['end']
        title = timestamp.get('title', f'Clip {i}')

        safe_title = re.sub(r'[<>:"/\\|?*&]', '_', title)
        safe_title = safe_title.strip()[:100]

        _, ext = os.path.splitext(video_path)
        if audio_only:
            output_path = os.path.join(output_dir, f"{i:02d}-{safe_title}.mp3")
        else:
            output_path = os.path.join(output_dir, f"{i:02d}-{safe_title}{ext}")

        print(f"[OK] Clip {i}/{len(timestamps)}: {title}")
        print(f"   Time: {start} -> {end}")

        try:
            if audio_only:
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', start,
                    '-to', end,
                    '-vn',
                    '-acodec', 'libmp3lame',
                    '-q:a', '2',
                    '-avoid_negative_ts', '1',
                    '-y',
                    output_path
                ]
            else:
                cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', start,
                    '-to', end,
                    '-c', 'copy',
                    '-avoid_negative_ts', '1',
                    '-y',
                    output_path
                ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            results.append({
                'success': True,
                'clip': i,
                'title': title,
                'path': output_path
            })
            print(f"   [OK] Saved to: {os.path.basename(output_path)}")

        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            results.append({
                'success': False,
                'clip': i,
                'title': title,
                'error': error_msg
            })
            print(f"   [ERROR] Failed: {error_msg[:100]}")
        except FileNotFoundError:
            results.append({
                'success': False,
                'clip': i,
                'title': title,
                'error': 'FFmpeg not found. Please install FFmpeg.'
            })
            print(f"   [ERROR] FFmpeg not found. Install from: https://ffmpeg.org/")
            break

    return results


def find_downloaded_video(output_path: str, title: str) -> Optional[str]:
    """Find the downloaded video or audio file by title"""
    extensions = ['.mp4', '.mkv', '.webm', '.avi', '.mp3']
    
    for ext in extensions:
        for filename in os.listdir(output_path):
            if filename.endswith(ext):
                if title and any(word.lower() in filename.lower() for word in title.split()[:3]):
                    return os.path.join(output_path, filename)
    
    for ext in extensions:
        for filename in os.listdir(output_path):
            if filename.endswith(ext):
                return os.path.join(output_path, filename)
    
    return None


def show_download_progress(thread_id: int, url: str, content_type: str):
    """Show download progress for a single item"""
    if content_type == 'playlist':
        print(f"[Thread {thread_id}] Brewing playlist...")
    elif content_type == 'channel':
        print(f"[Thread {thread_id}] Brewing channel...")
    else:
        print(f"[Thread {thread_id}] Brewing video...")


@lru_cache(maxsize=128)
def get_url_info(url: str) -> Tuple[str, Dict]:
    """
    Get URL information with caching to avoid duplicate yt-dlp calls.
    Returns (content_type, info_dict) for efficient reuse.

    Args:
        url (str): YouTube URL to analyze

    Returns:
        Tuple[str, Dict]: (content_type, info_dict) where content_type is 'video', 'playlist', or 'channel'
    """
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'skip_download': True,
            'playlist_items': '1',
        }

        with YoutubeDL(ydl_opts) as ydl:
            video_info = ydl.extract_info(url, download=False)

            if video_info is None:
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                if '/@' in url or '/channel/' in url or '/c/' in url or '/user/' in url:
                    return 'channel', {}
                elif 'list' in query_params:
                    return 'playlist', {}
                else:
                    return 'video', {}

            content_type = video_info.get('_type', 'video')

            if content_type == 'playlist':
                if video_info.get('uploader_id') and ('/@' in url or '/channel/' in url or '/c/' in url or '/user/' in url):
                    return 'channel', video_info
                else:
                    return 'playlist', video_info

            return content_type, video_info

    except Exception:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        if '/@' in url or '/channel/' in url or '/c/' in url or '/user/' in url:
            return 'channel', {}
        elif 'list' in query_params:
            return 'playlist', {}
        else:
            return 'video', {}


def get_content_type(url: str) -> str:
    """
    Get the content type of a YouTube URL.

    Args:
        url (str): YouTube URL to analyze

    Returns:
        str: 'video', 'playlist', or 'channel'
    """
    content_type, _ = get_url_info(url)
    return content_type


def parse_multiple_urls(input_string: str) -> List[str]:
    """
    Parse multiple URLs from input string separated by commas, spaces, newlines, or mixed formats.
    Handles complex mixed separators like "url1, url2 url3\nurl4".

    Args:
        input_string (str): String containing one or more URLs

    Returns:
        List[str]: List of cleaned URLs
    """
    urls = re.split(r'[,\s\n\t]+', input_string.strip())
    urls = [url.strip() for url in urls if url.strip()]

    valid_urls = []
    invalid_count = 0
    for url in urls:
        if ('youtube.com' in url or 'youtu.be' in url) and (
            '/watch?' in url or
            '/playlist?' in url or
            '/@' in url or
            '/channel/' in url or
            '/c/' in url or
            '/user/' in url or
            'youtu.be/' in url
        ):
            valid_urls.append(url)
        elif url:
            print(f"[WARNING] Skipping invalid URL: {url}")
            invalid_count += 1

    if invalid_count > 0:
        print(
            f"Found {len(valid_urls)} valid YouTube URLs, skipped {invalid_count} invalid entries")

    return valid_urls


def get_available_formats(url: str) -> None:
    """
    List available formats for debugging purposes.

    Args:
        url (str): YouTube URL to check formats for
    """
    ydl_opts = {
        'listformats': True,
        'quiet': False
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
    except Exception as error:
        print(f"Error listing formats: {str(error)}")


def download_single_video(url: str, output_path: str, thread_id: int = 0, audio_only: bool = False) -> dict:
    """
    Download a single YouTube video, playlist, or channel with retry mechanism.

    Args:
        url (str): YouTube URL to download (video, playlist, or channel)
        output_path (str): Directory to save the download
        thread_id (int): Thread identifier for logging
        audio_only (bool): If True, download audio only in MP3 format

    Returns:
        dict: Result status with success/failure info
    """
    if audio_only:
        format_selector = 'bestaudio/best'
        file_extension = 'mp3'
        postprocessors = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        print(f"[Thread {thread_id}] Audio-only mode: Downloading MP3...")
    else:
        format_selector = (
            'bestvideo[height<=1080]+bestaudio/best[height<=1080]/'
            'best'
        )
        file_extension = 'mp4'
        postprocessors = [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]

    downloader_options = {
    'format': format_selector,
    'ignoreerrors': True,
    'no_warnings': False,

    # PLAYLIST FIX
    'noplaylist': False,
    'extract_flat': False,

    # OUTPUT / POST
    'postprocessors': postprocessors,
    'keepvideo': False,
    'clean_infojson': True,

    # RETRIES
    'retries': MAX_RETRIES,
    'fragment_retries': MAX_RETRIES,

    # YOUTUBE SAFETY
    'compat_opts': ['no-youtube-unavailable-videos'],
    'youtube_include_dash_manifest': False,

    # NETWORK (let yt-dlp decide)
    'nocheckcertificate': True,
}

    if not audio_only:
        downloader_options['merge_output_format'] = 'mp4'

    content_type, _ = get_url_info(url)

    if content_type == 'playlist':
        downloader_options['outtmpl'] = os.path.join(
            output_path, '%(playlist_title)s', f'%(playlist_index)s-%(title)s.{file_extension}')
        print(f"[Thread {thread_id}] Detected playlist URL. Downloading entire playlist...")
        print(f"[Thread {thread_id}] Files will be saved to: {output_path}/[playlist_name]/")
    elif content_type == 'channel':
        downloader_options['outtmpl'] = os.path.join(
            output_path, '%(uploader)s', f'%(upload_date)s-%(title)s.{file_extension}')
        print(f"[Thread {thread_id}] Detected channel URL. Downloading entire channel...")
        print(f"[Thread {thread_id}] Files will be saved to: {output_path}/[channel_name]/")
    else:
        downloader_options['outtmpl'] = os.path.join(
            output_path, '%(title)s.{ext}')
        print(f"[Thread {thread_id}] Detected single video URL. Downloading {'audio' if audio_only else 'video'}...")
        print(f"[Thread {thread_id}] File will be saved to: {output_path}/")

    last_exception = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with YoutubeDL(downloader_options) as ydl:
                download_result = ydl.extract_info(url, download=True)

                if download_result is None:
                    return {
                        'url': url,
                        'success': False,
                        'count': 0,
                        'message': f"[ERROR] [Thread {thread_id}] Failed to extract video information. Video may be private or unavailable."
                    }

                if download_result.get('_type') == 'playlist':
                    title = download_result.get('title', 'Unknown Playlist')
                    video_count = len(download_result.get('entries', []))
                    print(f"[Thread {thread_id}] {content_type.title()}: '{title}' ({video_count} videos)")

                    if video_count == 0:
                        return {
                            'url': url,
                            'success': False,
                            'count': 0,
                            'message': f"[ERROR] [Thread {thread_id}] {content_type.title()} appears to be empty or private"
                        }

                    return {
                        'url': url,
                        'success': True,
                        'count': video_count,
                        'message': f"[OK] [Thread {thread_id}] {content_type.title()} '{title}' download completed! ({video_count} {'MP3s' if audio_only else 'videos'}) Location: {output_path}"
                    }
                else:
                    title = download_result.get('title', 'Unknown')
                    return {
                        'url': url,
                        'success': True,
                        'count': 1,
                        'message': f"[OK] [Thread {thread_id}] {'Audio' if audio_only else 'Video'} '{title}' download completed! Location: {output_path}"
                    }

        except Exception as error:
            last_exception = error
            if attempt < MAX_RETRIES:
                retry_delay = RETRY_DELAY * (2 ** (attempt - 1))
                error_msg = f"[WARNING] [Thread {thread_id}] Attempt {attempt}/{MAX_RETRIES} failed: {str(error)[:100]}. Retrying in {retry_delay}s..."
                print(error_msg)
                time.sleep(retry_delay)
            else:
                return {
                    'url': url,
                    'success': False,
                    'count': 0,
                    'message': f"[ERROR] [Thread {thread_id}] Failed after {MAX_RETRIES} attempts. Last error: {str(last_exception)}"
                }

    return {
        'url': url,
        'success': False,
        'count': 0,
        'message': f"[ERROR] [Thread {thread_id}] Unexpected error: {str(last_exception)}"
    }


def download_youtube_content(urls: List[str], output_path: Optional[str] = None,
                             list_formats: bool = False, max_workers: int = DEFAULT_CONCURRENT_WORKERS, 
                             audio_only: bool = False) -> None:
    """
    Download YouTube content (single videos, playlists, or channels) in MP4 format or MP3 audio only.
    Supports multiple URLs for simultaneous downloading with optimized concurrency.

    Args:
        urls (List[str]): List of YouTube URLs to download (videos, playlists, or channels)
        output_path (str, optional): Directory to save the downloads. Defaults to './downloads'
        list_formats (bool): If True, only list available formats without downloading
        max_workers (int): Maximum number of concurrent downloads (1-5, default=3)
        audio_only (bool): If True, download audio only in MP3 format
    """
    if output_path is None:
        output_path = os.path.join(os.getcwd(), 'downloads')

    if list_formats:
        print("Available formats for the first provided URL:")
        get_available_formats(urls[0])
        return

    os.makedirs(output_path, exist_ok=True)

    print(
        f"\nStarting download of {len(urls)} URL(s) with {max_workers} concurrent workers...")
    print(f"Output directory: {output_path}")
    print(f"Format: {'MP3 Audio Only' if audio_only else 'MP4 Video'}")

    playlist_count = sum(
        1 for url in urls if get_content_type(url) == 'playlist')
    channel_count = sum(
        1 for url in urls if get_content_type(url) == 'channel')
    video_count = len(urls) - playlist_count - channel_count

    content_summary = []
    if playlist_count > 0:
        content_summary.append(f"{playlist_count} playlist(s)")
    if channel_count > 0:
        content_summary.append(f"{channel_count} channel(s)")
    if video_count > 0:
        content_summary.append(f"{video_count} video(s)")

    if content_summary:
        print(f"Content: {' + '.join(content_summary)}")
    else:
        print("Content: Unknown content type")

    print("-" * 60)

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(download_single_video, url, output_path, i+1, audio_only): url
            for i, url in enumerate(urls)
        }

        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)
            print(result['message'])

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)

    successful_downloads = [r for r in results if r['success']]
    failed_downloads = [r for r in results if not r['success']]

    total_successful_count = sum(r.get('count', 1) for r in successful_downloads)
    total_failed_count = sum(r.get('count', 1) for r in failed_downloads)

    print(f"[OK] Successful downloads: {total_successful_count} {'files' if total_successful_count != 1 else 'file'}")
    print(f"[ERROR] Failed downloads: {total_failed_count} {'files' if total_failed_count != 1 else 'file'}")

    if failed_downloads:
        print("\n[ERROR] Failed URLs:")
        for result in failed_downloads:
            print(f"   * {result['url']}")
            print(f"     Reason: {result['message']}")

    if successful_downloads:
        print(f"\nAll files saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--list-formats':
        url = input("Enter the YouTube URL to list formats: ")
        download_youtube_content([url], list_formats=True)
    else:
        show_banner()

        url_input = get_urls_interactive()

        if not url_input or not url_input.strip():
            print("Multi-line mode")
            print("Enter one URL per line, press Enter twice when finished:")
            urls_list = []
            line_count = 1
            while True:
                line = input(f"   URL {line_count}: ")
                if line.strip() == "":
                    break
                urls_list.append(line)
                line_count += 1
            url_input = '\n'.join(urls_list)

        if not url_input.strip():
            print("No URLs entered. Exiting...")
            exit(1)

        urls = parse_multiple_urls(url_input)

        if not urls:
            print("No valid YouTube URLs found. Please try again.")
            exit(1)

        print()
        print(f"[OK] Found {len(urls)} valid URL(s)")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")

        quality = select_quality()

        if quality == 'audio':
            audio_only = True
            print("Selected: Audio only (MP3)")
        else:
            audio_only = False
            quality_labels = {
                'best': 'Best available (1080p)',
                '720p': 'High (720p)',
                '480p': 'Medium (480p)',
                '360p': 'Low (360p)'
            }
            print(f"Selected: {quality_labels.get(quality, 'Best')}")

        output_dir = select_output_directory()

        max_workers = 1
        if len(urls) > 1:
            max_workers = select_concurrent()
        
        timestamps = []
        split_enabled = False
        
        if len(urls) == 1:
            print()
            split_prompt = "Split this video" + (" (audio)" if audio_only else "") + "? (y/n, default=n): "
            split_choice = input(split_prompt).strip().lower()

            if split_choice == 'y':
                timestamps = get_timestamps_interactive()

                if timestamps:
                    split_enabled = True
                    print(f"\n{len(timestamps)} clips will be created after download")
                    for i, ts in enumerate(timestamps, 1):
                        duration_sec = time_to_seconds(ts['end']) - time_to_seconds(ts['start'])
                        print(f"  {i}. {ts['start']} -> {ts['end']} ({duration_sec}s): {ts['title']}")
        
        print()
        print(f"Brewing {len(urls)} video(s)...")
        print()

        if output_dir:
            download_youtube_content(
                urls, output_dir, max_workers=max_workers, audio_only=audio_only)
            final_output_dir = output_dir
        else:
            download_youtube_content(
                urls, max_workers=max_workers, audio_only=audio_only)
            final_output_dir = 'downloads'
        
        if split_enabled and timestamps:
            content_type = "audio" if audio_only else "video"
            print(f"\n{'=' * 60}")
            print(f"[OK] Starting {content_type} splitting...")
            print("-" * 60)

            media_file = find_downloaded_video(final_output_dir, "")

            if media_file:
                print(f"[OK] Found {content_type}: {os.path.basename(media_file)}")

                clips_dir = os.path.join(os.path.dirname(media_file), 'clips')

                split_results = split_video_by_timestamps(media_file, timestamps, clips_dir, audio_only)

                successful_clips = [r for r in split_results if r['success']]
                failed_clips = [r for r in split_results if not r['success']]

                print("\n" + "-" * 60)
                print("SPLIT SUMMARY")
                print("-" * 60)
                print(f"[OK] Successful clips: {len(successful_clips)}")
                print(f"[ERROR] Failed clips: {len(failed_clips)}")

                if successful_clips:
                    print(f"\n[OK] Clips saved to: {clips_dir}")

                if failed_clips:
                    print("\n[ERROR] Failed clips:")
                    for clip in failed_clips:
                        print(f"  {clip['clip']}. {clip['title']}")
            else:
                print(f"[ERROR] Could not find downloaded {content_type} for splitting")
