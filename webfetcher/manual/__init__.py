"""
Manual Chrome Hybrid Module

This module provides a fallback mechanism for web scraping when automated
methods fail. It leverages manual browser navigation combined with automated
content extraction via Chrome DevTools Protocol (CDP).

Key Features:
- Human-assisted browser navigation to bypass anti-bot detection
- Automated content extraction via Selenium WebDriver
- macOS-focused implementation with graceful UX
- Minimal manual intervention required

Usage:
    from manual_chrome import ManualChromeHelper

    helper = ManualChromeHelper(config)
    success, html, error = helper.start_session(url)
    if success:
        print(f"Extracted {len(html)} bytes")

Version: 1.0.0
Platform: macOS only
"""

from .helper import ManualChromeHelper
from .exceptions import (
    ManualChromeError,
    ChromeNotFoundError,
    PortInUseError,
    AttachmentError,
    TimeoutError
)

__version__ = "1.0.0"
__all__ = [
    "ManualChromeHelper",
    "ManualChromeError",
    "ChromeNotFoundError",
    "PortInUseError",
    "AttachmentError",
    "TimeoutError"
]
