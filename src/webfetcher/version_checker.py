#!/usr/bin/env python3
"""
Version checker for WebFetcher CLI
Checks GitHub for updates without blocking main program
"""
import os
import json
import time
import threading
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.error


# Version check configuration
GITHUB_REPO = "ttieli/web-fetcher"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CHECK_INTERVAL = 86400  # 24 hours in seconds
CACHE_FILE = Path.home() / ".cache" / "webfetcher" / "version_check.json"


def get_current_version() -> str:
    """
    Get current version from pyproject.toml

    Returns:
        str: Current version (e.g., "1.0.0")
    """
    try:
        # Try to get version from package metadata
        try:
            import importlib.metadata
            return importlib.metadata.version("webfetcher")
        except Exception:
            pass

        # Fallback: read from pyproject.toml
        from pathlib import Path
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            with open(pyproject_path, 'r') as f:
                for line in f:
                    if line.startswith('version = '):
                        # Extract version from: version = "1.0.0"
                        version = line.split('=')[1].strip().strip('"')
                        return version

        return "1.0.0"  # Default fallback
    except Exception:
        return "1.0.0"


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """
    Parse version string to tuple for comparison

    Args:
        version_str: Version string like "1.2.3" or "v1.2.3"

    Returns:
        Tuple[int, int, int]: (major, minor, patch)
    """
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')

    # Split and convert to integers
    parts = version_str.split('.')
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0

    return (major, minor, patch)


def is_newer_version(current: str, latest: str) -> bool:
    """
    Check if latest version is newer than current

    Args:
        current: Current version string
        latest: Latest version string

    Returns:
        bool: True if latest is newer
    """
    try:
        current_tuple = parse_version(current)
        latest_tuple = parse_version(latest)
        return latest_tuple > current_tuple
    except Exception:
        return False


def should_check_update() -> bool:
    """
    Check if we should perform update check based on cache

    Returns:
        bool: True if should check
    """
    try:
        if not CACHE_FILE.exists():
            return True

        # Read cache
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)

        last_check = cache.get('last_check', 0)
        current_time = time.time()

        # Check if interval has passed
        return (current_time - last_check) > CHECK_INTERVAL

    except Exception:
        return True


def save_check_cache(latest_version: Optional[str] = None):
    """
    Save version check cache

    Args:
        latest_version: Latest version found (if any)
    """
    try:
        # Ensure cache directory exists
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        cache = {
            'last_check': time.time(),
            'latest_version': latest_version
        }

        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)

    except Exception:
        pass  # Silently fail - not critical


def get_latest_version() -> Optional[str]:
    """
    Fetch latest version from GitHub API

    Returns:
        Optional[str]: Latest version tag or None if failed
    """
    try:
        # Set timeout to avoid blocking
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': 'WebFetcher-CLI'}
        )

        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            tag_name = data.get('tag_name', '')
            return tag_name.lstrip('v')  # Remove 'v' prefix if present

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception):
        return None


def check_for_updates_async():
    """
    Check for updates in background thread (non-blocking)
    """
    def _check():
        try:
            # Skip if checked recently
            if not should_check_update():
                return

            current_version = get_current_version()
            latest_version = get_latest_version()

            # Save cache regardless of result
            save_check_cache(latest_version)

            # Show update message if newer version available
            if latest_version and is_newer_version(current_version, latest_version):
                print(f"\n{'='*60}")
                print(f"📦 WebFetcher 有新版本可用!")
                print(f"   当前版本: v{current_version}")
                print(f"   最新版本: v{latest_version}")
                print(f"\n升级命令:")
                print(f"   pip install --upgrade webfetcher")
                print(f"\n或从源码更新:")
                print(f"   cd /path/to/Web_Fetcher && git pull")
                print(f"{'='*60}\n")

        except Exception:
            pass  # Silently fail - don't interrupt user

    # Run check in background thread
    thread = threading.Thread(target=_check, daemon=True)
    thread.start()


def check_for_updates():
    """
    Main entry point for version checking
    Call this at CLI startup
    """
    try:
        check_for_updates_async()
    except Exception:
        pass  # Never let version check crash the program
