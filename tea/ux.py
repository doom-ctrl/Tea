"""
Enhanced UX components for Tea YouTube Downloader.

Provides interactive menus, configuration editors, presets,
and improved option selection interfaces.
"""

from typing import Dict, List, Optional, Callable, Any
import os
import json


class InteractiveMenu:
    """Generic interactive menu with flexible navigation."""

    def __init__(
        self,
        title: str,
        options: List[Dict[str, Any]],
        prompt: str = "Enter choice",
        allow_multiple: bool = False,
        show_current: Optional[str] = None
    ):
        self.title = title
        self.options = options  # Each: {'key': '1', 'label': '...', 'value': ..., 'shortcut': 'q'}
        self.prompt = prompt
        self.allow_multiple = allow_multiple
        self.show_current = show_current

    def display(self) -> str:
        """Display menu and return selected key."""
        print(f"\n[OK] {self.title}")
        print("=" * 60)

        for opt in self.options:
            key = opt['key']
            label = opt.get('label', '')
            value = opt.get('value', '')
            shortcut = opt.get('shortcut', '')
            desc = opt.get('description', '')

            # Build display line
            line = f"  [{key}]"
            if shortcut:
                line += f" [{shortcut}]"
            line += f" {label}"

            # Show current value marker
            if self.show_current and str(value) == str(self.show_current):
                line += " [CURRENT]"

            print(line)

            if desc:
                print(f"      {desc}")

        print()
        return self._get_input()

    def _get_input(self) -> str:
        """Get and validate user input."""
        while True:
            try:
                choice = input(f"{self.prompt}: ").strip().lower()

                # Check shortcuts
                for opt in self.options:
                    if opt.get('shortcut', '').lower() == choice:
                        return opt['key']

                # Check direct keys
                valid_keys = [opt['key'] for opt in self.options]
                if choice in valid_keys:
                    return choice

                # Handle empty input (default)
                if not choice and self.show_current:
                    return str(self.show_current)

                print("[WARNING] Invalid choice. Please try again.")
            except (EOFError, KeyboardInterrupt):
                print("\n[INFO] Operation cancelled")
                return ''


class QualitySelector:
    """Enhanced quality selection with visual indicators."""

    QUALITY_OPTIONS = [
        {
            'key': '1',
            'shortcut': 'b',
            'label': 'Best Available',
            'description': '1080p video with audio',
            'details': 'Highest quality, larger file size (~500MB/hr)',
            'icon': '[HD]',
            'audio_only': False
        },
        {
            'key': '2',
            'shortcut': 'h',
            'label': 'High Quality',
            'description': '720p video with audio',
            'details': 'Good quality, moderate file size (~250MB/hr)',
            'icon': '[HQ]',
            'audio_only': False
        },
        {
            'key': '3',
            'shortcut': 'm',
            'label': 'Medium Quality',
            'description': '480p video with audio',
            'details': 'Lower quality, smaller file size (~150MB/hr)',
            'icon': '[MQ]',
            'audio_only': False
        },
        {
            'key': '4',
            'shortcut': 'l',
            'label': 'Low Quality',
            'description': '360p video with audio',
            'details': 'Lowest quality, smallest file size (~80MB/hr)',
            'icon': '[LQ]',
            'audio_only': False
        },
        {
            'key': '5',
            'shortcut': 'a',
            'label': 'Audio Only',
            'description': 'MP3 audio (320kbps)',
            'details': 'No video, audio only (~50MB/hr)',
            'icon': '[MP3]',
            'audio_only': True
        }
    ]

    def __init__(self, default_quality: Optional[str] = None):
        self.default_quality = default_quality

    def display(self, show_current: Optional[str] = None) -> str:
        """Display quality selection menu."""
        print("\nSelect video quality:")
        print("=" * 60)
        print()

        for opt in self.QUALITY_OPTIONS:
            key = opt['key']
            shortcut = opt['shortcut']
            icon = opt['icon']
            label = opt['label']
            desc = opt['description']
            details = opt['details']

            # Current marker
            marker = " <- CURRENT" if show_current == key else ""

            print(f"  [{key}] [{shortcut}] {icon} {label}{marker}")
            print(f"      {desc}")
            print(f"      {details}")
            print()

        # Get input
        while True:
            prompt = f"Enter choice (1-5 or shortcut, default={show_current or '1'}): "
            choice = input(prompt).strip().lower()

            # Empty = default
            if not choice:
                return show_current if show_current else '1'

            # Check shortcuts
            shortcut_map = {opt['shortcut']: opt['key'] for opt in self.QUALITY_OPTIONS}
            if choice in shortcut_map:
                return shortcut_map[choice]

            # Check numbers
            if choice in '12345':
                return choice

            print("[WARNING] Invalid choice. Please enter 1-5 or a shortcut.")

    def is_audio_only(self, choice: str) -> bool:
        """Check if the selected choice is audio-only."""
        for opt in self.QUALITY_OPTIONS:
            if opt['key'] == choice:
                return opt['audio_only']
        return False


class PresetManager:
    """Manage configuration presets and user profiles."""

    DEFAULT_PRESETS = {
        'music': {
            'name': 'Music Lover',
            'description': 'High quality audio for music collection',
            'settings': {
                'default_quality': '5',
                'mp3_quality': '320',
                'thumbnail_embed': True,
                'use_ai_filename_cleaning': True,
            }
        },
        'podcast': {
            'name': 'Podcast Archive',
            'description': 'Efficient storage for long-form content',
            'settings': {
                'default_quality': '5',
                'mp3_quality': '128',
                'thumbnail_embed': False,
                'use_ai_filename_cleaning': True,
            }
        },
        'video': {
            'name': 'Video Collector',
            'description': 'High quality videos with metadata',
            'settings': {
                'default_quality': '1',
                'thumbnail_embed': True,
                'use_ai_filename_cleaning': False,
            }
        },
        'minimal': {
            'name': 'Minimal',
            'description': 'Basic settings, fastest downloads',
            'settings': {
                'default_quality': '4',
                'mp3_quality': '192',
                'thumbnail_embed': False,
                'use_ai_filename_cleaning': False,
            }
        }
    }

    def __init__(self, config_manager):
        self._config = config_manager
        self._profile_path = self._get_profile_path()

    def _get_profile_path(self) -> str:
        """Get path to profiles file."""
        module_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(module_dir, 'tea-profiles.json')

    def list_presets(self) -> List[Dict[str, Any]]:
        """List all available presets."""
        presets = []
        for key, preset in self.DEFAULT_PRESETS.items():
            presets.append({
                'key': key,
                'name': preset['name'],
                'description': preset['description']
            })
        return presets

    def list_profiles(self) -> List[Dict[str, Any]]:
        """List user-saved profiles."""
        if not os.path.exists(self._profile_path):
            return []

        try:
            with open(self._profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profiles = []
            for key, profile in data.get('profiles', {}).items():
                profiles.append({
                    'key': key,
                    'name': profile.get('name', key),
                    'description': profile.get('description', '')
                })
            return profiles
        except (json.JSONDecodeError, IOError):
            return []

    def apply_preset(self, preset_key: str) -> bool:
        """Apply a preset configuration."""
        if preset_key not in self.DEFAULT_PRESETS:
            return False

        preset = self.DEFAULT_PRESETS[preset_key]
        self._config.update(preset['settings'])
        return True

    def save_profile(self, profile_key: str, name: str, description: str = '') -> bool:
        """Save current config as a named profile."""
        # Load existing profiles
        profiles = {}
        if os.path.exists(self._profile_path):
            try:
                with open(self._profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profiles = data.get('profiles', {})
            except (json.JSONDecodeError, IOError):
                pass

        # Save current config
        profiles[profile_key] = {
            'name': name,
            'description': description,
            'settings': self._config.to_dict(),
            'created_at': self._get_timestamp()
        }

        # Write back
        try:
            with open(self._profile_path, 'w', encoding='utf-8') as f:
                json.dump({'_version': '1.0.0', 'profiles': profiles}, f, indent=2)
            return True
        except IOError:
            return False

    def load_profile(self, profile_key: str) -> bool:
        """Load a saved profile."""
        if not os.path.exists(self._profile_path):
            return False

        try:
            with open(self._profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profiles = data.get('profiles', {})
            if profile_key not in profiles:
                return False

            profile = profiles[profile_key]
            self._config._config = profile['settings'].copy()
            self._config.save()
            return True
        except (json.JSONDecodeError, IOError, KeyError):
            return False

    def delete_profile(self, profile_key: str) -> bool:
        """Delete a saved profile."""
        if not os.path.exists(self._profile_path):
            return False

        try:
            with open(self._profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profiles = data.get('profiles', {})
            if profile_key not in profiles:
                return False

            del profiles[profile_key]

            with open(self._profile_path, 'w', encoding='utf-8') as f:
                json.dump({'_version': '1.0.0', 'profiles': profiles}, f, indent=2)
            return True
        except (json.JSONDecodeError, IOError, KeyError):
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class ConfigEditor:
    """Interactive configuration editor."""

    def __init__(self, config_manager, logger=None):
        self._config = config_manager
        self._logger = logger
        self._presets = PresetManager(config_manager)

    def run(self) -> None:
        """Run interactive configuration editor."""
        while True:
            choice = self._display_main_menu()

            if choice == '0' or choice == 'q' or choice == 'x':
                break
            elif choice in '1234567':
                self._edit_setting_by_number(choice)
            elif choice == '8' or choice == 'p':
                self._preset_menu()
            elif choice == '9' or choice == 'r':
                self._profile_menu()
            else:
                print("[WARNING] Invalid choice")

    def _display_main_menu(self) -> str:
        """Display main configuration menu."""
        print("\n[OK] Tea Configuration")
        print("=" * 60)
        print("\n  SETTINGS:")
        print(f"    [1] [q] Default quality         [{self._format_quality(self._config.default_quality)}]")
        print(f"    [2] [o] Default output          [{self._config.default_output}]")
        print(f"    [3] [c] Concurrent downloads    [{self._config.concurrent_downloads}]")
        print(f"    [4] [m] MP3 quality             [{self._config.mp3_quality}kbps]")
        print(f"    [5] [t] Thumbnail embedding     [{self._format_bool(self._config.thumbnail_embed)}]")
        print(f"    [6] [a] AI filename cleaning    [{self._format_bool(self._config.use_ai_filename_cleaning)}]")
        print(f"    [7] [d] Duplicate action        [{self._config.duplicate_action}]")
        print("\n  ACTIONS:")
        print(f"    [8] [p] Apply preset            (Music, Podcast, Video, Minimal)")
        print(f"    [9] [r] Profiles                (Save/Load custom profiles)")
        print(f"    [0] [x] Exit")
        print()

        return self._get_choice()

    def _edit_setting_by_number(self, choice: str) -> None:
        """Edit a setting by its menu number."""
        setting_map = {
            '1': ('default_quality', self._edit_quality),
            '2': ('default_output', self._edit_output),
            '3': ('concurrent_downloads', self._edit_concurrent),
            '4': ('mp3_quality', self._edit_mp3_quality),
            '5': ('thumbnail_embed', self._edit_bool),
            '6': ('use_ai_filename_cleaning', self._edit_bool),
            '7': ('duplicate_action', self._edit_duplicate_action),
        }

        if choice not in setting_map:
            print("[ERROR] Invalid setting")
            return

        key, editor = setting_map[choice]
        current = self._config.get(key)
        new_value = editor(key, current)

        if new_value is not None and new_value != current:
            self._config.set(key, new_value)
            print(f"[OK] {key} updated to: {new_value}")

    def _edit_quality(self, key: str, current: str) -> str:
        """Edit quality setting."""
        selector = QualitySelector(default_quality=current)
        return selector.display(show_current=current)

    def _edit_output(self, key: str, current: str) -> str:
        """Edit output directory."""
        print(f"\nCurrent: {current}")
        new_val = input(f"Enter new output directory (press Enter to keep): ").strip()
        return new_val if new_val else None

    def _edit_concurrent(self, key: str, current: int) -> int:
        """Edit concurrent downloads."""
        print(f"\nCurrent: {current}")
        while True:
            new_val = input(f"Enter concurrent downloads (1-5, press Enter to keep): ").strip()
            if not new_val:
                return None
            try:
                num = int(new_val)
                if 1 <= num <= 5:
                    return num
                print("[WARNING] Please enter 1-5")
            except ValueError:
                print("[WARNING] Please enter a number")

    def _edit_mp3_quality(self, key: str, current: str) -> str:
        """Edit MP3 quality."""
        print(f"\nCurrent: {current}kbps")
        print("Options: 128, 192, 256, 320")
        while True:
            new_val = input(f"Enter MP3 quality (press Enter to keep): ").strip()
            if not new_val:
                return None
            if new_val in {'128', '192', '256', '320'}:
                return new_val
            print("[WARNING] Please enter 128, 192, 256, or 320")

    def _edit_bool(self, key: str, current: bool) -> bool:
        """Edit boolean setting."""
        print(f"\nCurrent: {self._format_bool(current)}")
        while True:
            new_val = input(f"Enable? (y/n, press Enter to keep): ").strip().lower()
            if not new_val:
                return None
            if new_val == 'y':
                return True
            if new_val == 'n':
                return False
            print("[WARNING] Please enter y or n")

    def _edit_duplicate_action(self, key: str, current: str) -> str:
        """Edit duplicate action."""
        print(f"\nCurrent: {current}")
        print("Options: ask, download, skip")
        while True:
            new_val = input(f"Enter duplicate action (press Enter to keep): ").strip().lower()
            if not new_val:
                return None
            if new_val in {'ask', 'download', 'skip'}:
                return new_val
            print("[WARNING] Please enter ask, download, or skip")

    def _preset_menu(self) -> None:
        """Show preset selection menu."""
        print("\n[OK] Select a preset configuration")
        print("=" * 60)

        presets = self._presets.list_presets()
        for preset in presets:
            print(f"  [{preset['key']}] {preset['name']}")
            print(f"      {preset['description']}")
            print()

        print("  [0] [x] Cancel")
        print()

        choice = self._get_choice()

        if choice == '0' or choice == 'x':
            return

        if self._presets.apply_preset(choice):
            preset_name = self._presets.DEFAULT_PRESETS[choice]['name']
            print(f"[OK] Applied preset: {preset_name}")
        else:
            print("[ERROR] Invalid preset")

    def _profile_menu(self) -> None:
        """Show profile management menu."""
        while True:
            print("\n[OK] Profile Management")
            print("=" * 60)

            profiles = self._presets.list_profiles()
            if profiles:
                print("  SAVED PROFILES:")
                for p in profiles:
                    print(f"    [{p['key']}] {p['name']}")
                    if p.get('description'):
                        print(f"        {p['description']}")
                print()

            print("  ACTIONS:")
            print("    [1] [s] Save current as profile")
            print("    [2] [l] Load a profile")
            print("    [3] [d] Delete a profile")
            print("    [0] [x] Back")
            print()

            choice = self._get_choice()

            if choice == '0' or choice == 'x':
                break
            elif choice == '1' or choice == 's':
                self._save_profile()
            elif choice == '2' or choice == 'l':
                self._load_profile()
            elif choice == '3' or choice == 'd':
                self._delete_profile()

    def _save_profile(self) -> None:
        """Save current configuration as a profile."""
        name = input("Profile name: ").strip()
        if not name:
            print("[INFO] Cancelled")
            return

        key = name.lower().replace(' ', '-')
        desc = input("Description (optional): ").strip()

        if self._presets.save_profile(key, name, desc):
            print(f"[OK] Profile '{name}' saved")
        else:
            print("[ERROR] Failed to save profile")

    def _load_profile(self) -> None:
        """Load a saved profile."""
        profiles = self._presets.list_profiles()
        if not profiles:
            print("[INFO] No saved profiles")
            return

        print("\nSelect profile to load:")
        for p in profiles:
            print(f"  [{p['key']}] {p['name']}")
        print()

        choice = input("Enter profile key: ").strip().lower()

        if self._presets.load_profile(choice):
            print(f"[OK] Profile loaded")
        else:
            print("[ERROR] Failed to load profile")

    def _delete_profile(self) -> None:
        """Delete a saved profile."""
        profiles = self._presets.list_profiles()
        if not profiles:
            print("[INFO] No saved profiles")
            return

        print("\nSelect profile to delete:")
        for p in profiles:
            print(f"  [{p['key']}] {p['name']}")
        print()

        choice = input("Enter profile key: ").strip().lower()

        if self._presets.delete_profile(choice):
            print(f"[OK] Profile deleted")
        else:
            print("[ERROR] Failed to delete profile")

    def _get_choice(self) -> str:
        """Get user choice with support for numbers and shortcuts."""
        return input("Enter choice: ").strip().lower()

    def _format_quality(self, quality: str) -> str:
        """Format quality for display."""
        labels = {
            '1': 'Best (1080p)',
            '2': 'High (720p)',
            '3': 'Medium (480p)',
            '4': 'Low (360p)',
            '5': 'Audio (MP3)',
            'best': 'Best (1080p)',
            '720p': 'High (720p)',
            '480p': 'Medium (480p)',
            '360p': 'Low (360p)',
            'audio': 'Audio (MP3)'
        }
        return labels.get(quality, quality)

    def _format_bool(self, value: bool) -> str:
        """Format boolean for display."""
        return "ON" if value else "OFF"
