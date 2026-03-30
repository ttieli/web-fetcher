"""Web content fetchers (Selenium, etc)."""
# Conditional imports to handle optional dependencies
try:
    from .selenium import SeleniumFetcher, SeleniumMetrics
    from .selenium import ChromeConnectionError, SeleniumFetchError
    from .selenium import SeleniumTimeoutError, SeleniumNotAvailableError
    from .config import SeleniumConfig
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from .headless_manager import HeadlessChromeManager, ensure_headless_chrome
    HEADLESS_MANAGER_AVAILABLE = True
except ImportError:
    HEADLESS_MANAGER_AVAILABLE = False

__all__ = []
if SELENIUM_AVAILABLE:
    __all__.extend([
        'SeleniumFetcher', 'SeleniumMetrics', 'SeleniumConfig',
        'ChromeConnectionError', 'SeleniumFetchError',
        'SeleniumTimeoutError', 'SeleniumNotAvailableError'
    ])
if HEADLESS_MANAGER_AVAILABLE:
    __all__.extend(['HeadlessChromeManager', 'ensure_headless_chrome'])
