"""
Constants for ChromeDriver version management
ChromeDriver版本管理常量
"""
from pathlib import Path
from enum import Enum

# Chrome application path on macOS
CHROME_APP_PATH = "/Applications/Google Chrome.app"
CHROME_EXECUTABLE = f"{CHROME_APP_PATH}/Contents/MacOS/Google Chrome"
CHROME_PLIST = f"{CHROME_APP_PATH}/Contents/Info.plist"

# ChromeDriver possible locations
CHROMEDRIVER_LOCATIONS = [
    "chromedriver",  # In PATH
    "./chromedriver",  # Current directory
    "/usr/local/bin/chromedriver",  # Common install location
    str(Path.home() / ".webfetcher" / "drivers" / "current")  # Our managed location
]

# Cache base path
CACHE_BASE_PATH = Path.home() / ".webfetcher" / "drivers"

# Download URLs (to be used in Phase 2)
CHROME_FOR_TESTING_BASE = "https://storage.googleapis.com/chrome-for-testing-public"

class CompatibilityStatus(Enum):
    """Version compatibility status"""
    COMPATIBLE = "compatible"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    CHROME_NOT_FOUND = "chrome_not_found"
    DRIVER_NOT_FOUND = "driver_not_found"
