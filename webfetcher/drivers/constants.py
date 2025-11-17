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

# Download configuration
DOWNLOAD_TIMEOUT = 300  # 5 minutes
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds (exponential backoff)

# Chrome for Testing download URLs
# Format: {base_url}/{version}/mac-x64/chromedriver-mac-x64.zip
CHROME_FOR_TESTING_URL_TEMPLATE = (
    "https://storage.googleapis.com/chrome-for-testing-public/"
    "{version}/mac-x64/chromedriver-mac-x64.zip"
)

# Known versions endpoint for version mapping
CHROME_FOR_TESTING_VERSIONS = (
    "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
)

# Deprecated: kept for reference
CHROME_FOR_TESTING_BASE = "https://storage.googleapis.com/chrome-for-testing-public"

class CompatibilityStatus(Enum):
    """Version compatibility status"""
    COMPATIBLE = "compatible"
    MISMATCH = "mismatch"
    UNKNOWN = "unknown"
    CHROME_NOT_FOUND = "chrome_not_found"
    DRIVER_NOT_FOUND = "driver_not_found"
